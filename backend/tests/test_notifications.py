from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.ai.recommender import DisabledRecommender
from app.core.config import Settings
from app.core.errors import DomainError
from app.main import create_app
from app.repositories.dataset import build_snapshot
from app.repositories.state import StateRepository
from app.schemas.notifications import (
    EmployeeNotificationPreferences, HRContactUpdate, MailAccount, NotificationSettings,
    OfferAction, ResolveDelivery, SMTPConnection, TestMailCommand as MailTestCommand,
)
from app.schemas.recommendation import RecommendationItem, RecommendationResult
from app.schemas.state import RuntimeCompletion
from app.services.dataset import DatasetService
from app.services.mail_transport import MailFailure, SMTPTransport
from app.services.notifications import NotificationService


class Clock:
    def __init__(self):
        self.value = datetime(2026, 10, 1, 6, tzinfo=timezone.utc)  # 11:00 company time
    def __call__(self): return self.value
    def advance(self, **kwargs): self.value += timedelta(**kwargs)


class FakeAI:
    def __init__(self): self.calls = []
    def refine(self, context):
        self.calls.append(context.employee_id)
        return RecommendationResult(status="success", employee_id=context.employee_id,
            recommendations=[RecommendationItem(event_id=c.event_id, explanation="Develops a required skill.", evidence=c.factors)
                             for c in context.candidates[:3]], revision=context.revision, as_of_date=context.as_of_date)


class FakeMail:
    configured = True
    def __init__(self): self.sent = []; self.error = None
    def connect(self, value):
        return MailAccount(**value.model_dump(exclude={"password"}), encrypted_password="encrypted-test-only")
    def send(self, account, recipient, subject, body, message_id):
        if self.error: raise self.error
        self.sent.append((recipient, subject, body, message_id))


@pytest.fixture
def workflow(tiny_bundle, tmp_path, clock):
    store = DatasetService(build_snapshot(tiny_bundle), StateRepository(tmp_path / "state.json"), "fixture")
    now, ai, mail = Clock(), FakeAI(), FakeMail()
    service = NotificationService(store, ai, mail, lambda: clock, "https://career.example", now)
    service.connect(SMTPConnection(host="smtp.example.com", username="hr@example.com", sender_email="hr@example.com", password="private"))
    service.update_settings(NotificationSettings(enabled=True))
    service.update_preferences("TEST_EMP", preferences=EmployeeNotificationPreferences(email="employee@example.com"))
    service.generate("TEST_EMP")
    return service, now, ai, mail


def first_offer(service): return next(iter(service.state.offers.values()))
def accepted(service): return [d for d in service.state.deliveries.values() if d.status == "accepted"]


def test_uncertain_refresh_removes_old_offers_and_sends_nothing(workflow):
    service, now, ai, mail = workflow
    service.state.generations.clear()  # Force a new model response in this fixture.
    class UncertainAI(FakeAI):
        def refine(self, context):
            result = super().refine(context)
            return result.model_copy(update={"recommendations": [result.recommendations[0].model_copy(update={"confidence": "uncertain"})],
                "clarifying_questions": ["Какая задача сейчас приоритетна?"]})
    service.ai_client = UncertainAI()
    result = service.generate("TEST_EMP")
    assert result.status == "needs_clarification"
    assert service.state.generations["TEST_EMP"].status == "needs_clarification"
    assert all(offer.status == "invalidated" for offer in service.state.offers.values())
    service.dispatch()
    assert not mail.sent


def test_disk_failure_after_smtp_acceptance_recovers_without_resend(workflow, monkeypatch):
    service, now, ai, mail = workflow
    repository = service.dataset.state_repository
    original = repository.save
    def fail_after_acceptance(state):
        if any(d.status == "accepted" for d in state.notifications.deliveries.values()):
            raise OSError("disk unavailable")
        original(state)
    monkeypatch.setattr(repository, "save", fail_after_acceptance)
    with pytest.raises(OSError):
        service.dispatch()
    assert len(mail.sent) == 1
    assert any(d.status == "sending" for d in repository.load("fixture").notifications.deliveries.values())
    monkeypatch.setattr(repository, "save", original)
    store = DatasetService(build_snapshot(service.dataset.raw_bundle), repository, "fixture")
    restarted = NotificationService(store, ai, mail, service.as_of_date, service.app_url, now)
    restarted.tick()
    assert len(mail.sent) == 1
    assert any(d.status == "unknown" for d in restarted.state.deliveries.values())


def test_worker_visits_other_employees_after_model_failure(tiny_bundle, make_employee, tmp_path, clock):
    bundle = tiny_bundle.model_copy(update={"employees": tuple(make_employee(employee_id=f"EMP_{i}") for i in range(3))})
    class PartlyFailingAI(FakeAI):
        def refine(self, context):
            if context.employee_id == "EMP_0":
                self.calls.append(context.employee_id)
                raise DomainError("unavailable", "temporary model failure")
            return super().refine(context)
    ai = PartlyFailingAI()
    store = DatasetService(build_snapshot(bundle), StateRepository(tmp_path / "state.json"), "fixture")
    service = NotificationService(store, ai, FakeMail(), lambda: clock, "https://career.example", Clock())
    for _ in range(6): service.tick()
    assert ai.calls == ["EMP_0", "EMP_1", "EMP_2"]
    assert service.state.generations["EMP_0"].status == "failed"
    assert service.state.generations["EMP_2"].status == "ready"
    assert not service.mailer.sent  # Preparation also runs with delivery disabled.


def test_transient_retries_are_bounded(workflow):
    service, now, ai, mail = workflow
    mail.error = MailFailure("smtp_connection_failed", retryable=True)
    for _ in range(4):
        service.dispatch()
        now.advance(days=1)
    row = next(iter(service.state.deliveries.values()))
    assert row.status == "failed" and row.attempts == 4
    service.dispatch()
    assert service.state.deliveries[row.id].attempts == 4


def test_auth_failure_waits_for_reconnection(workflow):
    service, now, ai, mail = workflow
    mail.error = MailFailure("smtp_auth_failed", account_failure=True)
    service.dispatch()
    assert service.state.account.status == "auth_failed"
    row = next(iter(service.state.deliveries.values()))
    now.advance(days=2); service.dispatch()
    assert service.state.deliveries[row.id].attempts == 1
    mail.error = None
    service.connect(SMTPConnection(host="smtp.example.com", username="hr@example.com", sender_email="hr@example.com", password="new"))
    service.dispatch()
    assert len(mail.sent) == 1


def test_prepare_restart_and_parallel_dispatch_do_not_duplicate(workflow):
    service, now, ai, mail = workflow
    assert len(service.state.offers) == 1
    service.generate("TEST_EMP")
    assert ai.calls == ["TEST_EMP"]
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda _: service.dispatch(), range(2)))
    assert len(mail.sent) == 1
    store = DatasetService(build_snapshot(service.dataset.raw_bundle), service.dataset.state_repository, "fixture")
    restarted = NotificationService(store, ai, mail, service.as_of_date, service.app_url, now)
    restarted.recover(); restarted.tick()
    assert len(mail.sent) == 1 and len(restarted.state.offers) == 1
    assert store.capture().revision == 0  # metadata does not invalidate academic views


def test_window_changes_use_current_settings(workflow):
    service, now, ai, mail = workflow
    now.value = now.value.replace(hour=2)  # 07:00
    service.dispatch(); assert not mail.sent
    service.update_settings(service.state.settings.model_copy(update={"start_minute": 360}))
    service.dispatch(); assert len(mail.sent) == 1
    assert accepted(service)[0].settings_version == service.state.settings.version


def test_pending_reminder_uses_changed_interval(workflow):
    service, now, ai, mail = workflow
    service.dispatch()
    service.update_settings(service.state.settings.model_copy(update={"reminder_after_days": 14}))
    now.advance(days=7); service.dispatch(); assert len(mail.sent) == 1
    pending = next(d for d in service.state.deliveries.values() if d.status == "pending")
    assert pending.next_attempt_at > now()
    now.advance(days=7); service.dispatch(); assert len(mail.sent) == 2


@pytest.mark.parametrize("block", ["global", "employee", "hr", "email", "account"])
def test_all_sending_gates(workflow, block):
    service, now, ai, mail = workflow
    if block == "global": service.update_settings(service.state.settings.model_copy(update={"enabled": False}))
    if block == "employee": service.update_preferences("TEST_EMP", preferences=EmployeeNotificationPreferences(email="employee@example.com", paused=True))
    if block == "hr": service.update_preferences("TEST_EMP", hr_update=HRContactUpdate(email="employee@example.com", hr_paused=True))
    if block == "email": service.update_preferences("TEST_EMP", preferences=EmployeeNotificationPreferences())
    if block == "account": service.disconnect()
    service.dispatch()
    assert not mail.sent
    assert any(d.block_reason for d in service.state.deliveries.values())


def test_reminder_and_cooldown_stop_repeat_messages(workflow):
    service, now, ai, mail = workflow
    service.dispatch()
    now.advance(days=6); service.dispatch(); assert len(mail.sent) == 1
    now.advance(days=1); service.dispatch(); assert len(mail.sent) == 2
    now.advance(days=13); service.dispatch(); assert len(mail.sent) == 2
    now.advance(days=1); service.dispatch()
    assert len(mail.sent) == 2 and first_offer(service).status == "unanswered"


def test_snooze_has_one_reminder_and_commands_are_idempotent(workflow):
    service, now, ai, mail = workflow
    service.dispatch()
    command = OfferAction(command_id=uuid4(), action="later", snoozed_until=now() + timedelta(days=10))
    offer = service.action("TEST_EMP", first_offer(service).id, command)
    assert service.action("TEST_EMP", offer.id, command) == offer
    now.advance(days=9); service.dispatch(); assert len(mail.sent) == 1
    now.advance(days=1); service.dispatch(); service.dispatch()
    assert len(mail.sent) == 2
    with pytest.raises(DomainError):
        service.action("TEST_EMP", offer.id, command.model_copy(update={"action": "decline"}))


@pytest.mark.parametrize("action", ["enroll", "decline"])
def test_reaction_cancels_pending_invitation(workflow, action):
    service, now, ai, mail = workflow
    service.action("TEST_EMP", first_offer(service).id, OfferAction(command_id=uuid4(), action=action))
    service.dispatch(); now.advance(days=20); service.dispatch()
    assert not mail.sent


def test_completion_before_dispatch_cancels_invitation(workflow):
    service, now, ai, mail = workflow
    dataset = service.dataset
    with dataset.lock:
        completion = RuntimeCompletion(command_id=uuid4(), employee_id="TEST_EMP", event_id="EV_012",
            source_record_id=None, participation_date=service.as_of_date(), completed_on=service.as_of_date())
        dataset.commit(dataset.state.model_copy(update={"revision": 1, "completions": (completion,)}))
    service.dispatch()
    assert first_offer(service).status == "completed"
    assert [d.kind for d in accepted(service)] == ["completion"]
    assert "Завершено" in mail.sent[0][2]


def test_transient_retry_and_uncertain_outcome(workflow):
    service, now, ai, mail = workflow
    mail.error = MailFailure("smtp_connection_failed", retryable=True)
    service.dispatch()
    assert next(iter(service.state.deliveries.values())).attempts == 1
    service.dispatch(); assert next(iter(service.state.deliveries.values())).attempts == 1
    now.advance(minutes=5); mail.error = MailFailure("smtp_acceptance_unknown", uncertain=True)
    service.dispatch()
    row = next(iter(service.state.deliveries.values()))
    assert row.status == "unknown" and row.attempts == 2
    now.advance(days=30); mail.error = None; service.dispatch()
    assert not mail.sent
    with pytest.raises(DomainError): service.retry_failed(row.id)
    service.resolve_unknown(row.id, ResolveDelivery(outcome="accepted", note="Verified in sent folder"))
    assert service.state.deliveries[row.id].status == "accepted"


def test_restart_during_send_is_unknown(workflow):
    service, now, ai, mail = workflow
    service.update_settings(service.state.settings.model_copy(update={"enabled": False}))
    service.dispatch()
    with service.dataset.lock:
        state = service.state.model_copy(deep=True)
        row = next(iter(state.deliveries.values()))
        state.deliveries[row.id] = row.model_copy(update={"status": "sending", "attempted_at": now(), "attempts": 1})
        service._save(state)
    service.recover()
    service.update_settings(service.state.settings.model_copy(update={"enabled": True}))
    service.dispatch()
    assert service.state.deliveries[row.id].status == "unknown" and not mail.sent


def test_pause_keeps_stricter_employee_limits(workflow):
    service, now, ai, mail = workflow
    service.update_preferences("TEST_EMP", preferences=EmployeeNotificationPreferences(email="employee@example.com", minimum_interval_hours=240))
    service.dispatch(); now.advance(days=7); service.dispatch()
    assert len(mail.sent) == 1
    now.advance(days=3); service.dispatch(); assert len(mail.sent) == 2


def test_bad_address_can_be_corrected(workflow):
    service, now, ai, mail = workflow
    mail.error = MailFailure("recipient_rejected", address_failure=True)
    service.dispatch()
    assert service.preferences("TEST_EMP").address_blocked
    service.update_preferences("TEST_EMP", hr_update=HRContactUpdate(email="corrected@example.com"))
    mail.error = None; service.dispatch()
    assert mail.sent[0][0] == "corrected@example.com"


def test_test_letter_has_stable_command_id_and_no_employee_reaction(workflow):
    service, now, ai, mail = workflow
    service.update_settings(service.state.settings.model_copy(update={"enabled": False}))
    command = MailTestCommand(command_id=uuid4(), recipient="hr@example.com")
    assert service.queue_test(command) == service.queue_test(command)
    service.dispatch(); assert len(mail.sent) == 1
    assert first_offer(service).status == "proposed"
    assert service.offers_view("TEST_EMP")["offers"][0].status == "proposed"  # GET never marks a view


def test_account_credentials_encrypted_and_not_in_views(monkeypatch):
    transport = SMTPTransport(Fernet.generate_key().decode())
    class Client:
        def close(self): pass
    monkeypatch.setattr(transport, "_login", lambda account, password: Client())
    account = transport.connect(SMTPConnection(host="smtp.example.com", username="hr@example.com", sender_email="hr@example.com", password="unique-secret-value"))
    assert "unique-secret-value" not in account.model_dump_json()
    assert transport.cipher.decrypt(account.encrypted_password.encode()).decode() == "unique-secret-value"


@pytest.mark.parametrize("kwargs", [
    {"start_minute": 1100, "end_minute": 1000}, {"weekly_limit": 0},
    {"subject_template": "Subject\nBcc: injected@example.com"},
    {"body_template": "{name.__class__}"}, {"body_template": "{unknown}"},
])
def test_settings_validation(kwargs):
    with pytest.raises(ValidationError): NotificationSettings(**kwargs)


def test_settings_conflict_and_provider_missing(workflow):
    service, now, ai, mail = workflow
    with pytest.raises(DomainError): service.update_settings(NotificationSettings())
    service.ai_client = DisabledRecommender()
    service.tick()  # Cached offers and sending continue without calling the disabled model.
    assert service.settings_view()["ai_ready"] is False
    assert "encrypted_password" not in service.settings_view()["account"]


def test_notification_routes_enforce_roles_and_employee_scope(tmp_path):
    settings = Settings(raw_dir=Path(__file__).resolve().parents[2] / "data/raw", state_path=tmp_path / "state.json",
        notifications_worker_enabled=False,
        dev_identities={"self": {"role": "employee", "employee_id": "E0047"}, "hr": {"role": "hr"}})
    mail, ai = FakeMail(), FakeAI()
    with TestClient(create_app(settings, ai_client=ai, mailer=mail, notification_clock=Clock())) as client:
        own, hr = {"Authorization": "Bearer self"}, {"Authorization": "Bearer hr"}
        assert client.get("/api/hr/notifications/settings", headers=own).status_code == 403
        assert client.get("/api/hr/notifications/journal").status_code == 401
        assert client.get("/api/employees/E0001/notifications", headers=own).status_code == 403
        assert client.get("/api/employees/E0047/notifications", headers=own).headers["cache-control"] == "no-store"
        response = client.post("/api/hr/notifications/mail-account", headers=hr, json={"host": "smtp.example.com", "username": "hr@example.com", "sender_email": "hr@example.com", "password": "unique-secret-value"})
        assert response.status_code == 200 and "unique-secret-value" not in response.text and "encrypted_password" not in response.text
        assert client.post("/api/employees/E0047/recommendations", headers=own).status_code == 200
        offer = client.get("/api/employees/E0047/notifications", headers=own).json()["offers"][0]
        command = {"command_id": str(uuid4()), "action": "view"}
        assert client.post(f'/api/employees/E0047/offers/{offer["id"]}/actions', headers=hr, json=command).status_code == 403
        assert client.post(f'/api/employees/E0047/offers/{offer["id"]}/actions', headers=own, json=command).status_code == 200
        assert client.get("/api/hr/notifications/journal", headers=hr).json()["offers"][0]["status"] == "viewed"
        assert not mail.sent

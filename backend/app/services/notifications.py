"""Durable, single-process notification workflow on the existing atomic overlay.

All mutations and SMTP submission hold DatasetService.lock. The send intent is
committed BEFORE network I/O. An interrupted submission is UNKNOWN, never retried
automatically. SMTP Message-ID is correlation, not an exactly-once guarantee.
"""
import hashlib
import json
from datetime import datetime, time, timedelta, timezone
from threading import Lock
from uuid import NAMESPACE_URL, uuid4, uuid5
from urllib.parse import quote

from app.ai.recommender import DisabledRecommender, validate_recommendation_result
from app.core.errors import DomainError
from app.schemas.notifications import (
    ActionReceipt, Delivery, EmployeeContact, EmployeeNotificationPreferences,
    GenerationRecord, JournalEntry, NotificationState, Offer,
)
from .mail_transport import MailFailure
from .progress_engine import effective_history
from .recommendation_context import build_recommendation_context
from .recommendation_engine import recommend

COMPANY_TIME = timezone(timedelta(hours=5))  # one shared company clock, no employee timezone settings
OPEN = {"proposed", "viewed", "snoozed"}
CLOSED = {"declined", "completed", "invalidated", "unanswered"}
PRIORITY = {"test": -1, "session": 0, "completion": 1, "reminder": 2, "offer": 3}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


class NotificationService:
    def __init__(self, dataset, ai_client, mailer, as_of_date, app_url, now=None):
        self.dataset, self.ai_client, self.mailer = dataset, ai_client, mailer
        self.as_of_date, self.app_url = as_of_date, app_url.rstrip("/")
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.run_lock = Lock()
        self.cursor = 0

    @property
    def state(self):
        return self.dataset.state.notifications

    def _save(self, state):
        # Notification metadata does not change the academic dataset revision.
        self.dataset.commit(self.dataset.state.model_copy(update={"notifications": state}))

    def _log(self, state, kind, employee_id=None, offer_id=None, delivery_id=None, detail=None):
        entry = JournalEntry(id=str(uuid4()), at=self.now(), type=kind, employee_id=employee_id,
                             offer_id=offer_id, delivery_id=delivery_id, detail=detail)
        return state.model_copy(update={"journal": state.journal + (entry,)})

    def _employee(self, employee_id):
        employee = self.dataset.capture().employees.get(employee_id)
        if employee is None:
            raise DomainError("not_found", "Employee not found")
        return employee

    def _input_fingerprint(self, employee_id, snapshot):
        return fingerprint({
            "employee": snapshot.employees.get(employee_id).model_dump(mode="json"),
            "history": [r.model_dump(mode="json") for r in effective_history(snapshot, employee_id)],
            "events": [e.model_dump(mode="json") for e in snapshot.events.list()],
            "roles": [r.model_dump(mode="json") for r in snapshot.bundle.role_profiles],
            "date": self.as_of_date(),
        })

    def recover(self):
        with self.dataset.lock:
            state = self.state.model_copy(deep=True)
            for key, row in state.deliveries.items():
                if row.status == "sending":
                    state.deliveries[key] = row.model_copy(update={"status": "unknown", "error_code": "interrupted_submission"})
                    state = self._log(state, "delivery_unknown", row.employee_id, row.offer_id, row.id, "interrupted_submission")
            self._save(state)

    def settings_view(self):
        with self.dataset.lock:
            state = self.state
            account = state.account.model_dump(exclude={"encrypted_password"}) if state.account else None
            return {"settings": state.settings, "account": account, "company_now": self.now().astimezone(COMPANY_TIME),
                    "encryption_ready": self.mailer.configured,
                    "ai_ready": not isinstance(self.ai_client, DisabledRecommender)}

    def update_settings(self, settings):
        with self.dataset.lock:
            if settings.version != self.state.settings.version:
                raise DomainError("conflict", "Notification settings changed; reload before saving")
            state = self.state.model_copy(deep=True)
            state = state.model_copy(update={"settings": settings.model_copy(update={"version": settings.version + 1})})
            if settings.enabled and not self.state.settings.enabled:
                self._compact(state)
            # Pending content/time are recomputed at dispatch; history stays immutable.
            state = self._log(state, "settings_updated", detail=str(state.settings.version))
            self._save(state)
        return self.settings_view()

    def connect(self, connection):
        try:
            account = self.mailer.connect(connection)
        except MailFailure as error:
            raise DomainError("unavailable", error.code) from error
        with self.dataset.lock:
            state = self.state.model_copy(update={"account": account}, deep=True)
            state = self._log(state, "mail_account_connected")
            self._save(state)
        return self.settings_view()

    def disconnect(self):
        with self.dataset.lock:
            state = self.state.model_copy(update={"account": None}, deep=True)
            self._save(self._log(state, "mail_account_disconnected"))
        return self.settings_view()

    def preferences(self, employee_id):
        with self.dataset.lock:
            self._employee(employee_id)
            return self.state.contacts.get(employee_id, EmployeeContact())

    def update_preferences(self, employee_id, preferences=None, hr_update=None):
        with self.dataset.lock:
            self._employee(employee_id)
            state = self.state.model_copy(deep=True)
            old = state.contacts.get(employee_id, EmployeeContact())
            if hr_update is not None:
                value = old.model_copy(update={"hr_paused": hr_update.hr_paused,
                    "preferences": old.preferences.model_copy(update={"email": hr_update.email})})
            else:
                value = old.model_copy(update={"preferences": preferences})
            if value.preferences.email != old.preferences.email:
                value = value.model_copy(update={"address_blocked": False})
                for key, delivery in state.deliveries.items():
                    if delivery.employee_id == employee_id and delivery.status == "failed" and delivery.error_code == "recipient_rejected":
                        state.deliveries[key] = delivery.model_copy(update={"status": "pending", "attempts": 0, "due_at": self.now(), "error_code": None})
            state.contacts[employee_id] = value
            if (old.hr_paused and not value.hr_paused) or (old.preferences.paused and not value.preferences.paused):
                self._compact(state, employee_id)
            self._save(self._log(state, "contact_updated" if hr_update else "preferences_updated", employee_id))
            return value

    def generate(self, employee_id):
        with self.run_lock:
            return self._generate(employee_id)

    def _generate(self, employee_id):
        snapshot = self.dataset.capture()
        if snapshot.employees.get(employee_id) is None:
            raise DomainError("not_found", "Employee not found")
        token = self._input_fingerprint(employee_id, snapshot)
        previous = self.state.generations.get(employee_id)
        if previous and previous.fingerprint == token and previous.result:
            return previous.result.model_copy(update={"revision": snapshot.revision})
        try:
            result = recommend(employee_id, snapshot, self.as_of_date(), self.ai_client)
        except DomainError as error:
            with self.dataset.lock:
                state = self.state.model_copy(deep=True)
                state.generations[employee_id] = GenerationRecord(fingerprint=token, status="failed", updated_at=self.now(),
                    retry_at=self.now() + timedelta(minutes=15), error_code=error.code)
                self._save(self._log(state, "recommendation_failed", employee_id, detail=error.code))
            raise
        with self.dataset.lock:
            current = self.dataset.capture()
            if self._input_fingerprint(employee_id, current) != token:
                raise DomainError("conflict", "Employee data changed while generating; retry with fresh context")
            context = build_recommendation_context(employee_id, current, self.as_of_date())
            result = result.model_copy(update={"revision": current.revision})
            validate_recommendation_result(context, result)
            state = self.state.model_copy(deep=True)
            selected = {item.event_id for item in result.recommendations}
            for oid, old in state.offers.items():
                if old.employee_id == employee_id and old.status in OPEN and old.event_id not in selected:
                    state.offers[oid] = old.model_copy(update={"status": "invalidated", "updated_at": self.now()})
                    self._cancel(state, oid)
            history = effective_history(current, employee_id)
            for rank, item in enumerate(result.recommendations):
                # Existing in-progress training should not receive a new invitation.
                if any(h.event_id == item.event_id and h.status in {"in_progress", "overdue"} for h in history):
                    continue
                candidate = next(c for c in context.candidates if c.event_id == item.event_id)
                session = candidate.eligibility.next_session
                recurring = str(session) if item.event_id == "EV_036" else "once"
                oid = str(uuid5(NAMESPACE_URL, f"career-quest:{employee_id}:{item.event_id}:{recurring}"))
                old = state.offers.get(oid)
                if old and old.status in (CLOSED - {"invalidated"}) | {"enrolled"}:
                    continue
                if old:
                    state.offers[oid] = old.model_copy(update={"explanation": item.explanation, "rank": rank,
                        "input_fingerprint": token, "session_date": session, "updated_at": self.now(),
                        "status": "proposed" if old.status == "invalidated" else old.status})
                else:
                    state.offers[oid] = Offer(id=oid, employee_id=employee_id, event_id=item.event_id,
                        title=candidate.title, explanation=item.explanation, rank=rank, created_at=self.now(),
                        updated_at=self.now(), session_date=session, input_fingerprint=token)
                    state = self._log(state, "offer_created", employee_id, oid)
            state.generations[employee_id] = GenerationRecord(fingerprint=token, status=result.status if result.status == "no_candidates" else "ready",
                updated_at=self.now(), result=result)
            self._save(state)
        return result

    def _cancel(self, state, offer_id, kinds=None):
        for key, row in state.deliveries.items():
            if row.offer_id == offer_id and row.status == "pending" and (kinds is None or row.kind in kinds):
                state.deliveries[key] = row.model_copy(update={"status": "cancelled", "block_reason": "offer_changed"})

    def _compact(self, state, employee_id=None):
        """After a pause, retain one relevant overdue letter, not a catch-up burst."""
        by_employee = {}
        for row in state.deliveries.values():
            if row.employee_id and row.status == "pending" and row.due_at <= self.now() and (employee_id is None or row.employee_id == employee_id):
                by_employee.setdefault(row.employee_id, []).append(row)
        for rows in by_employee.values():
            ordered = sorted(rows, key=lambda row: (PRIORITY[row.kind], -row.created_at.timestamp()))
            for row in ordered[1:]:
                state.deliveries[row.id] = row.model_copy(update={"status": "cancelled", "block_reason": "superseded_after_pause"})

    def action(self, employee_id, offer_id, command):
        token = fingerprint({"employee": employee_id, "offer": offer_id, "command": command.model_dump(mode="json")})
        with self.dataset.lock:
            state = self.state.model_copy(deep=True)
            prior = state.receipts.get(str(command.command_id))
            if prior:
                if prior.fingerprint != token:
                    raise DomainError("conflict", "Command ID already used")
                return prior.result
            offer = state.offers.get(offer_id)
            if offer is None or offer.employee_id != employee_id:
                raise DomainError("not_found", "Offer not found")
            if offer.status in CLOSED:
                raise DomainError("conflict", "Offer is closed")
            changes = {"updated_at": self.now()}
            if command.action == "view":
                if offer.status == "proposed":
                    changes["status"] = "viewed"
            elif command.action == "enroll":
                context = build_recommendation_context(employee_id, self.dataset.capture(), self.as_of_date())
                if offer.event_id not in {c.event_id for c in context.candidates}:
                    raise DomainError("conflict", "Course is no longer eligible")
                event = self.dataset.capture().events.get(offer.event_id)
                session = command.session_date or offer.session_date
                if event.format != "self_paced" and (session not in event.upcoming_sessions or session < max(self.as_of_date(), self.now().astimezone(COMPANY_TIME).date())):
                    raise DomainError("invalid", "Choose an available future session")
                changes.update(status="enrolled", session_date=session if event.format != "self_paced" else None, snoozed_until=None)
                self._cancel(state, offer_id)
            elif command.action == "later":
                if offer.status == "enrolled":
                    raise DomainError("conflict", "Already enrolled")
                if command.snoozed_until is None or command.snoozed_until <= self.now():
                    raise DomainError("invalid", "Choose a future reminder time")
                changes.update(status="snoozed", snoozed_until=command.snoozed_until)
                # Keep a single pending invitation/reminder instead of accumulating messages.
                self._cancel(state, offer_id)
            elif command.action == "decline":
                changes.update(status="declined", reason=command.reason, snoozed_until=None)
                self._cancel(state, offer_id)
            offer = offer.model_copy(update=changes)
            state.offers[offer_id] = offer
            state.receipts[str(command.command_id)] = ActionReceipt(fingerprint=token, result=offer)
            state = self._log(state, "offer_" + command.action, employee_id, offer_id, detail=command.reason)
            self._save(state)
            return offer

    def offers_view(self, employee_id):
        with self.dataset.lock:
            self._employee(employee_id)
            return {"offers": sorted((o for o in self.state.offers.values() if o.employee_id == employee_id), key=lambda o: (o.rank, o.created_at)),
                    "contact": self.state.contacts.get(employee_id, EmployeeContact()), "company_now": self.now().astimezone(COMPANY_TIME),
                    "generation": self.state.generations.get(employee_id)}

    def journal_view(self, employee_id=None, after=0, limit=100):
        with self.dataset.lock:
            state = self.state
            journal = [e for e in state.journal if employee_id is None or e.employee_id == employee_id]
            return {"items": journal[after:after + limit], "next_offset": min(after + limit, len(journal)), "total": len(journal),
                    "deliveries": [d for d in state.deliveries.values() if employee_id is None or d.employee_id == employee_id],
                    "offers": [o for o in state.offers.values() if employee_id is None or o.employee_id == employee_id],
                    "contacts": {key: value for key, value in state.contacts.items() if employee_id is None or key == employee_id},
                    "generations": {key: value.model_dump(exclude={"result"}) for key, value in state.generations.items() if employee_id is None or key == employee_id}}

    def _queue(self, state, offer, kind, due, sequence="0"):
        key = str(uuid5(NAMESPACE_URL, f"mail:{offer.id}:{kind}:{sequence}"))
        if key not in state.deliveries:
            state.deliveries[key] = Delivery(id=key, employee_id=offer.employee_id, offer_id=offer.id, kind=kind,
                due_at=due, created_at=self.now(), message_id=f"<{key}@careerquest.local>")
        elif state.deliveries[key].status == "cancelled" and state.deliveries[key].block_reason == "offer_changed":
            state.deliveries[key] = state.deliveries[key].model_copy(update={"status": "pending", "due_at": due, "block_reason": None})
        return state

    def _sync(self, state):
        snapshot = self.dataset.capture()
        for employee_id, contact in list(state.contacts.items()):
            if contact.preferences.paused_until and contact.preferences.paused_until <= self.now():
                state.contacts[employee_id] = contact.model_copy(update={"preferences": contact.preferences.model_copy(update={"paused_until": None})})
                self._compact(state, employee_id)
        contexts = {}
        for oid, offer in list(state.offers.items()):
            if offer.status in CLOSED:
                continue
            history = effective_history(snapshot, offer.employee_id)
            if any(r.event_id == offer.event_id and r.status == "completed" and (offer.event_id != "EV_036" or r.date == offer.session_date) for r in history):
                offer = offer.model_copy(update={"status": "completed", "updated_at": self.now()})
                state.offers[oid] = offer
                self._cancel(state, oid)
                self._queue(state, offer, "completion", self.now())
                state = self._log(state, "course_completed", offer.employee_id, oid)
                continue
            if offer.status == "enrolled":
                if offer.session_date:
                    due = datetime.combine(offer.session_date - timedelta(days=1), time(), COMPANY_TIME) + timedelta(minutes=state.settings.start_minute)
                    self._queue(state, offer, "session", due, str(offer.session_date))
                continue
            if offer.employee_id not in contexts:
                contexts[offer.employee_id] = build_recommendation_context(offer.employee_id, snapshot, self.as_of_date())
            valid = {c.event_id for c in contexts[offer.employee_id].candidates}
            if offer.event_id not in valid or self._input_fingerprint(offer.employee_id, snapshot) != offer.input_fingerprint:
                self._cancel(state, oid)
                state.offers[oid] = offer.model_copy(update={"status": "invalidated", "updated_at": self.now()})
                state = self._log(state, "offer_invalidated", offer.employee_id, oid)

        # At most one pending invitation per employee. Alternative courses remain in the cabinet.
        for employee_id in sorted({o.employee_id for o in state.offers.values()}):
            offers = sorted((o for o in state.offers.values() if o.employee_id == employee_id), key=lambda o: (o.rank, o.created_at))
            if any(o.status == "enrolled" for o in offers):
                continue
            for offer in offers:
                if offer.status not in OPEN:
                    continue
                if any(d.employee_id == employee_id and d.status in {"pending", "sending", "unknown"} and d.kind in {"offer", "reminder"} for d in state.deliveries.values()):
                    break
                if offer.snoozed_until and offer.snoozed_until > self.now():
                    break
                sent = sorted((d for d in state.deliveries.values() if d.offer_id == offer.id and d.status == "accepted" and d.kind in {"offer", "reminder"}), key=lambda d: d.accepted_at)
                if not sent:
                    self._queue(state, offer, "offer", offer.snoozed_until or self.now(), str(offer.snoozed_until or "first"))
                    break
                reminders = sum(d.kind == "reminder" for d in sent)
                if offer.snoozed_until and offer.snoozed_until > sent[-1].accepted_at:
                    self._queue(state, offer, "reminder", offer.snoozed_until, "requested:" + offer.snoozed_until.isoformat())
                elif reminders < state.settings.maximum_reminders:
                    self._queue(state, offer, "reminder", sent[-1].accepted_at + timedelta(days=state.settings.reminder_after_days), str(reminders + 1))
                elif self.now() >= sent[-1].accepted_at + timedelta(days=state.settings.cooldown_days):
                    state.offers[offer.id] = offer.model_copy(update={"status": "unanswered", "updated_at": self.now()})
                    state = self._log(state, "offer_no_response", employee_id, offer.id)
                    continue
                break
        return state

    def _window(self, moment, settings):
        local = moment.astimezone(COMPANY_TIME)
        start = datetime.combine(local.date(), time(), COMPANY_TIME) + timedelta(minutes=settings.start_minute)
        end = datetime.combine(local.date(), time(), COMPANY_TIME) + timedelta(minutes=settings.end_minute)
        if local < start:
            return start
        if local >= end:
            return start + timedelta(days=1)
        return moment

    def _gate(self, state, delivery):
        now = self.now()
        if delivery.kind != "test" and not state.settings.enabled:
            return "global_pause", None
        if delivery.kind != "test" and not getattr(state.settings, delivery.kind + "_enabled"):
            return "notification_type_disabled", None
        contact = state.contacts.get(delivery.employee_id, EmployeeContact())
        pref = contact.preferences
        if delivery.kind != "test":
            if contact.hr_paused or pref.paused:
                return "employee_pause", None
            if pref.paused_until and pref.paused_until > now:
                return "employee_pause", pref.paused_until
        if state.account is None or state.account.status != "connected":
            return "mail_account_unavailable", None
        if delivery.kind != "test" and (not pref.email or contact.address_blocked):
            return "email_missing" if not pref.email else "email_blocked", None
        if delivery.kind == "test":
            return ("scheduled", delivery.due_at) if delivery.due_at > now else (None, None)
        offer = state.offers[delivery.offer_id]
        if delivery.kind in {"offer", "reminder"} and offer.status not in OPEN:
            return "cancel", None
        if delivery.kind in {"offer", "reminder"} and any(o.employee_id == offer.employee_id and o.status == "enrolled" for o in state.offers.values()):
            return "already_learning", None
        if offer.snoozed_until and offer.snoozed_until > now and delivery.kind in {"offer", "reminder"}:
            return "snoozed", offer.snoozed_until
        if delivery.kind == "session" and (offer.status != "enrolled" or not offer.session_date or offer.session_date <= now.astimezone(COMPANY_TIME).date()):
            return "cancel", None
        if delivery.kind == "completion" and offer.status != "completed":
            return "cancel", None
        due = delivery.due_at
        offer_letters = sorted((d for d in state.deliveries.values() if d.offer_id == offer.id and d.status == "accepted" and d.kind in {"offer", "reminder"}), key=lambda d: d.accepted_at)
        if delivery.kind == "reminder" and offer_letters:
            requested = offer.snoozed_until and offer.snoozed_until > offer_letters[-1].accepted_at
            if not requested and sum(d.kind == "reminder" for d in offer_letters) >= state.settings.maximum_reminders:
                return "cancel", None
            recomputed = offer.snoozed_until if requested else offer_letters[-1].accepted_at + timedelta(days=state.settings.reminder_after_days)
            due = max(due, recomputed) if delivery.attempts else recomputed
        if delivery.kind == "session" and not delivery.attempts:
            due = datetime.combine(offer.session_date - timedelta(days=1), time(), COMPANY_TIME) + timedelta(minutes=state.settings.start_minute)
        sent = sorted((d for d in state.deliveries.values() if d.employee_id == delivery.employee_id and d.attempted_at and d.status in {"accepted", "unknown", "sending"}), key=lambda d: d.accepted_at or d.attempted_at)
        if sent:
            due = max(due, (sent[-1].accepted_at or sent[-1].attempted_at) + timedelta(hours=max(pref.minimum_interval_hours, state.settings.minimum_interval_hours)))
        recent = [d for d in sent if (d.accepted_at or d.attempted_at) > now - timedelta(days=7)]
        limit = min(pref.weekly_limit, state.settings.weekly_limit)
        if len(recent) >= limit:
            due = max(due, (recent[-limit].accepted_at or recent[-limit].attempted_at) + timedelta(days=7))
        allowed = self._window(max(now, due), state.settings)
        if allowed > now:
            return "frequency_or_time_window", allowed
        return None, None

    def _render(self, state, delivery):
        if delivery.kind == "test":
            return "Career Quest — проверка почты", "Это тестовое письмо из кабинета HR."
        offer = state.offers[delivery.offer_id]
        employee = self._employee(offer.employee_id)
        messages = {"offer": "Предлагаем следующий шаг развития: " + offer.title,
                    "reminder": "Напоминаем о предложении: " + offer.title,
                    "session": f"Занятие запланировано на {offer.session_date}: {offer.title}. Время уточните у организатора.",
                    "completion": "Завершено: " + offer.title + ". Прогресс навыков обновлён в кабинете."}
        link = self.app_url + "/employee/" + quote(employee.employee_id, safe="")
        values = {"name": employee.full_name.replace("\n", " ").replace("\r", " "),
                  "course": offer.title.replace("\n", " ").replace("\r", " "), "message": messages[delivery.kind],
                  "explanation": offer.explanation if delivery.kind in {"offer", "reminder"} else "",
                  "link": link, "signature": state.settings.signature}
        subject = state.settings.subject_template.format_map(values).replace("\r", " ").replace("\n", " ")
        body = state.settings.body_template.format_map(values)
        body += "\n\nПосмотреть предложение и настроить уведомления: " + link
        return subject, body

    def preview(self, employee_id):
        with self.dataset.lock:
            self._employee(employee_id)
            offer = next((o for o in self.state.offers.values() if o.employee_id == employee_id and o.status in OPEN), None)
            if offer is None:
                raise DomainError("not_found", "No active offer to preview")
            row = Delivery(id="preview", employee_id=employee_id, offer_id=offer.id, kind="offer", due_at=self.now(), created_at=self.now(), message_id="preview")
            subject, body = self._render(self.state, row)
            return {"subject": subject, "body": body}

    def queue_test(self, command):
        with self.dataset.lock:
            state = self.state.model_copy(deep=True)
            key = "test:" + str(command.command_id)
            if key in state.deliveries:
                if state.deliveries[key].recipient != command.recipient:
                    raise DomainError("conflict", "Test command ID already used")
                return state.deliveries[key]
            if sum(d.kind == "test" and d.created_at > self.now() - timedelta(hours=1) for d in state.deliveries.values()) >= 3:
                raise DomainError("conflict", "Maximum three test letters per hour")
            row = Delivery(id=key, kind="test", recipient=command.recipient, due_at=self.now(), created_at=self.now(), message_id=f"<{command.command_id}@careerquest.local>")
            state.deliveries[key] = row
            self._save(self._log(state, "test_queued", delivery_id=key))
            return row

    def resolve_unknown(self, delivery_id, command):
        with self.dataset.lock:
            state = self.state.model_copy(deep=True)
            row = state.deliveries.get(delivery_id)
            if row is None:
                raise DomainError("not_found", "Delivery not found")
            if row.status != "unknown":
                raise DomainError("conflict", "Only an unknown submission can be reconciled")
            state.deliveries[row.id] = row.model_copy(update={"status": command.outcome,
                "accepted_at": row.attempted_at if command.outcome == "accepted" else None})
            self._save(self._log(state, "delivery_reconciled", row.employee_id, row.offer_id, row.id, command.note))
            return state.deliveries[row.id]

    def retry_failed(self, delivery_id):
        with self.dataset.lock:
            state = self.state.model_copy(deep=True)
            row = state.deliveries.get(delivery_id)
            if row is None:
                raise DomainError("not_found", "Delivery not found")
            if row.status != "failed":
                raise DomainError("conflict", "Only a confirmed failed submission can be retried")
            state.deliveries[row.id] = row.model_copy(update={"status": "pending", "attempts": 0, "due_at": self.now(), "error_code": None})
            self._save(self._log(state, "manual_retry_requested", row.employee_id, row.offer_id, row.id))
            return state.deliveries[row.id]

    def dispatch(self, limit=10):
        for _ in range(limit):
            with self.dataset.lock:
                state = self._sync(self.state.model_copy(deep=True))
                selected = None
                for row in sorted(state.deliveries.values(), key=lambda d: (PRIORITY[d.kind], d.due_at, d.id)):
                    if row.status != "pending":
                        continue
                    reason, due = self._gate(state, row)
                    if reason:
                        state.deliveries[row.id] = row.model_copy(update={"block_reason": reason,
                            "status": "cancelled" if reason == "cancel" else "pending", "next_attempt_at": due})
                        continue
                    selected = row
                    break
                self._save(state)
                if selected is None:
                    break
                subject, body = self._render(state, selected)
                recipient = selected.recipient if selected.kind == "test" else state.contacts[selected.employee_id].preferences.email
                sending = selected.model_copy(update={"status": "sending", "attempts": selected.attempts + 1,
                    "attempted_at": self.now(), "block_reason": None, "recipient": recipient,
                    "next_attempt_at": None,
                    "sender": state.account.sender_email, "subject": subject, "body": body,
                    "settings_version": state.settings.version})
                state.deliveries[sending.id] = sending
                self._save(self._log(state, "submission_started", sending.employee_id, sending.offer_id, sending.id))
                try:
                    self.mailer.send(state.account, recipient, subject, body, sending.message_id)
                except MailFailure as error:
                    state = self.state.model_copy(deep=True)
                    status = "unknown" if error.uncertain else "pending" if error.retryable and sending.attempts < 4 else "failed"
                    state.deliveries[sending.id] = sending.model_copy(update={"status": status, "error_code": error.code,
                        "due_at": self.now() + timedelta(minutes=(5, 30, 120, 360)[min(sending.attempts - 1, 3)])})
                    if error.account_failure:
                        state = state.model_copy(update={"account": state.account.model_copy(update={"status": "auth_failed"})})
                        state.deliveries[sending.id] = sending.model_copy(update={"status": "pending", "error_code": error.code})
                    if error.address_failure and sending.employee_id:
                        contact = state.contacts[sending.employee_id]
                        state.contacts[sending.employee_id] = contact.model_copy(update={"address_blocked": True})
                    self._save(self._log(state, "submission_" + state.deliveries[sending.id].status, sending.employee_id, sending.offer_id, sending.id, error.code))
                except Exception:
                    # Unknown transport exceptions may occur after acceptance too.
                    state = self.state.model_copy(deep=True)
                    state.deliveries[sending.id] = sending.model_copy(update={"status": "unknown", "error_code": "transport_outcome_unknown"})
                    self._save(self._log(state, "delivery_unknown", sending.employee_id, sending.offer_id, sending.id))
                else:
                    state = self.state.model_copy(deep=True)
                    state.deliveries[sending.id] = sending.model_copy(update={"status": "accepted", "accepted_at": self.now(), "error_code": None})
                    self._save(self._log(state, "mail_accepted", sending.employee_id, sending.offer_id, sending.id))

    def tick(self):
        if not self.run_lock.acquire(blocking=False):
            return
        try:
            self.recover()
            self.dispatch(limit=1)
            if isinstance(self.ai_client, DisabledRecommender):
                return
            employees = sorted(self.dataset.capture().employees.list(), key=lambda e: e.employee_id)
            for _ in range(len(employees)):
                employee = employees[self.cursor % len(employees)]
                self.cursor += 1
                record = self.state.generations.get(employee.employee_id)
                token = self._input_fingerprint(employee.employee_id, self.dataset.capture())
                if record and record.fingerprint == token and (record.result or record.retry_at and record.retry_at > self.now()):
                    continue
                try:
                    self._generate(employee.employee_id)
                except DomainError:
                    pass  # Failure is isolated; next employee is visited on the next tick.
                break
        finally:
            self.run_lock.release()

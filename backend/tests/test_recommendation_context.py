import json
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.ai.prompts import build_recommendation_messages
from app.ai.recommender import JSONRecommender, validate_recommendation_result
from app.core.config import Settings
from app.core.errors import DomainError
from app.main import create_app
from app.repositories.dataset import build_snapshot
from app.schemas.recommendation import RecommendationResult
from app.schemas.state import RuntimeCompletion
from app.services.recommendation_context import build_recommendation_context
from app.services.recommendation_engine import recommend


def valid_result(context):
    candidate = context.candidates[0]
    return RecommendationResult.model_validate({
        "status": "success", "employee_id": context.employee_id,
        "revision": context.revision, "as_of_date": context.as_of_date,
        "recommendations": [{"event_id": candidate.event_id,
                             "explanation": "The activity develops a required skill and meets prerequisites.",
                             "evidence": candidate.factors}],
    })


def test_symbat_receives_complete_profile_and_linked_history(real_bundle, clock):
    snapshot = build_snapshot(real_bundle, revision=7)
    context = build_recommendation_context("E0047", snapshot, clock)
    assert context.employee == snapshot.employees.get("E0047")
    assert len(context.employee.skills) == 23
    assert context.employee.hire_date == date(2022, 12, 22)
    assert context.employee.manager_id == "E0050"
    assert len(context.history) == 22
    assert sum(row.event.mandatory for row in context.history) == 6
    originals = {row.record_id: row for row in snapshot.history.for_employee("E0047")}
    assert {row.participation.source_record_id for row in context.history} == set(originals)
    for row in context.history:
        assert row.participation.source == originals[row.participation.source_record_id]
        assert row.event == snapshot.events.get(row.participation.event_id)
        assert row.participation.source.employee_id == "E0047"
    assert len(context.skill_catalog) == 60
    assert len(context.event_catalog) == 40
    assert context.revision == 7 and context.as_of_date == clock
    assert len(context.facts) == 23


def test_score_is_separate_from_completion_and_projection(real_bundle, clock):
    context = build_recommendation_context("E0047", build_snapshot(real_bundle), clock)
    python = next(row for row in context.history if row.event.event_id == "EV_012")
    assert python.participation.status == "completed"
    assert python.participation.source.completion_pct == 100
    assert python.participation.source.score == 65
    assert python.participation.source.feedback_rating == 4
    assert not python.included_in_skill_projection
    assert python.completion_date_basis == "historical_date_proxy"
    assert context.current_skills["SK_PYTHON"] == context.employee.skills["SK_PYTHON"] == 3
    security = next(row for row in context.history
                    if row.event.event_id == "EV_011" and row.participation.status == "completed")
    assert security.included_in_skill_projection
    assert context.current_skills["SK_APP_SECURITY"] == 2
    excluded = {row.event_id: row.reasons for row in context.excluded_events}
    assert "already_completed" in excluded["EV_012"]
    assert "mandatory" in excluded["EV_001"]
    assert all(not event.mandatory for event in context.event_catalog
               if event.event_id in {c.event_id for c in context.candidates})


def test_null_goal_is_not_invented_and_full_role_requirements_are_present(real_bundle, clock):
    context = build_recommendation_context("E0047", build_snapshot(real_bundle), clock)
    assert context.employee.career_goal is None
    assert {target.purpose for target in context.role_requirements} == {"current_role", "next_grade_benchmark"}
    target = next(t for t in context.role_requirements if t.purpose == "next_grade_benchmark")
    assert target.profile.required_skills["SK_API_DESIGN"] == 4
    assert "SK_API_DESIGN" in target.profile.critical_skills
    assert len(target.analysis.gaps) == len(target.profile.required_skills)
    assert {p.key for p in context.unknown_preferences} == {
        "career_direction", "learning_interests", "weekly_learning_hours",
        "preferred_learning_format", "noncompletion_reasons",
    }
    architecture = [row for row in context.history if row.event.event_id == "EV_007"]
    assert [row.participation.status for row in architecture] == ["no_show", "dropped", "dropped"]
    assert [row.participation.source.feedback_rating for row in architecture] == [None, 2, 1]


def test_cross_role_goal_and_lead_keep_distinct_requirements(real_bundle, clock):
    snapshot = build_snapshot(real_bundle)
    context = build_recommendation_context("E0004", snapshot, clock)
    by_purpose = {target.purpose: target for target in context.role_requirements}
    assert by_purpose["explicit_career_goal"].profile.role == "Product Manager"
    assert by_purpose["next_grade_benchmark"].profile.role == "Data Analyst"
    assert "career_direction" not in {p.key for p in context.unknown_preferences}
    lead = build_recommendation_context("E0006", snapshot, clock)
    assert [target.purpose for target in lead.role_requirements] == ["current_role"]


def test_unfamiliar_employee_and_runtime_history_are_preserved(tiny_bundle, make_history, clock):
    source = make_history(status="in_progress", completion_pct=80, assigned_by="manager")
    completion = RuntimeCompletion(command_id=uuid4(), employee_id="TEST_EMP", event_id="EV_012",
        source_record_id=source.record_id, participation_date=source.date, completed_on=clock)
    snapshot = build_snapshot(tiny_bundle.model_copy(update={"history": (source,)}),
                              revision=9, runtime_completions=(completion,))
    context = build_recommendation_context("TEST_EMP", snapshot, clock)
    assert len(context.history) == 1
    row = context.history[0]
    assert row.participation.status == "completed"
    assert row.participation.source.completion_pct == 80
    assert row.completion_date_basis == "runtime_recorded"
    assert row.included_in_skill_projection
    assert context.current_skills["SK_PYTHON"] == 2
    fact = next(f for f in context.facts if f.kind == "history_record")
    assert fact.values["completion_pct"] == 100
    assert fact.values["assigned_by"] == "manager"


def test_messages_include_entire_context_and_do_not_merge_data_into_system(real_bundle, clock):
    context = build_recommendation_context("E0047", build_snapshot(real_bundle), clock)
    messages = build_recommendation_messages(context)
    payload = json.loads(messages[1]["content"])
    assert payload["context"] == context.model_dump(mode="json")
    assert "output_schema" in payload
    assert len(payload["context"]["history"]) == 22
    assert "Symbat Baimukhanova" not in messages[0]["content"]


def test_ai_receives_context_and_can_cite_full_history(tiny_bundle, make_history, clock):
    history = make_history(status="dropped", completion_pct=65, score=None, feedback_rating=2)
    snapshot = build_snapshot(tiny_bundle.model_copy(update={"history": (history,)}))
    context = build_recommendation_context("TEST_EMP", snapshot, clock)
    result = valid_result(context)
    history_fact = next(f for f in context.facts if f.kind == "history_record")
    data = result.model_dump(mode="json")
    data["recommendations"][0]["evidence"].append(history_fact.model_dump(mode="json"))
    data["hypotheses"] = [{"statement": "This specific activity may not have fitted; the reason is unknown.",
                           "evidence": [history_fact.model_dump(mode="json")], "needs_confirmation": True}]
    data["clarifying_questions"] = ["Что помешало завершить занятие?"]
    captured = []

    def complete(messages):
        captured.append(json.loads(messages[1]["content"])["context"])
        return json.dumps(data)

    response = recommend("TEST_EMP", snapshot, clock, JSONRecommender(complete))
    assert captured == [context.model_dump(mode="json")]
    assert response.hypotheses[0].needs_confirmation
    assert response.clarifying_questions == data["clarifying_questions"]
    data["hypotheses"][0]["evidence"][0]["values"]["feedback_rating"] = 5
    with pytest.raises(ValueError, match="Hypothesis evidence"):
        validate_recommendation_result(context, RecommendationResult.model_validate(data))


def test_invalid_ai_output_is_not_exposed(tiny_bundle, clock):
    def broken(messages):
        raise RuntimeError("private provider credentials must not be echoed")

    with pytest.raises(DomainError) as error:
        recommend("TEST_EMP", build_snapshot(tiny_bundle), clock, JSONRecommender(broken))
    assert error.value.code == "unavailable"
    assert "credentials" not in error.value.message


def test_no_candidates_does_not_call_provider(tiny_bundle, make_event, clock):
    snapshot = build_snapshot(tiny_bundle.model_copy(update={"events": (make_event(mandatory=True),)}))

    def unexpected(messages):
        pytest.fail("Provider should not be called without candidates")

    assert recommend("TEST_EMP", snapshot, clock, JSONRecommender(unexpected)).status == "no_candidates"


def test_context_route_and_real_recommendation_use_same_private_context(tmp_path, clock):
    settings = Settings(raw_dir=Path(__file__).resolve().parents[2] / "data/raw",
        state_path=tmp_path / "state.json",
        dev_identities={"self": {"role": "employee", "employee_id": "E0047"}, "hr": {"role": "hr"}})
    captured = []

    def complete(messages):
        from app.ai.client import AIRefinementInput
        context = AIRefinementInput.model_validate(json.loads(messages[1]["content"])["context"])
        captured.append(context)
        return valid_result(context).model_dump_json()

    with TestClient(create_app(settings, ai_client=JSONRecommender(complete))) as client:
        url = "/api/employees/E0047/recommendations/context"
        assert client.get(url).status_code == 401
        own = client.get(url, headers={"Authorization": "Bearer self"})
        assert own.status_code == 200 and own.headers["cache-control"] == "no-store"
        assert len(own.json()["history"]) == 22
        assert client.get("/api/employees/E0001/recommendations/context", headers={"Authorization": "Bearer self"}).status_code == 403
        assert client.get(url, headers={"Authorization": "Bearer hr"}).status_code == 200
        response = client.post("/api/employees/E0047/recommendations", headers={"Authorization": "Bearer self"})
        assert response.status_code == 200
        assert captured[0].model_dump(mode="json") == own.json()
        assert all(row.participation.source.employee_id == "E0047" for row in captured[0].history)

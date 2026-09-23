"""Build one employee's complete, linked, snapshot-consistent LLM context."""
from datetime import date

from app.ai.client import (
    AIRefinementInput, ExcludedEvent, HistoryContext, RoleRequirementContext,
    UnknownPreference,
)
from app.core.errors import DomainError
from app.repositories.dataset import DatasetSnapshot
from app.schemas.recommendation import RecommendationFactor as Factor
from .eligibility import evaluate_event
from .progress_engine import current_skills, effective_history
from .skill_gap import analyze_target
from .trajectory import targets_for


def build_recommendation_context(
    employee_id: str, snapshot: DatasetSnapshot, as_of_date: date,
) -> AIRefinementInput:
    employee = snapshot.employees.get(employee_id)
    if employee is None:
        raise DomainError("not_found", "Employee not found")
    if as_of_date < snapshot.meta.as_of_date:
        raise DomainError("invalid", "Recommendation date cannot precede the dataset snapshot")

    history = effective_history(snapshot, employee_id)
    current = current_skills(snapshot, employee_id, as_of_date)
    next_grade, career_goal = targets_for(employee, current, snapshot)
    targets = [target for target in (next_grade, career_goal) if target is not None]
    events = sorted(snapshot.events.list(), key=lambda event: event.event_id)
    evaluations = [evaluate_event(employee, current, targets, history, event, as_of_date) for event in events]

    requirements = []
    current_profile = snapshot.skills.role_profile(employee.role, employee.grade)
    requirements.append(RoleRequirementContext(
        purpose="current_role", profile=current_profile,
        analysis=analyze_target(current, current_profile, snapshot.skills),
    ))
    for purpose, target in (("next_grade_benchmark", next_grade), ("explicit_career_goal", career_goal)):
        if target is not None:
            requirements.append(RoleRequirementContext(
                purpose=purpose, profile=snapshot.skills.role_profile(target.role, target.grade), analysis=target,
            ))

    facts = [Factor(kind="profile_context", values={
        "role": employee.role, "grade": employee.grade,
        "has_explicit_career_goal": employee.career_goal is not None,
        "target_role": employee.career_goal.target_role if employee.career_goal else None,
        "target_grade": employee.career_goal.target_grade if employee.career_goal else None,
        "work_format": employee.work_format, "interface_language": employee.preferred_language,
        "tenure_months": employee.tenure_months,
    }, source_ids=[employee_id])]
    runtime_ids = {
        completion.source_record_id or "runtime:" + str(completion.command_id)
        for completion in snapshot.runtime_completions if completion.employee_id == employee_id
    }
    linked_history = []
    for participation in history:
        event = snapshot.events.get(participation.event_id)
        is_runtime = participation.source_record_id in runtime_ids
        basis = ("runtime_recorded" if is_runtime else "historical_date_proxy") if participation.status == "completed" else "not_completed"
        contributes = (
            participation.status == "completed" and participation.completed_on is not None
            and employee.last_review_date < participation.completed_on <= as_of_date
        )
        linked_history.append(HistoryContext(
            participation=participation, event=event, completion_date_basis=basis,
            included_in_skill_projection=contributes,
        ))
        source = participation.source
        # Original source progress remains available in participation.source even
        # when a runtime completion supersedes its old in_progress/overdue status.
        facts.append(Factor(kind="history_record", values={
            "event_id": event.event_id, "title": event.title, "date": participation.date.isoformat(),
            "status": participation.status,
            "completion_pct": 100 if participation.status == "completed" else source.completion_pct if source else None,
            "score": source.score if source else None,
            "feedback_rating": source.feedback_rating if source else None,
            "assigned_by": source.assigned_by if source else "self",
            "mandatory": event.mandatory, "format": event.format, "duration_hours": event.duration_hours,
            "completion_date_basis": basis, "included_in_skill_projection": contributes,
        }, source_ids=[participation.source_record_id, event.event_id]))

    unknown = [
        UnknownPreference(key="learning_interests", reason="The profile has no explicit interests field; participation is evidence for hypotheses only.",
                          suggested_question="Какие темы тебе сейчас интересно развивать?"),
        UnknownPreference(key="weekly_learning_hours", reason="Available study time and calendar are not provided.",
                          suggested_question="Сколько времени в неделю тебе удобно выделять на обучение?"),
        UnknownPreference(key="preferred_learning_format", reason="Work format is not a stated learning preference; interface language is not course language.",
                          suggested_question="Какой формат обучения тебе удобнее сейчас?"),
    ]
    if employee.career_goal is None:
        unknown.insert(0, UnknownPreference(key="career_direction", reason="career_goal is null; next grade is a comparison benchmark, not a declared ambition.",
                                           suggested_question="Хочешь развиваться в текущей роли или попробовать другое направление?"))
    if any(row.status in {"dropped", "declined", "no_show"} for row in history):
        unknown.append(UnknownPreference(key="noncompletion_reasons", reason="History contains outcomes but no reasons for them.",
                                         suggested_question="Что мешало завершить или посетить прошлые занятия?"))

    return AIRefinementInput(
        employee_id=employee_id, current_grade=employee.grade, employee=employee,
        current_skills=current, skill_catalog=list(snapshot.skills.list()),
        proficiency_scale=dict(snapshot.bundle.proficiency_scale), history=linked_history,
        event_catalog=events, role_requirements=requirements, targets=targets,
        candidates=[candidate for candidate in evaluations if candidate.eligibility.eligible],
        excluded_events=[ExcludedEvent(event_id=c.event_id, reasons=c.eligibility.reasons)
                         for c in evaluations if not c.eligibility.eligible],
        facts=facts, unknown_preferences=unknown, revision=snapshot.revision, as_of_date=as_of_date,
    )

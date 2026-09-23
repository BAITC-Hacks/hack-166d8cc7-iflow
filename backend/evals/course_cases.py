"""Local counterexamples, not the jury's undisclosed profiles. No network here."""
from datetime import date
from app.schemas.activity import Event, SkillGain
from app.schemas.employee import Employee
from app.schemas.history import ActivityHistory
from app.schemas.skill import RoleProfile


def cases(source):
    role = "Backend Engineer"
    def event(event_id, title, skill, gain, cap, prerequisites, hours):
        return Event(event_id=event_id, title=title, description=f"Практическая работа над навыком {skill}.",
            type="course", format="self_paced", duration_hours=hours, mandatory=False,
            target_roles=(role,), target_grades=("Middle",),
            develops_skills=(SkillGain(skill_id=skill, gain=gain, max_level=cap),),
            prerequisites=prerequisites, upcoming_sessions=())
    events = (
        event("CHECK_01", "Проектирование распределённых систем", "SK_SYSTEM_DESIGN", 1, 4, {"SK_SYSTEM_DESIGN": 2}, 8),
        event("CHECK_02", "Практика публичных выступлений", "SK_PUBLIC_SPEAKING", 1, 3, {}, 4),
        event("CHECK_03", "Основы системного проектирования", "SK_SYSTEM_DESIGN", 1, 2, {}, 6),
        event("CHECK_04", "Продвинутый Python", "SK_PYTHON", 2, 3, {"SK_PYTHON": 1}, 12),
    )
    profiles = (
        RoleProfile(role=role, grade="Middle", required_skills={"SK_SYSTEM_DESIGN": 1, "SK_PYTHON": 1}, critical_skills=("SK_SYSTEM_DESIGN",)),
        RoleProfile(role=role, grade="Senior", required_skills={"SK_SYSTEM_DESIGN": 3, "SK_PYTHON": 3, "SK_PUBLIC_SPEAKING": 1}, critical_skills=("SK_SYSTEM_DESIGN", "SK_PYTHON")),
    )
    definitions = [
        ("lowest_skill_trap", {"SK_SYSTEM_DESIGN": 2, "SK_PYTHON": 3, "SK_PUBLIC_SPEAKING": 0}, "CHECK_01"),
        ("prerequisite_trap", {"SK_SYSTEM_DESIGN": 0, "SK_PYTHON": 3, "SK_PUBLIC_SPEAKING": 1}, "CHECK_03"),
        ("score_65_is_completed", {"SK_SYSTEM_DESIGN": 2, "SK_PYTHON": 1, "SK_PUBLIC_SPEAKING": 0}, "CHECK_01"),
    ]
    for index, (name, skills, expected) in enumerate(definitions):
        employee = Employee.model_validate({**source.employees[0].model_dump(), "employee_id": f"CHECK_EMP_{index}",
            "full_name": f"Проверочный сотрудник {index + 1}", "role": role, "grade": "Middle", "manager_id": None,
            "career_goal": None, "preferred_language": "ru", "skills": skills, "last_review_date": date(2026, 9, 1)})
        history = []
        if index == 0:
            history = [ActivityHistory(record_id=f"CHECK_HISTORY_{i}", employee_id=employee.employee_id,
                event_id="CHECK_02", date=date(2026, i + 5, 15), due_date=None, status="no_show",
                completion_pct=0, score=None, feedback_rating=None, assigned_by="self") for i in range(3)]
        if index == 2:
            history = [ActivityHistory(record_id="CHECK_COMPLETED", employee_id=employee.employee_id,
                event_id="CHECK_04", date=date(2026, 8, 20), due_date=None, status="completed",
                completion_pct=100, score=65, feedback_rating=4, assigned_by="self")]
        yield name, source.model_copy(update={"employees": (employee,), "events": events,
            "role_profiles": profiles, "history": tuple(history)}), employee.employee_id, expected

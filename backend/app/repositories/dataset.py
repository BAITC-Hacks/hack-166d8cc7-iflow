from dataclasses import dataclass
from pathlib import Path
import hashlib
from app.schemas.dataset import SourceBundle, EmployeesDataset, EventsDataset, SkillsDataset
from app.schemas.state import RuntimeCompletion
from .employees import EmployeeRepository
from .events import EventRepository
from .skills import SkillRepository
from .history import HistoryRepository, parse_history

RAW_NAMES = ("employees.json","events.json","skills.json","activity_history.csv")

def parse_employees(data: bytes) -> EmployeesDataset:
    return EmployeesDataset.model_validate_json(data.decode("utf-8-sig"))

def unique(rows, key):
    values = [key(row) for row in rows]
    if len(values) != len(set(values)):
        raise ValueError("Duplicate identifiers")
    return set(values)

def validate_bundle(b: SourceBundle) -> None:
    employees = unique(b.employees, lambda r:r.employee_id)
    events = unique(b.events, lambda r:r.event_id)
    skills = unique(b.skills, lambda r:r.skill_id)
    profiles = unique(b.role_profiles, lambda r:(r.role,r.grade))
    unique(b.history, lambda r:r.record_id)
    unique(b.history, lambda r:(r.employee_id,r.event_id,r.date))
    def require(condition: bool, message: str):
        if not condition: raise ValueError(message)
    for row in b.employees:
        require((row.role,row.grade) in profiles, "Unknown role/grade")
        require(row.manager_id is None or row.manager_id in employees, "Unknown manager")
        require(set(row.skills) <= skills, "Unknown employee skill")
        require(row.hire_date <= b.meta.as_of_date and row.last_review_date <= b.meta.as_of_date, "Future assessment/hire date")
        if row.career_goal:
            require((row.career_goal.target_role,row.career_goal.target_grade) in profiles, "Unknown career goal")
    for row in b.role_profiles:
        require(set(row.required_skills) <= skills and set(row.critical_skills) <= set(row.required_skills), "Unknown role skill")
    for row in b.events:
        require(set(row.prerequisites) <= skills and {g.skill_id for g in row.develops_skills} <= skills, "Unknown event skill")
        unique(row.develops_skills, lambda g:g.skill_id)
        require(all((role,grade) in profiles for role in row.target_roles for grade in row.target_grades), "Unknown event audience")
    for row in b.history:
        require(row.employee_id in employees and row.event_id in events, "Unknown history reference")
        require(row.date <= b.meta.as_of_date, "Future historical participation")

@dataclass(frozen=True)
class DatasetSnapshot:
    bundle: SourceBundle
    revision: int
    runtime_completions: tuple[RuntimeCompletion,...]
    employees: EmployeeRepository
    events: EventRepository
    skills: SkillRepository
    history: HistoryRepository
    @property
    def meta(self):
        return self.bundle.meta

def build_snapshot(bundle: SourceBundle, revision: int = 0, runtime_completions: tuple[RuntimeCompletion,...] = ()) -> DatasetSnapshot:
    validate_bundle(bundle)
    return DatasetSnapshot(bundle.model_copy(deep=True), revision, runtime_completions, EmployeeRepository(bundle.employees),
        EventRepository(bundle.events), SkillRepository(bundle.skills,bundle.role_profiles), HistoryRepository(bundle.history))

class DatasetRepository:
    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir
    def load(self) -> SourceBundle:
        employees = parse_employees((self.raw_dir/"employees.json").read_bytes())
        events = EventsDataset.model_validate_json((self.raw_dir/"events.json").read_bytes())
        skills = SkillsDataset.model_validate_json((self.raw_dir/"skills.json").read_bytes())
        if not employees.meta == events.meta == skills.meta:
            raise ValueError("Dataset metadata mismatch")
        bundle = SourceBundle(**skills.model_dump(),employees=employees.employees,events=events.events,
                              history=parse_history((self.raw_dir/"activity_history.csv").read_bytes()))
        validate_bundle(bundle)
        return bundle
    def fingerprint(self) -> str:
        payload = "".join(name+hashlib.sha256((self.raw_dir/name).read_bytes()).hexdigest() for name in sorted(RAW_NAMES))
        return hashlib.sha256(payload.encode()).hexdigest()

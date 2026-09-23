from datetime import date
from .common import Model, ID
from .employee import Employee
from .activity import Event
from .skill import Skill, RoleProfile
from .history import ActivityHistory

class DatasetMeta(Model):
    dataset: ID
    version: ID
    as_of_date: date

class EmployeesDataset(Model):
    meta: DatasetMeta
    employees: tuple[Employee, ...]

class EventsDataset(Model):
    meta: DatasetMeta
    events: tuple[Event, ...]

class SkillsDataset(Model):
    meta: DatasetMeta
    proficiency_scale: dict[str,str]
    skills: tuple[Skill, ...]
    role_profiles: tuple[RoleProfile, ...]

class SourceBundle(SkillsDataset):
    employees: tuple[Employee, ...]
    events: tuple[Event, ...]
    history: tuple[ActivityHistory, ...]

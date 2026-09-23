from typing import Literal
from .common import Model, ID, Level, Grade

class Skill(Model):
    skill_id: ID
    name: ID
    type: Literal["hard", "soft"]
    category: ID
    description: str

class RoleProfile(Model):
    role: ID
    grade: Grade
    required_skills: dict[ID, Level]
    critical_skills: tuple[ID, ...]

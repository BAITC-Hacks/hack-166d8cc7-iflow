from datetime import date
from typing import Annotated, Literal
from pydantic import Field
from .common import Model, ID, Level, Grade

class SkillGain(Model):
    skill_id: ID
    gain: Annotated[int, Field(ge=0, le=5)]
    max_level: Level

class Event(Model):
    event_id: ID
    title: ID
    description: str
    type: Literal["compliance","onboarding","course","workshop","mentoring","certification","meetup"]
    format: Literal["online","offline","self_paced"]
    duration_hours: Annotated[float, Field(gt=0)]
    mandatory: bool
    target_roles: tuple[ID, ...]
    target_grades: tuple[Grade, ...]
    develops_skills: tuple[SkillGain, ...]
    prerequisites: dict[ID, Level]
    upcoming_sessions: tuple[date, ...]

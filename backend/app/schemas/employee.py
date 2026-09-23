from datetime import date
from typing import Annotated, Literal
from pydantic import Field
from .common import Model, ID, Level, Grade

class CareerGoal(Model):
    target_role: ID
    target_grade: Grade

class Employee(Model):
    employee_id: ID
    full_name: ID
    department: ID
    role: ID
    grade: Grade
    manager_id: ID | None
    hire_date: date
    tenure_months: Annotated[int, Field(ge=0)]
    work_format: Literal["office", "hybrid", "remote"]
    preferred_language: Literal["kk", "ru", "en"]
    career_goal: CareerGoal | None
    skills: dict[ID, Level]
    last_review_date: date

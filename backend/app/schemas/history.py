from datetime import date as Date
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .common import Model, ID

Status = Literal["completed","in_progress","dropped","no_show","declined","overdue"]

class ActivityHistory(Model):
    record_id: ID
    employee_id: ID
    event_id: ID
    date: Date
    due_date: Date | None
    status: Status
    completion_pct: Annotated[int, Field(ge=0, le=100)]
    score: Annotated[int, Field(ge=0, le=100)] | None
    feedback_rating: Annotated[int, Field(ge=1, le=5)] | None
    assigned_by: Literal["self","manager","hr"]

    @model_validator(mode="after")
    def status_consistent(self):
        pct = self.completion_pct
        if self.status == "completed" and pct != 100:
            raise ValueError("Completed participation requires 100 percent")
        if self.status in ("no_show","declined") and pct != 0:
            raise ValueError("Absent participation requires zero percent")
        if self.status in ("in_progress","overdue") and pct > 95:
            raise ValueError("Unfinished participation cannot exceed 95 percent")
        if self.status == "dropped" and not 5 <= pct <= 95:
            raise ValueError("Dropped participation requires 5 to 95 percent")
        return self

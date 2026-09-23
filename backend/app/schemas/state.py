from datetime import date
from typing import Literal, Annotated
from uuid import UUID
from pydantic import Field
from .common import Model
from .employee import Employee
from .history import ActivityHistory
from .responses import CompletionResult
from .market import MarketReceipt
from .notifications import NotificationState

class RuntimeCompletion(Model):
    command_id: UUID
    employee_id: str
    event_id: str
    source_record_id: str | None
    participation_date: date
    completed_on: date

class CompletionReceipt(Model):
    request_fingerprint: str
    result: CompletionResult

class MutableState(Model):
    schema_version: Literal[1] = 1
    raw_fingerprint: str
    revision: Annotated[int,Field(ge=0)] = 0
    imported_employees: tuple[Employee,...] = ()
    imported_history: tuple[ActivityHistory,...] = ()
    completions: tuple[RuntimeCompletion,...] = ()
    receipts: dict[str,CompletionReceipt] = Field(default_factory=dict)
    market_receipts: dict[str,MarketReceipt] = Field(default_factory=dict)
    notifications: NotificationState = Field(default_factory=NotificationState)

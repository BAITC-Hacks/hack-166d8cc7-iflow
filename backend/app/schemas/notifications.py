"""Persisted mail workflow; credentials are never part of public responses."""
import re
from datetime import date
from string import Formatter
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, SecretStr, field_validator, model_validator
from .common import Model
from .recommendation import RecommendationResult


def email_address(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if len(value) > 254 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}", value):
        raise ValueError("Invalid email address")
    return value


class NotificationSettings(Model):
    version: int = Field(default=0, ge=0)
    enabled: bool = False
    start_minute: int = Field(default=600, ge=0, le=1439)
    end_minute: int = Field(default=1080, ge=1, le=1440)
    minimum_interval_hours: int = Field(default=24, ge=1, le=720)
    weekly_limit: int = Field(default=2, ge=1, le=14)
    reminder_after_days: int = Field(default=7, ge=1, le=90)
    maximum_reminders: int = Field(default=1, ge=0, le=5)
    cooldown_days: int = Field(default=14, ge=1, le=180)
    offer_enabled: bool = True
    reminder_enabled: bool = True
    session_enabled: bool = True
    completion_enabled: bool = True
    subject_template: str = Field(default="Career Quest: {course}", min_length=1, max_length=200)
    body_template: str = Field(default="Здравствуйте, {name}!\n\n{message}\n\n{explanation}\n\n{link}\n\n{signature}", min_length=1, max_length=5000)
    signature: str = Field(default="Команда развития сотрудников", max_length=500)

    @model_validator(mode="after")
    def valid_window_and_templates(self):
        if self.start_minute >= self.end_minute:
            raise ValueError("Sending window must start before it ends on the same day")
        if "\r" in self.subject_template or "\n" in self.subject_template:
            raise ValueError("Subject must be a single line")
        for template in (self.subject_template, self.body_template):
            for _, name, spec, conversion in Formatter().parse(template):
                if name is not None and (name not in {"name", "course", "message", "explanation", "link", "signature"} or spec or conversion):
                    raise ValueError("Unsupported template placeholder")
        return self


class EmployeeNotificationPreferences(Model):
    email: str | None = None
    paused: bool = False
    paused_until: AwareDatetime | None = None
    minimum_interval_hours: int = Field(default=24, ge=1, le=2160)
    weekly_limit: int = Field(default=2, ge=1, le=14)
    _email = field_validator("email")(email_address)


class EmployeeContact(Model):
    preferences: EmployeeNotificationPreferences = Field(default_factory=EmployeeNotificationPreferences)
    hr_paused: bool = False
    address_blocked: bool = False


class HRContactUpdate(Model):
    email: str | None = None
    hr_paused: bool = False
    _email = field_validator("email")(email_address)


class SMTPConnection(Model):
    host: str = Field(min_length=1, max_length=253, pattern=r"^[A-Za-z0-9.-]+$")
    port: int = Field(default=465, ge=1, le=65535)
    security: Literal["ssl", "starttls"] = "ssl"
    username: str = Field(min_length=1, max_length=254, pattern=r"^[^\r\n]+$")
    sender_email: str
    sender_name: str = Field(default="Career Quest HR", min_length=1, max_length=100, pattern=r"^[^\r\n]+$")
    password: SecretStr = Field(min_length=1, max_length=2048)
    _email = field_validator("sender_email")(email_address)


class MailAccount(Model):
    host: str
    port: int
    security: Literal["ssl", "starttls"]
    username: str
    sender_email: str
    sender_name: str
    encrypted_password: str
    status: Literal["connected", "auth_failed", "disconnected"] = "connected"


class Offer(Model):
    id: str
    employee_id: str
    event_id: str
    title: str
    explanation: str
    rank: int
    status: Literal["proposed", "viewed", "snoozed", "enrolled", "declined", "completed", "invalidated", "unanswered"] = "proposed"
    created_at: AwareDatetime
    updated_at: AwareDatetime
    snoozed_until: AwareDatetime | None = None
    session_date: date | None = None
    reason: str | None = None
    input_fingerprint: str


class Delivery(Model):
    id: str
    employee_id: str | None = None
    offer_id: str | None = None
    kind: Literal["offer", "reminder", "session", "completion", "test"]
    status: Literal["pending", "sending", "accepted", "unknown", "failed", "cancelled"] = "pending"
    due_at: AwareDatetime
    next_attempt_at: AwareDatetime | None = None
    created_at: AwareDatetime
    attempted_at: AwareDatetime | None = None
    accepted_at: AwareDatetime | None = None
    attempts: int = 0
    block_reason: str | None = None
    error_code: str | None = None
    recipient: str | None = None
    sender: str | None = None
    subject: str | None = None
    body: str | None = None
    settings_version: int | None = None
    message_id: str


class JournalEntry(Model):
    id: str
    at: AwareDatetime
    type: str
    employee_id: str | None = None
    offer_id: str | None = None
    delivery_id: str | None = None
    detail: str | None = None


class GenerationRecord(Model):
    fingerprint: str
    status: Literal["ready", "no_candidates", "failed"]
    updated_at: AwareDatetime
    retry_at: AwareDatetime | None = None
    error_code: str | None = None
    result: RecommendationResult | None = None


class OfferAction(Model):
    command_id: UUID
    action: Literal["view", "enroll", "later", "decline"]
    snoozed_until: AwareDatetime | None = None
    session_date: date | None = None
    reason: str | None = Field(default=None, max_length=1000)


class ActionReceipt(Model):
    fingerprint: str
    result: Offer


class TestMailCommand(Model):
    command_id: UUID
    recipient: str
    _email = field_validator("recipient")(email_address)


class ResolveDelivery(Model):
    outcome: Literal["accepted", "failed"]
    note: str = Field(min_length=3, max_length=500)


class NotificationState(Model):
    settings: NotificationSettings = Field(default_factory=NotificationSettings)
    account: MailAccount | None = None
    contacts: dict[str, EmployeeContact] = Field(default_factory=dict)
    offers: dict[str, Offer] = Field(default_factory=dict)
    deliveries: dict[str, Delivery] = Field(default_factory=dict)
    generations: dict[str, GenerationRecord] = Field(default_factory=dict)
    receipts: dict[str, ActionReceipt] = Field(default_factory=dict)
    journal: tuple[JournalEntry, ...] = ()

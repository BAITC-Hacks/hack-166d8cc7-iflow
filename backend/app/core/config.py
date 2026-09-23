from pathlib import Path
from datetime import date
import json
import os
from typing import Literal
from dotenv import dotenv_values
from pydantic import Field, SecretStr
from app.schemas.common import Model
from .auth import Principal

ROOT = Path(__file__).resolve().parents[3]
DEMO_IDENTITIES={
    "demo-employee":{"role":"employee","employee_id":"E0001"},
    "demo-active":{"role":"employee","employee_id":"E0004"},
    "demo-hr":{"role":"hr"},
}

class Settings(Model):
    raw_dir: Path = ROOT/"data/raw"
    state_path: Path = ROOT/"data/state/state.json"
    allowed_origin: str = "http://localhost:3000"
    dev_identities: dict[str,Principal] = Field(default_factory=dict)
    application_date: date | None = None
    notifications_worker_enabled: bool = True
    notification_poll_seconds: float = Field(default=2, ge=0.1, le=3600)
    public_app_url: str = "http://localhost:3000"
    mail_encryption_key: SecretStr | None = Field(default=None, repr=False)
    ai_provider: Literal["none", "openai"] = "none"
    openai_api_key: SecretStr | None = Field(default=None, repr=False)
    openai_model: str = Field(default="gpt-4.1-mini", min_length=1)
    ai_timeout_seconds: float = Field(default=10, ge=1, le=120)
    ai_max_output_tokens: int = Field(default=1400, ge=256, le=4096)
    ai_auto_prepare: bool = False

    @classmethod
    def from_env(cls, env_file: Path | None = None):
        # Read only the project file; process variables take precedence. Do not
        # mutate os.environ or expose credentials through a public config dump.
        values = {k: v for k, v in dotenv_values(env_file or ROOT/".env", interpolate=False, encoding="utf-8-sig").items() if v is not None}
        values.update(os.environ)
        get = values.get
        return cls(raw_dir=get("DATA_RAW_DIR",str(ROOT/"data/raw")),
            state_path=get("STATE_PATH",str(ROOT/"data/state/state.json")),
            allowed_origin=get("FRONTEND_ORIGIN","http://localhost:3000"),
            # Public historical demo credentials are never accepted by env startup.
            dev_identities={k:v for k,v in json.loads(get("DEV_IDENTITIES_JSON", "{}")).items() if k not in DEMO_IDENTITIES},
            application_date=get("APPLICATION_DATE") or None,
            notifications_worker_enabled=get("NOTIFICATION_WORKER_ENABLED", "true"),
            notification_poll_seconds=get("NOTIFICATION_POLL_SECONDS", "2"),
            public_app_url=get("PUBLIC_APP_URL", "http://localhost:3000"),
            mail_encryption_key=get("MAIL_ENCRYPTION_KEY") or None,
            ai_provider=get("AI_PROVIDER", "none").strip().lower(),
            openai_api_key=get("OPENAI_API_KEY") or None,
            openai_model=get("OPENAI_MODEL") or "gpt-4.1-mini",
            ai_timeout_seconds=get("AI_TIMEOUT_SECONDS", "10"),
            ai_max_output_tokens=get("AI_MAX_OUTPUT_TOKENS", "1400"),
            ai_auto_prepare=get("AI_AUTO_PREPARE", "false"))

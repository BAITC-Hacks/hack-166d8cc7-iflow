from pathlib import Path
from datetime import date
import json
import os
from pydantic import Field
from app.schemas.common import Model
from .auth import Principal

ROOT = Path(__file__).resolve().parents[3]
DEMO_IDENTITIES={"demo-employee":{"role":"employee","employee_id":"E0001"},"demo-hr":{"role":"hr"}}

class Settings(Model):
    raw_dir: Path = ROOT/"data/raw"
    state_path: Path = ROOT/"data/state/state.json"
    allowed_origin: str = "http://localhost:3000"
    dev_identities: dict[str,Principal] = Field(default_factory=lambda:{k:Principal(**v) for k,v in DEMO_IDENTITIES.items()})
    application_date: date | None = None

    @classmethod
    def from_env(cls):
        return cls(raw_dir=os.getenv("DATA_RAW_DIR",str(ROOT/"data/raw")),
            state_path=os.getenv("STATE_PATH",str(ROOT/"data/state/state.json")),
            allowed_origin=os.getenv("FRONTEND_ORIGIN","http://localhost:3000"),
            dev_identities=json.loads(os.getenv("DEV_IDENTITIES_JSON",json.dumps(DEMO_IDENTITIES))),
            application_date=os.getenv("APPLICATION_DATE") or None)

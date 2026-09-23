from pathlib import Path
import os
import tempfile
from app.schemas.state import MutableState

class StateRepository:
    def __init__(self,path: Path):
        self.path=path
    def load(self,expected_fingerprint: str) -> MutableState:
        if not self.path.exists(): return MutableState(raw_fingerprint=expected_fingerprint)
        state=MutableState.model_validate_json(self.path.read_bytes())
        if state.raw_fingerprint!=expected_fingerprint:
            raise ValueError("Raw data fingerprint differs from saved state; restore matching data or explicitly reset demo state")
        return state
    def save(self,state: MutableState) -> None:
        state=MutableState.model_validate(state.model_dump())
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=self.path.parent,delete=False) as stream:
                temporary=Path(stream.name)
                stream.write(state.model_dump_json())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary,self.path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

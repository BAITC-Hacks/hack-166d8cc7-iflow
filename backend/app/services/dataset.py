from threading import Lock
from app.repositories.dataset import DatasetSnapshot, build_snapshot
from app.repositories.state import StateRepository
from app.schemas.state import MutableState

class DatasetService:
    def __init__(self,snapshot: DatasetSnapshot,state_repository: StateRepository | None = None,raw_fingerprint: str = ""):
        self.raw_bundle=snapshot.bundle.model_copy(deep=True)
        self.lock=Lock()
        self.state_repository=state_repository
        self.state=state_repository.load(raw_fingerprint) if state_repository else MutableState(raw_fingerprint=raw_fingerprint)
        self._snapshot=self.preview(self.state)
    def capture(self) -> DatasetSnapshot:
        return self._snapshot
    def preview(self,state: MutableState) -> DatasetSnapshot:
        state=MutableState.model_validate(state.model_dump())
        bundle=self.raw_bundle.model_copy(update={
            "employees":self.raw_bundle.employees+state.imported_employees,
            "history":self.raw_bundle.history+state.imported_history})
        return build_snapshot(bundle,state.revision,state.completions)
    def commit(self,next_state: MutableState) -> DatasetSnapshot:
        # Caller holds the single mutation lock from read through publication.
        if next_state==self.state: return self._snapshot
        candidate=self.preview(next_state)
        if self.state_repository is None: raise RuntimeError("State repository is required for mutations")
        self.state_repository.save(next_state)
        self.state=next_state
        self._snapshot=candidate
        return candidate

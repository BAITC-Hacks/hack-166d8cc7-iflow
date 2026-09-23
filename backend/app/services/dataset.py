from app.repositories.dataset import DatasetSnapshot

class DatasetService:
    def __init__(self,snapshot: DatasetSnapshot):
        self._snapshot=snapshot
    def capture(self) -> DatasetSnapshot:
        return self._snapshot

import csv
import io
from app.schemas.history import ActivityHistory

def parse_history(data: bytes) -> tuple[ActivityHistory, ...]:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)) or set(reader.fieldnames) != set(ActivityHistory.model_fields):
        raise ValueError("History headers do not match the starter-kit schema")
    return tuple(ActivityHistory.model_validate({k: None if v == "" else v for k,v in row.items()}) for row in reader)

class HistoryRepository:
    def __init__(self, rows: tuple[ActivityHistory, ...]):
        self._rows = {row.record_id: row.model_copy(deep=True) for row in rows}
    def list(self) -> tuple[ActivityHistory, ...]:
        return tuple(row.model_copy(deep=True) for row in self._rows.values())
    def get(self, record_id: str) -> ActivityHistory | None:
        row = self._rows.get(record_id)
        return row.model_copy(deep=True) if row else None
    def for_employee(self, employee_id: str) -> tuple[ActivityHistory, ...]:
        return tuple(row for row in self.list() if row.employee_id == employee_id)

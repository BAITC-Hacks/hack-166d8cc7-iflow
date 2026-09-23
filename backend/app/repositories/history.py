import csv
import io
from pydantic import ValidationError
from .validation import SourceValidationError
from app.schemas.history import ActivityHistory

def parse_history(data: bytes) -> tuple[ActivityHistory, ...]:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)) or set(reader.fieldnames) != set(ActivityHistory.model_fields):
        raise SourceValidationError([{"loc":["activity_history.csv",1],"type":"headers","message":"Headers must match the starter-kit schema"}])
    rows=[]
    for line,row in enumerate(reader,start=2):
        try:
            rows.append(ActivityHistory.model_validate({k: None if v == "" else v for k,v in row.items()}))
        except ValidationError as error:
            raise SourceValidationError([{"loc":["activity_history.csv",line,*e["loc"]],"type":e["type"],"message":"Invalid value"} for e in error.errors()]) from error
    return tuple(rows)

class HistoryRepository:
    def __init__(self, rows: tuple[ActivityHistory, ...]):
        self._rows = {row.record_id: row.model_copy(deep=True) for row in rows}
    def list(self) -> tuple[ActivityHistory, ...]:
        return tuple(row.model_copy(deep=True) for row in self._rows.values())
    def get(self, record_id: str) -> ActivityHistory | None:
        row = self._rows.get(record_id)
        return row.model_copy(deep=True) if row else None
    def for_employee(self, employee_id: str) -> tuple[ActivityHistory, ...]:
        return tuple(row.model_copy(deep=True) for row in self._rows.values() if row.employee_id == employee_id)

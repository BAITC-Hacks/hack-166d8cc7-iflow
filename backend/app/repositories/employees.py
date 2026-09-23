from app.schemas.employee import Employee

class EmployeeRepository:
    def __init__(self, rows: tuple[Employee, ...]):
        self._rows = {row.employee_id: row.model_copy(deep=True) for row in rows}
    def list(self) -> tuple[Employee, ...]:
        return tuple(row.model_copy(deep=True) for row in self._rows.values())
    def get(self, key: str) -> Employee | None:
        row = self._rows.get(key)
        return row.model_copy(deep=True) if row else None

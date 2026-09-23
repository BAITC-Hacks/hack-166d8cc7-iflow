from app.schemas.activity import Event

class EventRepository:
    def __init__(self, rows: tuple[Event, ...]):
        self._rows = {row.event_id: row.model_copy(deep=True) for row in rows}
    def list(self) -> tuple[Event, ...]:
        return tuple(row.model_copy(deep=True) for row in self._rows.values())
    def get(self, key: str) -> Event | None:
        row = self._rows.get(key)
        return row.model_copy(deep=True) if row else None

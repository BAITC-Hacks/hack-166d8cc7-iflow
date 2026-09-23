from datetime import date
from app.core.errors import DomainError
from app.repositories.dataset import DatasetSnapshot
from app.schemas.recommendation import RecommendationResult

def recommend(employee_id: str,snapshot: DatasetSnapshot,as_of_date: date) -> RecommendationResult:
    if snapshot.employees.get(employee_id) is None:
        raise DomainError("not_found","Employee not found")
    raise DomainError("recommendations_not_implemented","AI recommendations are not implemented")

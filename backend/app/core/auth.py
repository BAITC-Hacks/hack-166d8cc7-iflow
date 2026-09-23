from typing import Literal
from pydantic import model_validator
from app.schemas.common import Model
from .errors import DomainError

class Principal(Model):
    role: Literal["employee","hr"]
    employee_id: str | None = None
    @model_validator(mode="after")
    def employee_has_subject(self):
        if self.role=="employee" and not self.employee_id:
            raise ValueError("Employee identity needs a subject")
        return self

def resolve_principal(authorization: str | None, identities: dict[str,Principal]) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        raise DomainError("unauthorized","A development bearer token is required")
    principal=identities.get(authorization[7:])
    if principal is None: raise DomainError("unauthorized","Unknown identity")
    return principal

def require_access(principal: Principal, employee_id: str) -> None:
    if principal.role!="hr" and principal.employee_id!=employee_id:
        raise DomainError("forbidden","Access denied")

def require_hr(principal: Principal) -> None:
    if principal.role!="hr": raise DomainError("forbidden","HR access required")

def require_self(principal: Principal, employee_id: str) -> None:
    if principal.role!="employee" or principal.employee_id!=employee_id:
        raise DomainError("forbidden","Only the employee may complete their activity")

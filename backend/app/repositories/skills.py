from app.schemas.skill import Skill, RoleProfile

class SkillRepository:
    def __init__(self, rows: tuple[Skill,...], profiles: tuple[RoleProfile,...]):
        self._rows = {r.skill_id:r.model_copy(deep=True) for r in rows}
        self._profiles = {(r.role,r.grade):r.model_copy(deep=True) for r in profiles}
    def list(self) -> tuple[Skill,...]:
        return tuple(r.model_copy(deep=True) for r in self._rows.values())
    def get(self, key: str) -> Skill | None:
        row = self._rows.get(key)
        return row.model_copy(deep=True) if row else None
    def role_profile(self, role: str, grade: str) -> RoleProfile | None:
        row = self._profiles.get((role,grade))
        return row.model_copy(deep=True) if row else None

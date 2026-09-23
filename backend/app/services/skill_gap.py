from collections.abc import Mapping
from app.schemas.skill import RoleProfile
from app.schemas.responses import SkillGap, TargetAnalysis
from app.repositories.skills import SkillRepository

def calculate_gaps(current: Mapping[str,int], profile: RoleProfile, skills: SkillRepository) -> list[SkillGap]:
    return [SkillGap(skill_id=k,name=skills.get(k).name,current_level=current.get(k,0),
        required_level=v,gap=max(v-current.get(k,0),0),is_critical=k in profile.critical_skills)
        for k,v in profile.required_skills.items()]

def analyze_target(current: Mapping[str,int], profile: RoleProfile, skills: SkillRepository) -> TargetAnalysis:
    total=sum(profile.required_skills.values())
    coverage=sum(min(current.get(k,0),v) for k,v in profile.required_skills.items())/total if total else 1.0
    return TargetAnalysis(role=profile.role,grade=profile.grade,gaps=calculate_gaps(current,profile,skills),requirement_coverage=coverage)

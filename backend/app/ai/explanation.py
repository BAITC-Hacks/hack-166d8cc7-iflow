"""Render user-facing facts from the dataset, never from model prose."""
from collections import Counter


def factual_explanation(context, candidate):
    ru = context.employee.preferred_language != "en"
    names = {s.skill_id: s.name for s in context.skill_catalog}
    event = next(e for e in context.event_catalog if e.event_id == candidate.event_id)
    text = [f"{context.employee.role}, {context.employee.grade}."]
    for requirement in context.role_requirements:
        if requirement.purpose == "current_role":
            continue
        target = requirement.analysis
        if requirement.purpose == "next_grade_benchmark" and any(
            r.purpose == "explicit_career_goal" and (r.analysis.role,r.analysis.grade)==(target.role,target.grade)
            for r in context.role_requirements):
            continue
        default = context.employee.career_goal is None
        label = ("Ориентир по умолчанию, цель сотрудником не заявлена" if default else
                 "Заявленная карьерная цель" if requirement.purpose == "explicit_career_goal" else "Следующий грейд") if ru else (
                 "Default benchmark, not a stated employee ambition" if default else
                 "Stated career goal" if requirement.purpose == "explicit_career_goal" else "Next-grade benchmark")
        text.append(f"{label}: {target.role} / {target.grade}.")
        for gap in target.gaps:
            if gap.gap <= 0:
                continue
            gain = candidate.possible_skill_gains.get(gap.skill_id, 0)
            critical = ("критичный" if ru else "critical") if gap.is_critical else ("некритичный" if ru else "noncritical")
            if gain > 0:
                after = gap.current_level + gain
                remaining = max(0, gap.required_level - after)
                text.append(f"{names[gap.skill_id]} ({critical}): {gap.current_level} → {after}; " +
                    (f"требуется {gap.required_level}, остаток после курса {remaining}." if ru else
                     f"required {gap.required_level}, remaining after activity {remaining}."))
            elif gap.is_critical:
                available = any(c.possible_skill_gains.get(gap.skill_id, 0) > 0 for c in context.candidates)
                text.append(f"{names[gap.skill_id]} ({critical}): {gap.current_level}/{gap.required_level}. " +
                    ("Этот курс не закрывает пробел. " if ru else "This activity does not close this gap. ") +
                    (("Сейчас нет доступного мероприятия с приростом по этому навыку." if ru else
                      "No currently eligible activity improves this skill.") if not available else ""))
    for growth in event.develops_skills:
        gain = candidate.possible_skill_gains[growth.skill_id]
        text.append(f"{names[growth.skill_id]}: " +
            (f"реальный прирост +{gain}, предел курса {growth.max_level}." if ru else
             f"actual gain +{gain}, activity cap {growth.max_level}."))
    outcomes = Counter(h.participation.status for h in context.history if h.event.event_id == event.event_id)
    format_outcomes = Counter(h.participation.status for h in context.history if h.event.format == event.format and not h.event.mandatory)
    text.append(("История этого мероприятия: " if ru else "This activity's history: ") +
                (", ".join(f"{k}={v}" for k, v in sorted(outcomes.items())) or ("записей нет" if ru else "no records")) + ".")
    text.append(("История формата " if ru else "History for format ") + event.format + ": " +
                (", ".join(f"{k}={v}" for k, v in sorted(format_outcomes.items())) or ("записей нет" if ru else "no records")) + ".")
    text.append(("Роль, грейд и начальные требования проверены. " if ru else "Role, grade and prerequisites verified. ") +
                f"{event.format}, {event.duration_hours} " + ("ч." if ru else "hours."))
    return " ".join(text)


def ground_result(context, result):
    candidates = {c.event_id: c for c in context.candidates}
    items = []
    for item in result.recommendations:
        candidate = candidates[item.event_id]
        benefit = ", ".join(f"{key} +{value}" for key, value in candidate.possible_skill_gains.items() if value > 0)
        items.append(item.model_copy(update={"explanation": factual_explanation(context, candidate),
            "additional_value": benefit if items else None}))
    # Model-generated hypotheses can contain the same unsupported claims as prose.
    return result.model_copy(update={"recommendations": items, "hypotheses": []})

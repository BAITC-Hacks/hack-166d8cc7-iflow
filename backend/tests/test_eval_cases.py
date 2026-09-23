from evals.course_cases import cases
from app.repositories.dataset import build_snapshot
from app.services.recommendation_context import build_recommendation_context


def test_counterexamples_exercise_distinct_failures(real_bundle, clock):
    for name, bundle, employee_id, expected in cases(real_bundle):
        context = build_recommendation_context(employee_id, build_snapshot(bundle), clock)
        available = {c.event_id for c in context.candidates}
        assert expected in available
        if name == "lowest_skill_trap":
            assert "CHECK_02" in available  # Selection must reason; eligibility alone cannot solve it.
            assert len(context.history) == 3
        if name == "prerequisite_trap":
            assert "CHECK_01" not in available
        if name == "score_65_is_completed":
            assert "CHECK_04" not in available
            assert context.history[0].participation.source.score == 65

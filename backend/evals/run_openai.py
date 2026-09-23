"""Explicit, bounded live evaluation. Never launches workers or sends email."""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ai.openai_provider import create_recommender
from app.core.config import Settings
from app.core.errors import DomainError
from app.repositories.dataset import DatasetRepository, build_snapshot
from app.services.recommendation_engine import recommend
from evals.course_cases import cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Allow up to four paid OpenAI requests")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, help="Evaluation-only timeout override; does not change app defaults")
    parser.add_argument("--case", choices=["all", "symbat", "lowest_skill_trap", "prerequisite_trap", "score_65_is_completed"], default="all")
    args = parser.parse_args()
    if not args.live: parser.error("Use --live to explicitly enable paid calls")
    settings = Settings.from_env()
    if args.timeout is not None:
        if not 1 <= args.timeout <= 120: parser.error("timeout must be between 1 and 120 seconds")
        settings = settings.model_copy(update={"ai_timeout_seconds": args.timeout})
    if settings.ai_provider != "openai" or not settings.openai_api_key:
        parser.error("Configure AI_PROVIDER=openai and OPENAI_API_KEY in the root .env")
    source = DatasetRepository(settings.raw_dir).load()
    scenarios = list(cases(source)) + [("symbat", source, "E0047", None)]
    provider = create_recommender(settings)
    records = []
    try:
        for name, bundle, employee_id, expected in scenarios:
            if args.case != "all" and name != args.case: continue
            start = time.perf_counter()
            record = {"case": name, "employee_id": employee_id, "expected_first_event": expected}
            try:
                result = recommend(employee_id, build_snapshot(bundle), bundle.meta.as_of_date, provider)
                chosen = [item.event_id for item in result.recommendations]
                record.update(status=result.status, selected_events=chosen,
                    expected_choice_passed=(bool(chosen) and chosen[0] == expected) if expected else None,
                    result=result.model_dump(mode="json"), usage=provider.last_usage)
            except DomainError as error:
                record.update(status="error", error=error.message, details=error.details)
            record["seconds"] = round(time.perf_counter() - start, 2)
            records.append(record)
            print(json.dumps({k: v for k, v in record.items() if k != "result"}, ensure_ascii=True), flush=True)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({"model": settings.openai_model, "timeout_seconds": settings.ai_timeout_seconds,
                "note": "Synthetic local counterexamples; not jury profiles. Expected-ID checks do not evaluate every claim in prose.",
                "cases": records}, ensure_ascii=False, indent=2), encoding="utf-8")
            if record.get("details") and record["details"][0].get("reason") in {"ai_auth", "ai_permission", "ai_quota", "ai_configuration"}:
                break
    finally:
        provider.close()


if __name__ == "__main__": main()

"""OpenAI Responses adapter. Evidence is selected by reference, never rewritten."""
import hashlib
import json
import time
from typing import Literal

from openai import OpenAI, APIConnectionError, APIStatusError, APITimeoutError
from pydantic import Field

from app.core.errors import DomainError
from app.schemas.common import Model
from app.schemas.recommendation import RecommendationItem, RecommendationResult
from .client import AIRefinementInput
from .prompts import SYSTEM_INSTRUCTIONS
from .recommender import DisabledRecommender, validate_recommendation_result


class WireItem(Model):
    event_id: str
    confidence: Literal["high", "uncertain"]
    additional_value: str | None
    evidence_ids: list[str] = Field(min_length=3, max_length=8)


class WireResult(Model):
    status: Literal["success", "no_candidates", "needs_clarification"]
    recommendations: list[WireItem] = Field(max_length=3)
    clarifying_questions: list[str] = Field(max_length=2)


def request_payload(context):
    # Strict structured output disallows arbitrary object keys in factor.values.
    # Assign immutable IDs to the existing facts; resolve them locally afterward.
    evidence, by_content = {}, {}
    def reference(factor):
        content = json.dumps(factor.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        if content not in by_content:
            key = f"F{len(evidence) + 1}"
            by_content[content] = key
            evidence[key] = factor
        return by_content[content]
    payload = context.model_dump(mode="json")
    payload["facts"] = [reference(f) for f in context.facts]
    for candidate, original in zip(payload["candidates"], context.candidates):
        candidate["factors"] = [reference(f) for f in original.factors]
    payload["evidence_index"] = {key: value.model_dump(mode="json") for key, value in evidence.items()}
    instructions = SYSTEM_INSTRUCTIONS.replace(
        "For each recommendation copy exact evidence objects from that candidate's factors\nor context.facts, using at least three distinct kinds and including the candidate's\nskill_levels, critical_skill or attainable_gain evidence. Hypothesis evidence must\nalso be copied from supplied facts/factors. Preserve employee_id, revision, as_of_date.",
        "Return evidence_ids from the candidate's factors or context.facts, resolved via evidence_index. "
        "Cite at least three distinct factor kinds and include this candidate's skill_levels, critical_skill or attainable_gain. "
        "For hypotheses cite existing evidence_ids too. Do not invent or rewrite facts. "
        "Employee identity, revision and date are preserved by the server.")
    instructions += "\nTransport contract: return only fields in the supplied schema. Do not generate explanations or hypotheses. " \
        "The server renders user-facing explanations from verified facts. Focus on multi-factor selection and evidence_ids. " \
        "Keep additional_value for extra choices under 15 words; primary null. Questions only when clarification changes the choice."
    return [{"role": "system", "content": instructions},
            {"role": "user", "content": json.dumps({"context": payload}, ensure_ascii=False)}], evidence


def provider_error(reason, message):
    return DomainError("unavailable", message, [{"reason": reason}])


class OpenAIRecommender:
    def __init__(self, settings, client=None):
        self.model = settings.openai_model
        self.max_output_tokens = settings.ai_max_output_tokens
        self.timeout_seconds = settings.ai_timeout_seconds
        self.client = client or OpenAI(api_key=settings.openai_api_key.get_secret_value(),
            base_url="https://api.openai.com/v1", timeout=settings.ai_timeout_seconds, max_retries=0)
        self.cache_key = "openai:" + self.model + ":selection-v3:" + hashlib.sha256(SYSTEM_INSTRUCTIONS.encode()).hexdigest()[:16]
        self.last_usage = None

    def close(self):
        self.client.close()

    def _request(self, messages):
        # One recovery attempt for stalled transport, sharing the original budget.
        # Selection has no external side effects; authentication/quota errors do not retry.
        deadline = time.monotonic() + self.timeout_seconds
        for attempt in range(2):
            budget = max(0.1, min(self.timeout_seconds / 2, deadline - time.monotonic()))
            try:
                return self.client.with_options(timeout=budget).responses.parse(
                    model=self.model, input=messages, text_format=WireResult,
                    max_output_tokens=self.max_output_tokens, store=False)
            except APITimeoutError:
                if attempt or deadline - time.monotonic() < 0.1:
                    raise

    def refine(self, context: AIRefinementInput) -> RecommendationResult:
        messages, evidence = request_payload(context)
        self.last_usage = None
        try:
            response = self._request(messages)
        except APITimeoutError:
            raise provider_error("ai_timeout", "AI не успел ответить. Попробуйте позже.") from None
        except APIConnectionError:
            raise provider_error("ai_connection", "Не удалось подключиться к AI-провайдеру.") from None
        except APIStatusError as error:
            if error.status_code == 401:
                reason, message = "ai_auth", "OpenAI отклонил ключ. Проверьте OPENAI_API_KEY на сервере."
            elif error.status_code == 403:
                reason, message = "ai_permission", "Ключу OpenAI недоступны модель или Responses API. Проверьте права проекта."
            elif error.status_code == 429:
                quota = error.code in {"insufficient_quota", "billing_hard_limit_reached"}
                reason, message = ("ai_quota", "Недостаточно квоты OpenAI API. Проверьте баланс и лимиты проекта.") if quota else ("ai_rate_limit", "Достигнут лимит запросов OpenAI. Попробуйте позже.")
            elif error.status_code in {400, 404}:
                reason, message = "ai_configuration", "OpenAI отклонил настройки модели или формат запроса."
            else:
                reason, message = "ai_provider", "AI-провайдер временно недоступен."
            raise provider_error(reason, message) from None
        except Exception:
            raise provider_error("ai_invalid_output", "Не удалось получить корректный ответ AI.") from None
        usage = getattr(response, "usage", None)
        if usage:
            self.last_usage = {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}
        if response.status != "completed" or response.output_parsed is None:
            raise provider_error("ai_incomplete", "AI не завершил подбор или отказался отвечать. Рекомендации не сохранены.")
        try:
            result = response.output_parsed
            candidates = {c.event_id: c for c in context.candidates}
            recommendations = []
            for item in result.recommendations:
                candidate = candidates[item.event_id]  # Unknown events still fail closed.
                supported = candidate.factors + context.facts
                selected = [evidence[key] for key in item.evidence_ids if key in evidence and evidence[key] in supported]
                if len({f.kind for f in selected}) < 3 or not any(f.kind in {"skill_levels", "critical_skill", "attainable_gain"} for f in selected):
                    selected = candidate.factors
                recommendations.append(RecommendationItem(event_id=item.event_id, explanation="Pending verified explanation",
                    confidence=item.confidence, additional_value=item.additional_value, evidence=selected))
            hypotheses = []
            return validate_recommendation_result(context, RecommendationResult(status=result.status,
                employee_id=context.employee_id, revision=context.revision, as_of_date=context.as_of_date,
                recommendations=recommendations, hypotheses=hypotheses, clarifying_questions=result.clarifying_questions))
        except (KeyError, ValueError, TypeError):
            raise provider_error("ai_unsupported_evidence", "Ответ AI не прошёл проверку фактов. Рекомендации не сохранены.") from None


class MissingKeyRecommender(DisabledRecommender):
    def refine(self, context):
        raise DomainError("recommendations_not_implemented", "Для OpenAI не задан OPENAI_API_KEY на сервере.")


def create_recommender(settings):
    if settings.ai_provider == "none":
        return DisabledRecommender()
    if not settings.openai_api_key:
        return MissingKeyRecommender()
    return OpenAIRecommender(settings)

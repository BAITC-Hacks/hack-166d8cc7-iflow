"""OpenAI Responses adapter. Evidence is selected by reference, never rewritten."""
import hashlib
import json
from typing import Literal

from openai import OpenAI, APIConnectionError, APIStatusError, APITimeoutError
from pydantic import Field

from app.core.errors import DomainError
from app.schemas.common import Model
from app.schemas.recommendation import RecommendationItem, RecommendationHypothesis, RecommendationResult
from .client import AIRefinementInput
from .prompts import SYSTEM_INSTRUCTIONS
from .recommender import DisabledRecommender, validate_recommendation_result


class WireItem(Model):
    event_id: str
    explanation: str
    confidence: Literal["high", "uncertain"]
    additional_value: str | None
    evidence_ids: list[str] = Field(min_length=3, max_length=8)


class WireHypothesis(Model):
    statement: str
    evidence_ids: list[str] = Field(min_length=1, max_length=5)


class WireResult(Model):
    status: Literal["success", "no_candidates", "needs_clarification"]
    recommendations: list[WireItem] = Field(max_length=3)
    hypotheses: list[WireHypothesis] = Field(max_length=3)
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
        "Employee identity, revision and date are preserved by the server. Keep explanations concise (2-4 sentences).")
    return [{"role": "system", "content": instructions},
            {"role": "user", "content": json.dumps({"context": payload}, ensure_ascii=False)}], evidence


def provider_error(reason, message):
    return DomainError("unavailable", message, [{"reason": reason}])


class OpenAIRecommender:
    def __init__(self, settings, client=None):
        self.model = settings.openai_model
        self.max_output_tokens = settings.ai_max_output_tokens
        self.client = client or OpenAI(api_key=settings.openai_api_key.get_secret_value(),
            base_url="https://api.openai.com/v1", timeout=settings.ai_timeout_seconds, max_retries=0)
        self.cache_key = "openai:" + self.model + ":refs-v1:" + hashlib.sha256(SYSTEM_INSTRUCTIONS.encode()).hexdigest()[:16]
        self.last_usage = None

    def close(self):
        self.client.close()

    def refine(self, context: AIRefinementInput) -> RecommendationResult:
        messages, evidence = request_payload(context)
        self.last_usage = None
        try:
            response = self.client.responses.parse(model=self.model, input=messages, text_format=WireResult,
                max_output_tokens=self.max_output_tokens, store=False)
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
            recommendations = [RecommendationItem(event_id=item.event_id, explanation=item.explanation,
                confidence=item.confidence, additional_value=item.additional_value,
                evidence=[evidence[key] for key in item.evidence_ids]) for item in result.recommendations]
            hypotheses = [RecommendationHypothesis(statement=item.statement,
                evidence=[evidence[key] for key in item.evidence_ids]) for item in result.hypotheses]
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

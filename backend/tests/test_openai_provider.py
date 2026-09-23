import json
from types import SimpleNamespace

import httpx
import pytest
from openai import OpenAI

from app.ai.openai_provider import OpenAIRecommender, WireResult, create_recommender, request_payload
from app.ai.recommender import DisabledRecommender
from app.core.config import Settings
from app.core.errors import DomainError
from app.repositories.dataset import build_snapshot
from app.services.recommendation_context import build_recommendation_context


@pytest.fixture
def context(tiny_bundle, clock):
    return build_recommendation_context("TEST_EMP", build_snapshot(tiny_bundle), clock)


def wire_result(context):
    _, facts = request_payload(context)
    candidate = context.candidates[0]
    return {"status": "success", "recommendations": [{"event_id": candidate.event_id,
        "confidence": "high", "additional_value": None,
        "evidence_ids": [next(key for key, value in facts.items() if value == factor)
                         for factor in candidate.factors[:8]]}],
        "clarifying_questions": []}


def mock_sdk(handler):
    return OpenAI(api_key="test-secret", base_url="https://api.openai.com/v1", max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def response_envelope(value):
    return {"id": "resp_test", "object": "response", "created_at": 1, "status": "completed",
        "model": "gpt-4.1-mini", "output": [{"id": "msg_test", "type": "message", "role": "assistant",
        "status": "completed", "content": [{"type": "output_text", "text": json.dumps(value), "annotations": []}]}],
        "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}}


def test_sdk_strict_output_and_exact_fact_resolution(context):
    calls = []
    def handle(request):
        body = json.loads(request.content); calls.append(body)
        assert request.url.path == "/v1/responses"
        assert body["store"] is False and body["text"]["format"]["strict"] is True
        assert body["max_output_tokens"] == 1400
        schema = body["text"]["format"]["schema"]
        assert schema["additionalProperties"] is False
        assert schema["$defs"]["WireItem"]["additionalProperties"] is False
        return httpx.Response(200, json=response_envelope(wire_result(context)))
    client = mock_sdk(handle)
    provider = OpenAIRecommender(Settings(), client)
    result = provider.refine(context)
    assert result.employee_id == context.employee_id and result.revision == context.revision
    assert result.recommendations[0].evidence == context.candidates[0].factors[:8]
    assert len(calls) == 1
    assert provider.last_usage == {"input_tokens": 100, "output_tokens": 50}
    provider.close()


@pytest.mark.parametrize("status,code,reason", [(401, "invalid_api_key", "ai_auth"),
    (403, "permission_denied", "ai_permission"), (429, "insufficient_quota", "ai_quota"),
    (429, "rate_limit_exceeded", "ai_rate_limit"), (500, "server_error", "ai_provider")])
def test_provider_errors_are_sanitized_and_not_retried(context, status, code, reason):
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(status, json={"error": {"message": "test-secret-private", "code": code, "type": "error"}})
    provider = OpenAIRecommender(Settings(), mock_sdk(handle))
    with pytest.raises(DomainError) as caught: provider.refine(context)
    assert caught.value.details == [{"reason": reason}]
    assert "test-secret" not in str(caught.value)
    assert len(calls) == 1
    provider.close()


def test_timeout_and_refusal_do_not_create_a_recommendation(context):
    def timeout(request): raise httpx.ReadTimeout("test-secret-private", request=request)
    provider = OpenAIRecommender(Settings(), mock_sdk(timeout))
    with pytest.raises(DomainError) as caught: provider.refine(context)
    assert caught.value.details == [{"reason": "ai_timeout"}]
    provider.close()


def test_one_timeout_can_recover_without_replacing_llm_selection(context):
    calls=[]
    def handle(request):
        calls.append(request)
        if len(calls)==1:
            raise httpx.ReadTimeout("stalled",request=request)
        return httpx.Response(200,json=response_envelope(wire_result(context)))
    provider=OpenAIRecommender(Settings(),mock_sdk(handle))
    assert provider.refine(context).status=='success'
    assert len(calls)==2
    provider.close()
    envelope = response_envelope(wire_result(context))
    envelope["output"][0]["content"] = [{"type": "refusal", "refusal": "Cannot answer"}]
    provider = OpenAIRecommender(Settings(), mock_sdk(lambda _: httpx.Response(200, json=envelope)))
    with pytest.raises(DomainError) as caught: provider.refine(context)
    assert caught.value.details == [{"reason": "ai_incomplete"}]
    provider.close()


def test_unknown_fact_id_cannot_break_valid_course_or_leak_prose(context):
    value = wire_result(context); value["recommendations"][0]["evidence_ids"][0] = "invented"
    provider = OpenAIRecommender(Settings(), mock_sdk(lambda _: httpx.Response(200, json=response_envelope(value))))
    result = provider.refine(context)
    assert result.status == "success"
    assert all(f in context.candidates[0].factors + context.facts for f in result.recommendations[0].evidence)
    provider.close()


def test_dotenv_loading_process_precedence_and_secret_masking(tmp_path, monkeypatch):
    file = tmp_path / ".env"
    file.write_text("AI_PROVIDER=openai\nOPENAI_API_KEY=file-secret\nNVIDIA_API_KEY=unused-secret\nOPENAI_MODEL=model-a\nAI_AUTO_PREPARE=false\n", encoding="utf-8-sig")
    for name in ("OPENAI_API_KEY", "OPENAI_MODEL", "AI_AUTO_PREPARE", "AI_PROVIDER"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "model-b")
    settings = Settings.from_env(file)
    assert settings.openai_api_key.get_secret_value() == "file-secret"
    assert settings.openai_model == "model-b" and not settings.ai_auto_prepare
    assert "file-secret" not in repr(settings) and "file-secret" not in settings.model_dump_json()
    assert isinstance(create_recommender(Settings()), DisabledRecommender)
    assert isinstance(create_recommender(Settings(ai_provider="openai")), DisabledRecommender)


def test_model_switch_changes_recommendation_cache_identity():
    dummy = SimpleNamespace()
    first = OpenAIRecommender(Settings(openai_model="model-a"), dummy)
    second = OpenAIRecommender(Settings(openai_model="model-b"), dummy)
    assert first.cache_key != second.cache_key

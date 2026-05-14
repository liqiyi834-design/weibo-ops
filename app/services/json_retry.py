from __future__ import annotations

from typing import Any

from app.llm.client import BaseLLMClient, LLMClientError


def complete_json_with_retry(
    llm: BaseLLMClient,
    system_prompt: str,
    user_prompt: str,
    required_fields: list[str],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    data = _safe_generate(llm, system_prompt, user_prompt)
    if _has_required_fields(data, required_fields):
        return {**defaults, **data}

    missing = [field for field in required_fields if not data.get(field)]
    retry_prompt = (
        f"{user_prompt}\n\n"
        "The previous response was missing required fields and failed validation.\n"
        f"Missing fields: {', '.join(missing)}\n"
        "Return only one complete JSON object. Do not explain. Do not use Markdown."
    )
    retry_data = _safe_generate(llm, system_prompt, retry_prompt)
    if _has_required_fields(retry_data, required_fields):
        return {**defaults, **retry_data}

    return {**defaults, **retry_data} if isinstance(retry_data, dict) else defaults


def _safe_generate(llm: BaseLLMClient, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    try:
        data = llm.generate_json(system_prompt, user_prompt)
    except LLMClientError:
        return {}
    return data if isinstance(data, dict) else {}


def _has_required_fields(data: dict[str, Any], required_fields: list[str]) -> bool:
    return all(bool(data.get(field)) for field in required_fields)

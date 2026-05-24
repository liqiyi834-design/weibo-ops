from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.llm.client import BaseLLMClient
from app.schemas.comment import (
    StyleMemoryExtractRequest,
    StyleMemoryExtractResponse,
    StyleMemoryIngestRequest,
    StyleMemoryIngestResponse,
    StyleMemoryObservation,
)
from app.services.json_retry import complete_json_with_retry
from app.services.knowledge_service import KnowledgeService


class StyleMemoryService:
    def __init__(self, settings: Settings, llm: BaseLLMClient | None = None):
        self.settings = settings
        self.llm = llm
        self.memory_dir = Path(settings.knowledge_dir) / "style_memory"

    def extract(self, request: StyleMemoryExtractRequest) -> StyleMemoryExtractResponse:
        observation = self._extract_with_llm(request) if self.llm else self._extract_fallback(request)
        ingested = None
        if request.auto_ingest:
            ingested = self.ingest(
                StyleMemoryIngestRequest(
                    observation=observation,
                    operator_note=request.operator_note,
                    rebuild_index=request.rebuild_index,
                )
            )
        return StyleMemoryExtractResponse(observation=observation, ingested=ingested)

    def ingest(self, request: StyleMemoryIngestRequest) -> StyleMemoryIngestResponse:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        path = self._next_path(request.observation)
        path.write_text(self._render_markdown(request), encoding="utf-8")
        rebuild_stats = None
        if request.rebuild_index:
            rebuild_stats = KnowledgeService(self.settings).rebuild()
        return StyleMemoryIngestResponse(path=str(path), observation=request.observation, rebuild_stats=rebuild_stats)

    def list_cards(self, limit: int = 50) -> list[dict]:
        if not self.memory_dir.exists():
            return []
        cards = []
        for path in sorted(self.memory_dir.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True):
            cards.append({"id": path.stem, "path": str(path), "preview": _preview(path.read_text(encoding="utf-8"))})
        return cards[:limit]

    def _extract_with_llm(self, request: StyleMemoryExtractRequest) -> StyleMemoryObservation:
        assert self.llm is not None
        data = complete_json_with_retry(
            llm=self.llm,
            system_prompt="You extract reusable writing style observations. Return JSON only.",
            user_prompt=_style_memory_prompt(request),
            required_fields=["hook_patterns", "sentence_rhythm", "argument_structure", "reusable_rules"],
            defaults=_fallback_data(request.source_text),
        )
        return _observation_from_data(request, data)

    def _extract_fallback(self, request: StyleMemoryExtractRequest) -> StyleMemoryObservation:
        return _observation_from_data(request, _fallback_data(request.source_text))

    def _next_path(self, observation: StyleMemoryObservation) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        slug = _slugify(f"{observation.account_id}-{observation.style_name}-{observation.creator_name or 'style'}")
        return self.memory_dir / f"{stamp}-{slug}-{uuid4().hex[:8]}.md"

    def _render_markdown(self, request: StyleMemoryIngestRequest) -> str:
        observation = request.observation
        created_at = datetime.now(timezone.utc).isoformat()
        return "\n".join(
            [
                "---",
                "memory_type: style_memory",
                f"creator_name: {observation.creator_name}",
                f"platform: {observation.platform}",
                f"account_id: {observation.account_id}",
                f"style_name: {observation.style_name}",
                f"source_url: {observation.source_url or ''}",
                f"permission_level: {observation.permission_level}",
                f"needs_review: {str(observation.needs_review).lower()}",
                f"created_at: {created_at}",
                "---",
                "",
                f"# 风格记忆库：{observation.creator_name or observation.style_name}",
                "",
                "## Scope",
                "",
                f"- Account: {observation.account_id}",
                f"- Style: {observation.style_name}",
                f"- Platform: {observation.platform}",
                f"- Permission: {observation.permission_level}",
                "",
                "## Hook Patterns",
                *[f"- {item}" for item in observation.hook_patterns],
                "",
                "## Sentence Rhythm",
                "",
                observation.sentence_rhythm,
                "",
                "## Argument Structure",
                *[f"- {item}" for item in observation.argument_structure],
                "",
                "## Rhetorical Devices",
                *[f"- {item}" for item in observation.rhetorical_devices],
                "",
                "## Reusable Rules",
                *[f"- {item}" for item in observation.reusable_rules],
                "",
                "## Avoid Points",
                *[f"- {item}" for item in observation.avoid_points],
                "",
                "## Example Lines",
                *[f"- {item}" for item in observation.example_lines],
                "",
                "## Operator Note",
                "",
                request.operator_note or "",
                "",
            ]
        )


def _style_memory_prompt(request: StyleMemoryExtractRequest) -> str:
    return (
        "StyleMemorySchema\n"
        "Extract reusable writing style observations from the source text. Do not copy long original passages.\n"
        "Return JSON with keys: hook_patterns, sentence_rhythm, argument_structure, rhetorical_devices, "
        "emotion_level, suitable_topics, avoid_points, reusable_rules, example_lines.\n"
        f"creator_name: {request.creator_name}\n"
        f"platform: {request.platform}\n"
        f"account_id: {request.account_id}\n"
        f"style_name: {request.style_name}\n"
        f"permission_level: {request.permission_level}\n"
        f"source_text:\n{request.source_text[:6000]}"
    )


def _observation_from_data(request: StyleMemoryExtractRequest, data: dict) -> StyleMemoryObservation:
    return StyleMemoryObservation(
        creator_name=request.creator_name,
        platform=request.platform,
        account_id=request.account_id,
        style_name=request.style_name,
        hook_patterns=_string_list(data.get("hook_patterns")),
        sentence_rhythm=str(data.get("sentence_rhythm") or ""),
        argument_structure=_string_list(data.get("argument_structure")),
        rhetorical_devices=_string_list(data.get("rhetorical_devices")),
        emotion_level=_emotion_level(data.get("emotion_level")),
        suitable_topics=_string_list(data.get("suitable_topics")),
        avoid_points=_string_list(data.get("avoid_points")),
        reusable_rules=_string_list(data.get("reusable_rules")),
        example_lines=_short_examples(data.get("example_lines")),
        source_url=request.source_url,
        permission_level=request.permission_level,
        needs_review=True,
    )


def _fallback_data(source_text: str) -> dict:
    sentences = re.split(r"[。！？!?；;\n]+", source_text)
    examples = [item.strip() for item in sentences if item.strip()][:3]
    return {
        "hook_patterns": ["从明确判断或反差观察切入。"],
        "sentence_rhythm": "短句和中句混合，先给判断，再补边界。",
        "argument_structure": ["开头判断", "补充事实或观察", "解释冲突", "收束到可讨论观点"],
        "rhetorical_devices": ["反差", "设问"],
        "emotion_level": 5,
        "suitable_topics": ["热点评论", "公共表达"],
        "avoid_points": ["不照搬原文", "不扩散未核验信息"],
        "reusable_rules": ["提炼写法，不复制具体措辞。"],
        "example_lines": examples,
    }


def _string_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _short_examples(value) -> list[str]:
    return [item[:80] for item in _string_list(value)[:5]]


def _emotion_level(value) -> int:
    try:
        return max(1, min(10, int(value)))
    except (TypeError, ValueError):
        return 5


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text, flags=re.UNICODE).strip("-")
    return (slug or "style-memory")[:60]


def _preview(text: str, length: int = 160) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= length else compact[: length - 1] + "..."

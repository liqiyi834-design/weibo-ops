from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.llm.client import BaseLLMClient
from app.schemas.comment import KnowledgeIngestRequest
from app.schemas.feedback import (
    DraftFeedbackRecord,
    DraftFeedbackRequest,
    DraftFeedbackResponse,
    FeedbackMemoryDraft,
    FeedbackMemorySummarizeRequest,
    FeedbackMemorySummarizeResponse,
)
from app.services.knowledge_ingestion_service import KnowledgeIngestionService


class DraftFeedbackService:
    def __init__(
        self,
        path: Path | str = Path("output/draft_feedback/feedback.jsonl"),
        settings: Settings | None = None,
        llm: BaseLLMClient | None = None,
    ):
        self.path = Path(path)
        self.settings = settings
        self.llm = llm

    def record(self, request: DraftFeedbackRequest) -> DraftFeedbackResponse:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        record = DraftFeedbackRecord(
            **request.model_dump(),
            id=f"{now.strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}",
            created_at=now,
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json(ensure_ascii=False) + "\n")
        return DraftFeedbackResponse(record=record, path=str(self.path))

    def list_records(self, limit: int = 50) -> list[DraftFeedbackRecord]:
        if not self.path.exists():
            return []
        rows: list[DraftFeedbackRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(DraftFeedbackRecord(**json.loads(line)))
        return list(reversed(rows[-limit:]))

    def summarize_memory(self, request: FeedbackMemorySummarizeRequest) -> FeedbackMemorySummarizeResponse:
        records = self._filtered_records(request)
        draft = self._summarize_with_llm(records, request) if request.use_llm and self.llm else _fallback_draft(
            records, request
        )
        ingested = None
        if request.auto_ingest:
            if self.settings is None:
                raise ValueError("settings is required when auto_ingest is true")
            ingested = KnowledgeIngestionService(self.settings).ingest(
                KnowledgeIngestRequest(
                    topic=draft.title,
                    content=draft.markdown,
                    source_title="草稿反馈提炼",
                    credibility="medium",
                    needs_review=True,
                    operator_note=request.operator_note or "从 draft_feedback.jsonl 提炼的待审核长期记忆草案。",
                    rebuild_index=request.rebuild_index,
                )
            )
        return FeedbackMemorySummarizeResponse(draft=draft, ingested=ingested)

    def _filtered_records(self, request: FeedbackMemorySummarizeRequest) -> list[DraftFeedbackRecord]:
        records = self.list_records(limit=max(request.limit, 1) * 3)
        if request.account_id:
            records = [item for item in records if item.account_id == request.account_id]
        if request.status:
            records = [item for item in records if item.status == request.status]
        return records[: request.limit]

    def _summarize_with_llm(
        self, records: list[DraftFeedbackRecord], request: FeedbackMemorySummarizeRequest
    ) -> FeedbackMemoryDraft:
        assert self.llm is not None
        data = self.llm.generate_json(
            system_prompt="You summarize draft review feedback into reusable editorial memory. Return JSON only.",
            user_prompt=_feedback_memory_prompt(records, request),
        )
        return _draft_from_data(records, request, data)


def _fallback_draft(
    records: list[DraftFeedbackRecord], request: FeedbackMemorySummarizeRequest
) -> FeedbackMemoryDraft:
    data = {
        "keep_patterns": _comments_for(records, {"keep", "good_angle"}),
        "rewrite_patterns": _comments_for(records, {"rewrite", "too_ai", "too_hard", "too_soft", "wrong_angle"}),
        "discard_patterns": _comments_for(records, {"discard"}),
        "style_rules": _rules_from_actions(records),
        "judgment_rules": _judgment_rules(records),
        "avoid_points": _avoid_points(records),
        "fact_check_rules": _comments_for(records, {"needs_fact_check"}),
        "example_feedback": [item.comment for item in records[:8]],
    }
    return _draft_from_data(records, request, data)


def _draft_from_data(
    records: list[DraftFeedbackRecord], request: FeedbackMemorySummarizeRequest, data: dict
) -> FeedbackMemoryDraft:
    title = f"草稿反馈提炼：{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    draft = FeedbackMemoryDraft(
        title=title,
        account_id=request.account_id or "all",
        source_count=len(records),
        keep_patterns=_string_list(data.get("keep_patterns")),
        rewrite_patterns=_string_list(data.get("rewrite_patterns")),
        discard_patterns=_string_list(data.get("discard_patterns")),
        style_rules=_string_list(data.get("style_rules")),
        judgment_rules=_string_list(data.get("judgment_rules")),
        avoid_points=_string_list(data.get("avoid_points")),
        fact_check_rules=_string_list(data.get("fact_check_rules")),
        example_feedback=_string_list(data.get("example_feedback"))[:8],
    )
    draft.markdown = _render_memory_markdown(draft)
    return draft


def _render_memory_markdown(draft: FeedbackMemoryDraft) -> str:
    return "\n".join(
        [
            f"# {draft.title}",
            "",
            "## Scope",
            "",
            f"- Account: {draft.account_id}",
            f"- Source feedback count: {draft.source_count}",
            "- Status: pending human review",
            "",
            "## Keep Patterns",
            *_bullets(draft.keep_patterns),
            "",
            "## Rewrite Patterns",
            *_bullets(draft.rewrite_patterns),
            "",
            "## Discard Patterns",
            *_bullets(draft.discard_patterns),
            "",
            "## Style Rules",
            *_bullets(draft.style_rules),
            "",
            "## Judgment Rules",
            *_bullets(draft.judgment_rules),
            "",
            "## Avoid Points",
            *_bullets(draft.avoid_points),
            "",
            "## Fact Check Rules",
            *_bullets(draft.fact_check_rules),
            "",
            "## Example Feedback",
            *_bullets(draft.example_feedback),
            "",
        ]
    )


def _feedback_memory_prompt(records: list[DraftFeedbackRecord], request: FeedbackMemorySummarizeRequest) -> str:
    lines = [
        "FeedbackMemorySchema",
        "Summarize raw draft feedback into durable editorial rules. Do not copy long text.",
        "Return JSON with keys: keep_patterns, rewrite_patterns, discard_patterns, style_rules, "
        "judgment_rules, avoid_points, fact_check_rules, example_feedback.",
        f"account_id: {request.account_id or 'all'}",
        "raw_feedback:",
    ]
    for item in records[:80]:
        lines.append(
            json.dumps(
                {
                    "topic": item.topic,
                    "draft_id": item.draft_id,
                    "action": item.action,
                    "comment": item.comment,
                    "style": item.style,
                    "created_at": item.created_at.isoformat(),
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(lines)


def _comments_for(records: list[DraftFeedbackRecord], actions: set[str]) -> list[str]:
    return [f"{item.topic or item.draft_id or '未命名草稿'}：{item.comment}" for item in records if item.action in actions][
        :8
    ]


def _rules_from_actions(records: list[DraftFeedbackRecord]) -> list[str]:
    rules = []
    actions = {item.action for item in records}
    if "too_ai" in actions:
        rules.append("避免总结腔和模板化结论，增加具体判断、人的犹豫或观察细节。")
    if "too_hard" in actions:
        rules.append("语气过硬时降低定性强度，先写边界和依据，再给判断。")
    if "too_soft" in actions:
        rules.append("表达过软时补足明确立场，但仍避免攻击个人。")
    if "wrong_angle" in actions:
        rules.append("角度被判定跑偏时，回到用户反馈里的核心冲突重新组织。")
    return rules


def _judgment_rules(records: list[DraftFeedbackRecord]) -> list[str]:
    rules = []
    if any(item.action == "discard" or "商业" in item.comment for item in records):
        rules.append("商业推广类话题默认降权，除非存在规则不透明、消费者权益或公共讨论价值。")
    if any(item.action == "good_angle" for item in records):
        rules.append("被标记为角度对的草稿，应保留其核心判断框架，再调整语气和句式。")
    return rules


def _avoid_points(records: list[DraftFeedbackRecord]) -> list[str]:
    points = []
    if any("AI" in item.comment or item.action == "too_ai" for item in records):
        points.append("避免像报告摘要一样复述背景，减少“首先/其次/综上”式结构。")
    if any("太硬" in item.comment or item.action == "too_hard" for item in records):
        points.append("事实未核清时，不要用满格判断和绝对化措辞。")
    if any("商业" in item.comment for item in records):
        points.append("避免把商业促销话题写成广告或替平台做传播。")
    return points


def _string_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- 暂无"]

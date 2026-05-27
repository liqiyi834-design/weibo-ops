from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.comment import KnowledgeIngestResponse


DraftFeedbackAction = Literal[
    "keep",
    "rewrite",
    "discard",
    "style_note",
    "too_ai",
    "too_hard",
    "too_soft",
    "wrong_angle",
    "good_angle",
    "needs_fact_check",
]

DraftFeedbackSource = Literal["telegram", "hermes", "streamlit", "api", "manual"]


class DraftFeedbackRequest(BaseModel):
    topic: str | None = None
    draft_id: str | None = None
    action: DraftFeedbackAction = "style_note"
    comment: str = Field(min_length=1)
    source: DraftFeedbackSource = "hermes"
    account_id: str = "today_direct"
    style: str | None = None
    message_ref: str | None = None
    reviewer: str | None = None
    should_extract_style_memory: bool = False
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_topic_or_draft_id(self) -> "DraftFeedbackRequest":
        if not self.topic and not self.draft_id:
            raise ValueError("topic or draft_id is required")
        return self


class DraftFeedbackRecord(DraftFeedbackRequest):
    id: str
    created_at: datetime
    status: Literal["pending_review", "reviewed", "ignored"] = "pending_review"


class DraftFeedbackResponse(BaseModel):
    success: bool = True
    record: DraftFeedbackRecord
    path: str


class FeedbackMemoryDraft(BaseModel):
    title: str
    account_id: str = "today_direct"
    source_count: int = 0
    keep_patterns: list[str] = Field(default_factory=list)
    rewrite_patterns: list[str] = Field(default_factory=list)
    discard_patterns: list[str] = Field(default_factory=list)
    style_rules: list[str] = Field(default_factory=list)
    judgment_rules: list[str] = Field(default_factory=list)
    avoid_points: list[str] = Field(default_factory=list)
    fact_check_rules: list[str] = Field(default_factory=list)
    example_feedback: list[str] = Field(default_factory=list)
    markdown: str = ""


class FeedbackMemorySummarizeRequest(BaseModel):
    limit: int = Field(default=30, ge=1, le=200)
    account_id: str | None = "today_direct"
    status: Literal["pending_review", "reviewed", "ignored"] | None = "pending_review"
    use_llm: bool = False
    auto_ingest: bool = False
    rebuild_index: bool = True
    operator_note: str | None = None


class FeedbackMemorySummarizeResponse(BaseModel):
    success: bool = True
    draft: FeedbackMemoryDraft
    ingested: KnowledgeIngestResponse | None = None

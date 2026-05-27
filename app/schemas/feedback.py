from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


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

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReviewMessageRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1)
    channel: Literal["telegram"] = "telegram"
    message_type: str = Field(default="workflow_update", max_length=64)
    dedupe_key: str | None = Field(default=None, max_length=160)
    max_chars: int = Field(default=3000, ge=500, le=3800)


class ReviewMessageResponse(BaseModel):
    ok: bool
    channel: str
    configured: bool
    skipped: bool = False
    chunk_count: int = 0
    sent_count: int = 0
    message_ids: list[int] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    dedupe_key: str | None = None

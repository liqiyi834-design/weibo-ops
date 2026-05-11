from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class HotTopic(BaseModel):
    rank: int | None = None
    keyword: str
    hot_value: str | None = None
    url: str | None = None
    source: str = "manual"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FactSummary(BaseModel):
    topic: str
    confirmed_facts: list[str] = Field(default_factory=list)
    controversy_points: list[str] = Field(default_factory=list)
    uncertain_points: list[str] = Field(default_factory=list)
    public_sentiment: str | None = None
    risk_level: Literal["low", "medium", "high"] = "low"


class TopicClassification(BaseModel):
    category: Literal[
        "brand_pr",
        "entertainment",
        "gender_issue",
        "social_issue",
        "crime_case",
        "disaster",
        "minor_related",
        "political_sensitive",
        "unknown",
    ] = "unknown"
    recommended_persona: str = "rational_critic"
    max_emotion_level: int = 7
    risk_notes: list[str] = Field(default_factory=list)


class RetrievedKnowledge(BaseModel):
    content: str
    source: str
    score: float | None = None


class OpinionDraft(BaseModel):
    core_conflict: str
    critique_angles: list[str] = Field(default_factory=list)
    usable_lines: list[str] = Field(default_factory=list)


class CommentOutput(BaseModel):
    one_liner: str
    short_comment: str
    emotional_version: str
    rational_version: str
    ironic_version: str
    comment_replies: list[str] = Field(default_factory=list)


class SafetyResult(BaseModel):
    is_safe: bool
    risk_level: Literal["low", "medium", "high", "blocked"] = "low"
    issues: list[str] = Field(default_factory=list)
    revised_output: CommentOutput | None = None


class GenerateCommentRequest(BaseModel):
    topic: str = Field(min_length=1)
    persona: str = "rational_critic"
    emotion_level: int = Field(default=6, ge=1, le=10)
    use_rag: bool = True
    context_text: str = ""


class GenerateCommentResponse(BaseModel):
    topic: str
    fact_summary: FactSummary
    topic_classification: TopicClassification
    retrieved_knowledge: list[RetrievedKnowledge]
    opinion: OpinionDraft
    output: CommentOutput
    safety: SafetyResult

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class HotTopic(BaseModel):
    rank: int | None = None
    keyword: str
    hot_value: str | None = None
    read_count: int | None = None
    discussion_count: int | None = None
    sampled_posts_count: int | None = None
    controversy_score: float | None = None
    url: str | None = None
    label: str | None = None
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


class KnowledgeIngestRequest(BaseModel):
    topic: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source_url: str | None = None
    source_title: str | None = None
    credibility: Literal["unknown", "low", "medium", "high"] = "unknown"
    needs_review: bool = True
    candidate_pool_id: str | None = None
    candidate_item_id: str | None = None
    operator_note: str | None = None
    rebuild_index: bool = True


class KnowledgeIngestResponse(BaseModel):
    success: bool = True
    topic: str
    path: str
    source_url: str | None = None
    needs_review: bool = True
    rebuild_stats: dict[str, int | bool | str] | None = None


class KnowledgeRecordSummary(BaseModel):
    id: str
    topic: str
    path: str
    source_url: str | None = None
    source_title: str | None = None
    credibility: Literal["unknown", "low", "medium", "high"] = "unknown"
    needs_review: bool = True
    candidate_pool_id: str | None = None
    candidate_item_id: str | None = None
    created_at: datetime | None = None
    preview: str = ""


class KnowledgeRecord(KnowledgeRecordSummary):
    operator_note: str | None = None
    content: str = ""


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
    account_id: str = "today_direct"
    style: str | None = None
    # Backward-compatible alias for older callers. Prefer `style` in new code.
    persona: str | None = None
    emotion_level: int = Field(default=6, ge=1, le=10)
    use_rag: bool = True
    context_text: str = ""


class GenerateCommentResponse(BaseModel):
    topic: str
    account_id: str = "today_direct"
    style: str = "rational_critic"
    fact_summary: FactSummary
    topic_classification: TopicClassification
    retrieved_knowledge: list[RetrievedKnowledge]
    opinion: OpinionDraft
    output: CommentOutput
    safety: SafetyResult


class ZhihuAnswerOutput(BaseModel):
    question_title: str
    answer_title: str
    opening_judgement: str
    background_summary: str
    core_argument: str
    supporting_points: list[str] = Field(default_factory=list)
    counter_arguments: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    answer_body: str
    references: list[str] = Field(default_factory=list)


class GenerateZhihuAnswerRequest(GenerateCommentRequest):
    question_title: str | None = None
    zhihu_domain: str | None = None
    zhihu_domain_context: str | None = None


class GenerateZhihuAnswerResponse(BaseModel):
    topic: str
    account_id: str = "today_direct"
    style: str = "rational_critic"
    zhihu_domain: str | None = None
    fact_summary: FactSummary
    topic_classification: TopicClassification
    retrieved_knowledge: list[RetrievedKnowledge]
    opinion: OpinionDraft
    output: ZhihuAnswerOutput


class TopicSelectionRequest(BaseModel):
    topics: list[HotTopic] = Field(default_factory=list)
    max_results: int = Field(default=5, ge=3, le=10)
    source_limit: int = Field(default=50, ge=1, le=50)
    enrich_metrics: bool = False
    research_limit: int = Field(default=10, ge=1, le=10)


class SelectedTopic(BaseModel):
    rank: int | None = None
    keyword: str
    score: float
    category: str
    risk_level: Literal["low", "medium", "high"] = "low"
    reason: str
    recommended_angle: str
    avoid_points: list[str] = Field(default_factory=list)
    hot_value: str | None = None
    read_count: int | None = None
    discussion_count: int | None = None
    sampled_posts_count: int | None = None
    controversy_score: float | None = None
    label: str | None = None
    url: str | None = None
    source: str = "manual"
    target_platform_scores: dict[str, float] = Field(default_factory=dict)
    recommended_targets: list[str] = Field(default_factory=list)
    zhihu_question_title: str | None = None
    zhihu_answer_angle: str | None = None
    zhihu_required_research: list[str] = Field(default_factory=list)
    zhihu_reason: str | None = None
    zhihu_domain_scores: dict[str, float] = Field(default_factory=dict)
    zhihu_recommended_domain: str | None = None
    zhihu_domain_reason: str | None = None


class TopicResearchMetrics(BaseModel):
    keyword: str
    read_count: int | None = None
    discussion_count: int | None = None
    sampled_posts_count: int = 0
    controversy_score: float | None = None
    source_url: str | None = None
    error: str | None = None


class StyleInfo(BaseModel):
    id: str
    name: str
    description: str = ""
    best_for: list[str] = Field(default_factory=list)


class AccountConfig(BaseModel):
    id: str
    name: str
    positioning: str
    default_style: str = "rational_critic"
    allowed_styles: list[str] = Field(default_factory=lambda: ["rational_critic"])
    blocked_styles_for_high_risk: list[str] = Field(default_factory=list)
    preferred_topics: list[str] = Field(default_factory=list)
    risk_policy: str = "高风险话题必须降温，不自动发布。"


class TopicSelectionResponse(BaseModel):
    source: str
    evaluated_count: int
    selected: list[SelectedTopic]
    notes: list[str] = Field(default_factory=list)


CandidateStatus = Literal["candidate", "selected", "skipped", "researched"]


class CandidatePoolItem(SelectedTopic):
    id: str
    status: CandidateStatus = "candidate"
    operator_note: str | None = None


class CandidatePool(BaseModel):
    id: str
    title: str
    source: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    items: list[CandidatePoolItem]
    notes: list[str] = Field(default_factory=list)


class CandidatePoolCreateRequest(TopicSelectionRequest):
    title: str | None = None


class CandidatePoolSummary(BaseModel):
    id: str
    title: str
    source: str
    created_at: datetime
    item_count: int
    selected_count: int = 0


class CandidateStatusUpdateRequest(BaseModel):
    status: CandidateStatus
    operator_note: str | None = None


DraftStatus = Literal["draft", "reviewed", "rejected", "published_manually"]
DraftType = Literal["micro_comment", "zhihu_answer", "video_script"]
DraftPlatform = Literal["weibo", "zhihu", "video", "other"]


class DraftCreateRequest(GenerateCommentRequest):
    candidate_pool_id: str | None = None
    candidate_item_id: str | None = None
    title: str | None = None
    platform: DraftPlatform = "weibo"
    draft_type: DraftType = "micro_comment"


class ZhihuDraftCreateRequest(GenerateZhihuAnswerRequest):
    candidate_pool_id: str | None = None
    candidate_item_id: str | None = None
    title: str | None = None


class DraftUpdateRequest(BaseModel):
    status: DraftStatus | None = None
    operator_note: str | None = None
    edited_text: str | None = None
    published_url: str | None = None
    published_at: datetime | None = None
    performance_note: str | None = None


class DraftRecord(BaseModel):
    id: str
    title: str
    topic: str
    account_id: str
    style: str
    platform: DraftPlatform = "weibo"
    draft_type: DraftType = "micro_comment"
    status: DraftStatus = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    candidate_pool_id: str | None = None
    candidate_item_id: str | None = None
    risk_level: Literal["low", "medium", "high", "blocked"] = "low"
    generated: GenerateCommentResponse | None = None
    zhihu_answer: GenerateZhihuAnswerResponse | None = None
    edited_text: str | None = None
    operator_note: str | None = None
    published_url: str | None = None
    published_at: datetime | None = None
    performance_note: str | None = None


class DraftSummary(BaseModel):
    id: str
    title: str
    topic: str
    account_id: str
    style: str
    platform: DraftPlatform = "weibo"
    draft_type: DraftType = "micro_comment"
    status: DraftStatus
    risk_level: Literal["low", "medium", "high", "blocked"]
    created_at: datetime
    updated_at: datetime
    published_url: str | None = None

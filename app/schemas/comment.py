from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class HotTopic(BaseModel):
    rank: int | None = None
    original_rank: int | None = None
    keyword: str
    hot_value: str | None = None
    category_label: str | None = None
    read_count: int | None = None
    discussion_count: int | None = None
    sampled_posts_count: int | None = None
    controversy_score: float | None = None
    url: str | None = None
    label: str | None = None
    platform: str = "manual"
    source: str = "manual"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


TopicAssetStatus = Literal["observing", "candidate", "research_needed", "researched", "archived"]
PlatformTarget = Literal["weibo", "zhihu", "video", "wechat"]
PlatformRoutingDecisionType = Literal["recommended", "optional", "not_recommended"]


class TopicAsset(BaseModel):
    id: str
    canonical_title: str
    summary: str = ""
    source_platforms: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    hot_signals: dict[str, str | int | float | None] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "low"
    research_status: Literal["none", "needed", "partial", "complete"] = "none"
    status: TopicAssetStatus = "observing"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TopicAssetCreateRequest(BaseModel):
    canonical_title: str = Field(min_length=1)
    summary: str = ""
    source_platforms: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    hot_signals: dict[str, str | int | float | None] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "low"
    research_status: Literal["none", "needed", "partial", "complete"] = "none"
    status: TopicAssetStatus = "observing"


class TopicAssetUpdateRequest(BaseModel):
    canonical_title: str | None = None
    summary: str | None = None
    source_platforms: list[str] | None = None
    source_urls: list[str] | None = None
    hot_signals: dict[str, str | int | float | None] | None = None
    tags: list[str] | None = None
    risk_level: Literal["low", "medium", "high"] | None = None
    research_status: Literal["none", "needed", "partial", "complete"] | None = None
    status: TopicAssetStatus | None = None


class TopicAssetSummary(BaseModel):
    id: str
    canonical_title: str
    source_platforms: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "low"
    research_status: Literal["none", "needed", "partial", "complete"] = "none"
    status: TopicAssetStatus = "observing"
    updated_at: datetime


class PlatformRoutingDecision(BaseModel):
    topic_asset_id: str
    target_platform: PlatformTarget
    fit_score: float = Field(ge=0, le=100)
    decision: PlatformRoutingDecisionType
    reasons: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    suggested_angle: str = ""
    required_research: list[str] = Field(default_factory=list)


class PlatformRoutingResponse(BaseModel):
    topic_asset_id: str
    llm_used: bool = False
    decisions: list[PlatformRoutingDecision]


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


class StyleMemoryObservation(BaseModel):
    creator_name: str = ""
    platform: str = "manual"
    account_id: str = "today_direct"
    style_name: str = "general"
    hook_patterns: list[str] = Field(default_factory=list)
    sentence_rhythm: str = ""
    argument_structure: list[str] = Field(default_factory=list)
    rhetorical_devices: list[str] = Field(default_factory=list)
    emotion_level: int = Field(default=5, ge=1, le=10)
    suitable_topics: list[str] = Field(default_factory=list)
    avoid_points: list[str] = Field(default_factory=list)
    reusable_rules: list[str] = Field(default_factory=list)
    example_lines: list[str] = Field(default_factory=list)
    source_url: str | None = None
    permission_level: Literal["own", "authorized", "public_reference"] = "public_reference"
    needs_review: bool = True


class StyleMemoryExtractRequest(BaseModel):
    creator_name: str = ""
    platform: str = "manual"
    source_text: str = Field(min_length=1)
    source_url: str | None = None
    account_id: str = "today_direct"
    style_name: str = "general"
    permission_level: Literal["own", "authorized", "public_reference"] = "public_reference"
    operator_note: str | None = None
    auto_ingest: bool = False
    rebuild_index: bool = True


class StyleMemoryIngestRequest(BaseModel):
    observation: StyleMemoryObservation
    operator_note: str | None = None
    rebuild_index: bool = True


class StyleMemoryIngestResponse(BaseModel):
    success: bool = True
    path: str
    observation: StyleMemoryObservation
    rebuild_stats: dict[str, int | bool | str] | None = None


class StyleMemoryExtractResponse(BaseModel):
    observation: StyleMemoryObservation
    ingested: StyleMemoryIngestResponse | None = None


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
    source_platform: str = "weibo"
    enrich_metrics: bool = False
    research_limit: int = Field(default=10, ge=1, le=10)


class SelectedTopic(BaseModel):
    rank: int | None = None
    original_rank: int | None = None
    keyword: str
    score: float
    category: str
    risk_level: Literal["low", "medium", "high"] = "low"
    reason: str
    recommended_angle: str
    avoid_points: list[str] = Field(default_factory=list)
    hot_value: str | None = None
    category_label: str | None = None
    read_count: int | None = None
    discussion_count: int | None = None
    sampled_posts_count: int | None = None
    controversy_score: float | None = None
    label: str | None = None
    url: str | None = None
    platform: str = "manual"
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
    rerank_score: float | None = None
    rerank_decision: Literal["select", "backup", "reject"] | None = None
    rerank_reason: str = ""
    needed_context: list[str] = Field(default_factory=list)
    research_summary: str = ""
    source_urls: list[str] = Field(default_factory=list)
    llm_reranked: bool = False


class TopicResearchMetrics(BaseModel):
    keyword: str
    read_count: int | None = None
    discussion_count: int | None = None
    sampled_posts_count: int = 0
    controversy_score: float | None = None
    source_url: str | None = None
    error: str | None = None


class ResearchSource(BaseModel):
    title: str = ""
    url: str = ""
    domain: str = ""
    published_date: str | None = None
    author: str | None = None
    summary: str = ""
    highlights: list[str] = Field(default_factory=list)
    relevance_score: float | None = None
    credibility: Literal["unknown", "low", "medium", "high"] = "unknown"
    ingest_recommendation: Literal["candidate_only", "can_ingest_after_review"] = "candidate_only"


class TopicResearchSourcesRequest(BaseModel):
    topic: str = Field(min_length=1)
    query: str | None = None
    limit: int = Field(default=5, ge=1, le=10)
    include_domains: list[str] = Field(default_factory=list)
    exclude_domains: list[str] = Field(default_factory=list)


class TopicResearchSourcesResponse(BaseModel):
    topic: str
    query: str
    source: str = "exa"
    sources: list[ResearchSource] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    is_configured: bool = True


class WeiboAiSearchResearchRequest(BaseModel):
    topic: str = Field(min_length=1)
    max_polls: int = Field(default=6, ge=1, le=10)
    poll_interval_seconds: float = Field(default=1.5, ge=0, le=10)


class TopicRerankCandidate(BaseModel):
    keyword: str = Field(min_length=1)
    original_score: float = Field(default=0, ge=0, le=100)
    reason: str = ""
    recommended_angle: str = ""
    risk_level: Literal["low", "medium", "high"] = "low"
    category: str = "unknown"
    hot_value: str | None = None
    rank: int | None = None
    label: str | None = None
    category_label: str | None = None
    url: str | None = None
    research_sources: list[ResearchSource] = Field(default_factory=list)


class RerankedTopic(BaseModel):
    keyword: str
    final_score: float = Field(ge=0, le=100)
    decision: Literal["select", "backup", "reject"] = "backup"
    recommended_angle: str = ""
    risk_level: Literal["low", "medium", "high"] = "low"
    reason: str = ""
    needed_context: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    research_summary: str = ""
    source_urls: list[str] = Field(default_factory=list)


class TopicRerankRequest(BaseModel):
    candidates: list[TopicRerankCandidate] = Field(default_factory=list)
    max_results: int = Field(default=3, ge=1, le=10)
    account_id: str = "today_direct"


class TopicRerankResponse(BaseModel):
    selected: list[RerankedTopic] = Field(default_factory=list)
    rejected: list[RerankedTopic] = Field(default_factory=list)
    llm_used: bool = False
    notes: list[str] = Field(default_factory=list)


class GenerationContextRequest(BaseModel):
    topic: str = Field(min_length=1)
    research_sources: list[ResearchSource] = Field(default_factory=list)
    rag_results: list[RetrievedKnowledge] = Field(default_factory=list)
    reranked_topic: RerankedTopic | None = None
    classification: TopicClassification | None = None
    max_sources: int = Field(default=5, ge=1, le=10)
    max_rag_items: int = Field(default=5, ge=1, le=10)


class GenerationContextResponse(BaseModel):
    topic: str
    context_text: str
    source_urls: list[str] = Field(default_factory=list)
    needs_verification: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


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
    use_exa_rerank: bool = False
    use_weibo_aisearch_rerank: bool = True
    exa_research_limit: int = Field(default=5, ge=1, le=10)
    exa_sources_per_topic: int = Field(default=3, ge=1, le=5)
    rerank_account_id: str = "today_direct"


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
DraftType = Literal["micro_comment", "zhihu_answer", "video_script", "wechat_article"]
DraftPlatform = Literal["weibo", "zhihu", "video", "wechat", "other"]


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

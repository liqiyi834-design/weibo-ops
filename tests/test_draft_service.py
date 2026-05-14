from pathlib import Path
from uuid import uuid4

from app.schemas.comment import (
    CommentOutput,
    DraftRecord,
    FactSummary,
    GenerateCommentResponse,
    OpinionDraft,
    SafetyResult,
    TopicClassification,
)
from app.services.draft_service import DraftService


def build_generated_response() -> GenerateCommentResponse:
    return GenerateCommentResponse(
        topic="测试话题",
        account_id="today_direct",
        style="rational_critic",
        fact_summary=FactSummary(topic="测试话题", confirmed_facts=["事实"]),
        topic_classification=TopicClassification(category="social_issue"),
        retrieved_knowledge=[],
        opinion=OpinionDraft(core_conflict="冲突"),
        output=CommentOutput(
            one_liner="一句话",
            short_comment="短评",
            emotional_version="情绪版",
            rational_version="理性版",
            ironic_version="讽刺版",
        ),
        safety=SafetyResult(is_safe=True, risk_level="low"),
    )


def test_draft_service_saves_lists_and_updates():
    test_root = Path(".rag_index") / f"draft-test-{uuid4().hex}"
    service = DraftService(root=test_root)

    draft = service.save(
        generated=build_generated_response(),
        title="测试草稿",
        candidate_pool_id="pool-1",
        candidate_item_id="item-1",
    )
    summaries = service.list_drafts()
    updated = service.update(
        draft_id=draft.id,
        status="reviewed",
        operator_note="人工已审",
        edited_text="人工编辑正文",
    )

    assert isinstance(draft, DraftRecord)
    assert summaries[0].id == draft.id
    assert updated.status == "reviewed"
    assert updated.operator_note == "人工已审"
    assert updated.edited_text == "人工编辑正文"

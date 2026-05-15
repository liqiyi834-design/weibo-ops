from pathlib import Path
from uuid import uuid4

from app.schemas.comment import (
    CommentOutput,
    DraftRecord,
    FactSummary,
    GenerateCommentResponse,
    GenerateZhihuAnswerResponse,
    OpinionDraft,
    SafetyResult,
    TopicClassification,
    ZhihuAnswerOutput,
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


def test_draft_service_saves_zhihu_answer_and_publish_note():
    test_root = Path(".rag_index") / f"zhihu-draft-test-{uuid4().hex}"
    service = DraftService(root=test_root)
    generated = GenerateZhihuAnswerResponse(
        topic="平台售后规则争议",
        account_id="today_direct",
        style="rational_critic",
        fact_summary=FactSummary(topic="平台售后规则争议", confirmed_facts=["事实"]),
        topic_classification=TopicClassification(category="social_issue"),
        retrieved_knowledge=[],
        opinion=OpinionDraft(core_conflict="规则解释与用户预期冲突"),
        output=ZhihuAnswerOutput(
            question_title="如何看待平台售后规则争议？",
            answer_title="先讨论规则，再讨论情绪",
            opening_judgement="值得讨论。",
            background_summary="公开信息有限。",
            core_argument="重点是规则透明度。",
            answer_body="这类问题适合先看规则，再看责任边界。",
        ),
    )

    draft = service.save_zhihu_answer(generated=generated, candidate_pool_id="pool-1")
    updated = service.update(
        draft_id=draft.id,
        status="published_manually",
        published_url="https://www.zhihu.com/question/1/answer/2",
        performance_note="人工发布后记录。",
    )
    summary = service.list_drafts()[0]

    assert isinstance(draft, DraftRecord)
    assert draft.platform == "zhihu"
    assert draft.draft_type == "zhihu_answer"
    assert draft.generated is None
    assert draft.zhihu_answer is not None
    assert updated.published_url == "https://www.zhihu.com/question/1/answer/2"
    assert summary.platform == "zhihu"
    assert summary.draft_type == "zhihu_answer"

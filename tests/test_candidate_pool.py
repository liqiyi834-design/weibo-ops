from pathlib import Path
from uuid import uuid4

from app.schemas.comment import SelectedTopic
from app.services.candidate_pool_service import CandidatePoolService


def test_candidate_pool_service_saves_lists_and_updates():
    test_root = Path(".rag_index") / f"candidate-pool-test-{uuid4().hex}"
    service = CandidatePoolService(root=test_root)
    selected = [
        SelectedTopic(
            rank=1,
            keyword="某品牌文案翻车",
            score=92.5,
            category="brand_pr",
            risk_level="low",
            reason="有冲突点",
            recommended_angle="从公关边界切入。",
            avoid_points=["不要自动发布"],
            source="test",
            target_platform_scores={"weibo": 92.5, "zhihu": 81.0},
            recommended_targets=["weibo", "zhihu"],
            zhihu_question_title="如何看待某品牌文案翻车？",
            zhihu_answer_angle="从品牌沟通和用户预期展开。",
            zhihu_required_research=["补充品牌回应"],
            zhihu_reason="适合展开成长回答",
        )
    ]

    pool = service.save(selected=selected, source="test", title="今日候选池")
    summaries = service.list_pools()
    updated = service.update_item(
        pool_id=pool.id,
        item_id=pool.items[0].id,
        status="selected",
        operator_note="人工确认优先写",
    )

    assert pool.title == "今日候选池"
    assert summaries[0].id == pool.id
    assert summaries[0].item_count == 1
    assert updated.items[0].status == "selected"
    assert updated.items[0].operator_note == "人工确认优先写"
    assert updated.items[0].target_platform_scores["zhihu"] == 81.0
    assert updated.items[0].zhihu_question_title == "如何看待某品牌文案翻车？"

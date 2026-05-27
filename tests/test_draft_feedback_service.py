from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.feedback import DraftFeedbackRequest
from app.services.draft_feedback_service import DraftFeedbackService
from mcp_server.tools import record_draft_feedback_tool


def _feedback_path() -> Path:
    root = Path(".rag_index") / f"feedback-test-{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root / "feedback.jsonl"


def test_record_draft_feedback_appends_pending_record():
    path = _feedback_path()
    service = DraftFeedbackService(path)

    response = service.record(
        DraftFeedbackRequest(
            topic="盒马郑重道歉",
            action="too_ai",
            comment="太像AI，少一点总结腔，多一点人的具体判断。",
            source="telegram",
        )
    )

    records = service.list_records()
    assert response.success is True
    assert response.path == str(path)
    assert records[0].topic == "盒马郑重道歉"
    assert records[0].action == "too_ai"
    assert records[0].status == "pending_review"


def test_record_draft_feedback_requires_topic_or_draft_id():
    with pytest.raises(ValidationError):
        DraftFeedbackRequest(comment="太硬了")


def test_record_draft_feedback_mcp_tool():
    path = _feedback_path()
    service = DraftFeedbackService(path)

    result = record_draft_feedback_tool(
        topic="某话题",
        action="rewrite",
        comment="角度对，但语气太硬，重写得松一点。",
        source="hermes",
        service=service,
    )

    assert result["success"] is True
    assert result["record"]["topic"] == "某话题"
    assert result["record"]["action"] == "rewrite"
    assert path.exists()

from pathlib import Path
from uuid import uuid4

from app.schemas.notification import ReviewMessageRequest
from app.services.notification_service import NotificationService


class FakeNotificationService(NotificationService):
    def __init__(self, tmp_path: Path):
        super().__init__(hermes_home=tmp_path / "hermes", dedupe_path=tmp_path / "sent.jsonl")
        self.sent_texts: list[str] = []

    def _telegram_config(self) -> dict[str, str]:
        return {
            "TELEGRAM_BOT_TOKEN": "token",
            "TELEGRAM_HOME_CHANNEL": "123",
        }

    def _telegram_send_message(self, token: str, chat_id: str, text: str, proxy: str | None) -> dict:
        self.sent_texts.append(text)
        return {"ok": True, "result": {"message_id": len(self.sent_texts)}}


def _test_root() -> Path:
    root = Path(".rag_index") / f"notification-test-{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_review_message_sends_to_configured_home_channel():
    service = FakeNotificationService(_test_root())

    response = service.send_review_message(
        ReviewMessageRequest(
            title="本轮候选摘要",
            body="候选 A\n候选 B",
            message_type="candidate_summary",
            dedupe_key="run-1-summary",
        )
    )

    assert response.ok is True
    assert response.sent_count == 1
    assert response.message_ids == [1]
    assert "本轮候选摘要" in service.sent_texts[0]
    assert "候选 A" in service.sent_texts[0]


def test_review_message_splits_long_body():
    service = FakeNotificationService(_test_root())

    response = service.send_review_message(
        ReviewMessageRequest(
            title="话题 A",
            body="段落\n" + ("x" * 1500) + "\n" + ("y" * 1500),
            max_chars=1000,
        )
    )

    assert response.ok is True
    assert response.chunk_count > 1
    assert response.sent_count == response.chunk_count
    assert "(1/" in service.sent_texts[0]


def test_review_message_dedupe_key_skips_repeat():
    service = FakeNotificationService(_test_root())
    request = ReviewMessageRequest(title="话题 A", body="正文", dedupe_key="same-key")

    first = service.send_review_message(request)
    second = service.send_review_message(request)

    assert first.ok is True
    assert second.ok is True
    assert second.skipped is True
    assert len(service.sent_texts) == 1


def test_review_message_reports_missing_config():
    root = _test_root()
    service = NotificationService(hermes_home=root / "missing", dedupe_path=root / "sent.jsonl")

    response = service.send_review_message(ReviewMessageRequest(title="话题 A", body="正文"))

    assert response.ok is False
    assert response.configured is False
    assert response.errors

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.schemas.feedback import DraftFeedbackRecord, DraftFeedbackRequest, DraftFeedbackResponse


class DraftFeedbackService:
    def __init__(self, path: Path | str = Path("output/draft_feedback/feedback.jsonl")):
        self.path = Path(path)

    def record(self, request: DraftFeedbackRequest) -> DraftFeedbackResponse:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        record = DraftFeedbackRecord(
            **request.model_dump(),
            id=f"{now.strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}",
            created_at=now,
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json(ensure_ascii=False) + "\n")
        return DraftFeedbackResponse(record=record, path=str(self.path))

    def list_records(self, limit: int = 50) -> list[DraftFeedbackRecord]:
        if not self.path.exists():
            return []
        rows: list[DraftFeedbackRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(DraftFeedbackRecord(**json.loads(line)))
        return list(reversed(rows[-limit:]))

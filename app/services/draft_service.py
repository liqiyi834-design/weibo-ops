from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.schemas.comment import DraftRecord, DraftStatus, DraftSummary, GenerateCommentResponse


class DraftService:
    def __init__(self, root: Path | str = Path("output/drafts")):
        self.root = Path(root)

    def save(
        self,
        generated: GenerateCommentResponse,
        title: str | None = None,
        candidate_pool_id: str | None = None,
        candidate_item_id: str | None = None,
    ) -> DraftRecord:
        self.root.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        draft = DraftRecord(
            id=f"{now.strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}",
            title=title or generated.topic,
            topic=generated.topic,
            account_id=generated.account_id,
            style=generated.style,
            status="draft",
            created_at=now,
            updated_at=now,
            candidate_pool_id=candidate_pool_id,
            candidate_item_id=candidate_item_id,
            risk_level=generated.safety.risk_level,
            generated=generated,
        )
        self._write(draft)
        return draft

    def list_drafts(self) -> list[DraftSummary]:
        summaries = [self._summary(self._read(path)) for path in self._iter_draft_files()]
        return sorted(summaries, key=lambda item: item.updated_at, reverse=True)

    def get(self, draft_id: str) -> DraftRecord:
        return self._read(self._path(draft_id))

    def update(
        self,
        draft_id: str,
        status: DraftStatus | None = None,
        operator_note: str | None = None,
        edited_text: str | None = None,
    ) -> DraftRecord:
        draft = self.get(draft_id)
        if status is not None:
            draft.status = status
        if operator_note is not None:
            draft.operator_note = operator_note
        if edited_text is not None:
            draft.edited_text = edited_text
        draft.updated_at = datetime.now(timezone.utc)
        self._write(draft)
        return draft

    def _summary(self, draft: DraftRecord) -> DraftSummary:
        return DraftSummary(
            id=draft.id,
            title=draft.title,
            topic=draft.topic,
            account_id=draft.account_id,
            style=draft.style,
            status=draft.status,
            risk_level=draft.risk_level,
            created_at=draft.created_at,
            updated_at=draft.updated_at,
        )

    def _iter_draft_files(self) -> list[Path]:
        if not self.root.exists():
            return []
        return list(self.root.glob("*.json"))

    def _path(self, draft_id: str) -> Path:
        safe_id = draft_id.replace("/", "").replace("\\", "")
        return self.root / f"{safe_id}.json"

    def _write(self, draft: DraftRecord) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(draft.id).write_text(
            draft.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _read(self, path: Path) -> DraftRecord:
        if not path.exists():
            raise FileNotFoundError(f"Draft not found: {path.stem}")
        return DraftRecord(**json.loads(path.read_text(encoding="utf-8")))

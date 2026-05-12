from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.schemas.comment import (
    CandidatePool,
    CandidatePoolItem,
    CandidatePoolSummary,
    CandidateStatus,
    SelectedTopic,
)


class CandidatePoolService:
    def __init__(self, root: Path | str = Path("output/topic_candidates")):
        self.root = Path(root)

    def save(
        self,
        selected: list[SelectedTopic],
        source: str,
        title: str | None = None,
        notes: list[str] | None = None,
    ) -> CandidatePool:
        self.root.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        pool = CandidatePool(
            id=f"{now.strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}",
            title=title or f"选题候选池 {now.strftime('%Y-%m-%d %H:%M')}",
            source=source,
            created_at=now,
            items=[
                CandidatePoolItem(
                    id=uuid4().hex[:12],
                    status="candidate",
                    **item.model_dump(),
                )
                for item in selected
            ],
            notes=notes or [],
        )
        self._write(pool)
        return pool

    def list_pools(self) -> list[CandidatePoolSummary]:
        summaries = [self._summary(self._read(path)) for path in self._iter_pool_files()]
        return sorted(summaries, key=lambda item: item.created_at, reverse=True)

    def get(self, pool_id: str) -> CandidatePool:
        return self._read(self._path(pool_id))

    def update_item(
        self,
        pool_id: str,
        item_id: str,
        status: CandidateStatus,
        operator_note: str | None = None,
    ) -> CandidatePool:
        pool = self.get(pool_id)
        for item in pool.items:
            if item.id == item_id:
                item.status = status
                item.operator_note = operator_note
                self._write(pool)
                return pool
        raise ValueError(f"Candidate item not found: {item_id}")

    def _summary(self, pool: CandidatePool) -> CandidatePoolSummary:
        return CandidatePoolSummary(
            id=pool.id,
            title=pool.title,
            source=pool.source,
            created_at=pool.created_at,
            item_count=len(pool.items),
            selected_count=sum(1 for item in pool.items if item.status == "selected"),
        )

    def _iter_pool_files(self) -> list[Path]:
        if not self.root.exists():
            return []
        return list(self.root.glob("*.json"))

    def _path(self, pool_id: str) -> Path:
        safe_id = pool_id.replace("/", "").replace("\\", "")
        return self.root / f"{safe_id}.json"

    def _write(self, pool: CandidatePool) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(pool.id).write_text(
            pool.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _read(self, path: Path) -> CandidatePool:
        if not path.exists():
            raise FileNotFoundError(f"Candidate pool not found: {path.stem}")
        return CandidatePool(**json.loads(path.read_text(encoding="utf-8")))

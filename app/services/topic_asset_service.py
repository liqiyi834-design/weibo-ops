from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.schemas.comment import (
    TopicAsset,
    TopicAssetCreateRequest,
    TopicAssetStatus,
    TopicAssetSummary,
    TopicAssetUpdateRequest,
)


class TopicAssetService:
    def __init__(self, root: Path | str = Path("output/topic_assets")):
        self.root = Path(root)

    def create(self, request: TopicAssetCreateRequest) -> TopicAsset:
        self.root.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        asset = TopicAsset(
            id=f"{now.strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}",
            canonical_title=request.canonical_title,
            summary=request.summary,
            source_platforms=_dedupe(request.source_platforms),
            source_urls=_dedupe(request.source_urls),
            hot_signals=request.hot_signals,
            tags=_dedupe(request.tags),
            risk_level=request.risk_level,
            research_status=request.research_status,
            status=request.status,
            created_at=now,
            updated_at=now,
        )
        self._write(asset)
        return asset

    def list_assets(
        self,
        status: TopicAssetStatus | None = None,
        limit: int = 100,
    ) -> list[TopicAssetSummary]:
        assets = [self._read(path) for path in self._iter_asset_files()]
        if status:
            assets = [asset for asset in assets if asset.status == status]
        summaries = [self._summary(asset) for asset in assets]
        return sorted(summaries, key=lambda item: item.updated_at, reverse=True)[:limit]

    def get(self, asset_id: str) -> TopicAsset:
        return self._read(self._path(asset_id))

    def update(self, asset_id: str, request: TopicAssetUpdateRequest) -> TopicAsset:
        asset = self.get(asset_id)
        updates = request.model_dump(exclude_unset=True)
        for field, value in updates.items():
            if value is None:
                continue
            if field in {"source_platforms", "source_urls", "tags"}:
                value = _dedupe(value)
            setattr(asset, field, value)
        asset.updated_at = datetime.now(timezone.utc)
        self._write(asset)
        return asset

    def _summary(self, asset: TopicAsset) -> TopicAssetSummary:
        return TopicAssetSummary(
            id=asset.id,
            canonical_title=asset.canonical_title,
            source_platforms=asset.source_platforms,
            risk_level=asset.risk_level,
            research_status=asset.research_status,
            status=asset.status,
            updated_at=asset.updated_at,
        )

    def _iter_asset_files(self) -> list[Path]:
        if not self.root.exists():
            return []
        return list(self.root.glob("*.json"))

    def _path(self, asset_id: str) -> Path:
        safe_id = asset_id.replace("/", "").replace("\\", "")
        return self.root / f"{safe_id}.json"

    def _write(self, asset: TopicAsset) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(asset.id).write_text(
            asset.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _read(self, path: Path) -> TopicAsset:
        if not path.exists():
            raise FileNotFoundError(f"Topic asset not found: {path.stem}")
        return TopicAsset(**json.loads(path.read_text(encoding="utf-8")))


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item and item.strip()))

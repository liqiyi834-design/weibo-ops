from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.schemas.comment import KnowledgeIngestRequest, KnowledgeIngestResponse
from app.services.knowledge_service import KnowledgeService


class KnowledgeIngestionService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.inbox_dir = Path(settings.knowledge_dir) / "inbox"

    def ingest(self, request: KnowledgeIngestRequest) -> KnowledgeIngestResponse:
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        path = self._next_path(request.topic)
        path.write_text(self._render_markdown(request), encoding="utf-8")

        rebuild_stats = None
        if request.rebuild_index:
            rebuild_stats = KnowledgeService(self.settings).rebuild()

        return KnowledgeIngestResponse(
            topic=request.topic,
            path=str(path),
            source_url=request.source_url,
            needs_review=request.needs_review,
            rebuild_stats=rebuild_stats,
        )

    def _next_path(self, topic: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        slug = _slugify(topic)
        return self.inbox_dir / f"{stamp}-{slug}-{uuid4().hex[:8]}.md"

    def _render_markdown(self, request: KnowledgeIngestRequest) -> str:
        created_at = datetime.now(timezone.utc).isoformat()
        return "\n".join(
            [
                "---",
                f"topic: {request.topic}",
                f"source_url: {request.source_url or ''}",
                f"source_title: {request.source_title or ''}",
                f"credibility: {request.credibility}",
                f"needs_review: {str(request.needs_review).lower()}",
                f"candidate_pool_id: {request.candidate_pool_id or ''}",
                f"candidate_item_id: {request.candidate_item_id or ''}",
                f"created_at: {created_at}",
                "---",
                "",
                f"# {request.topic}",
                "",
                "## Source",
                "",
                f"- URL: {request.source_url or 'manual input'}",
                f"- Title: {request.source_title or ''}",
                f"- Credibility: {request.credibility}",
                f"- Needs review: {request.needs_review}",
                "",
                "## Operator Note",
                "",
                request.operator_note or "",
                "",
                "## Content",
                "",
                request.content.strip(),
                "",
            ]
        )


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text, flags=re.UNICODE).strip("-")
    return (slug or "topic")[:40]

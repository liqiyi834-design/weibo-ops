from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.schemas.comment import KnowledgeIngestRequest, KnowledgeIngestResponse, KnowledgeRecord, KnowledgeRecordSummary
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

    def list_records(
        self,
        candidate_pool_id: str | None = None,
        candidate_item_id: str | None = None,
        limit: int = 50,
    ) -> list[KnowledgeRecordSummary]:
        records = [self._to_summary(self._read_record(path)) for path in self._iter_record_files()]
        if candidate_pool_id is not None:
            records = [record for record in records if record.candidate_pool_id == candidate_pool_id]
        if candidate_item_id is not None:
            records = [record for record in records if record.candidate_item_id == candidate_item_id]
        return sorted(
            records,
            key=lambda record: record.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )[:limit]

    def get_record(self, record_id: str) -> KnowledgeRecord:
        safe_id = record_id.replace("/", "").replace("\\", "")
        path = self.inbox_dir / f"{safe_id}.md"
        if not path.exists():
            raise FileNotFoundError(f"Knowledge record not found: {record_id}")
        return self._read_record(path)

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

    def _iter_record_files(self) -> list[Path]:
        if not self.inbox_dir.exists():
            return []
        return list(self.inbox_dir.glob("*.md"))

    def _read_record(self, path: Path) -> KnowledgeRecord:
        raw = path.read_text(encoding="utf-8")
        metadata, body = _split_frontmatter(raw)
        content = _section_text(body, "Content")
        operator_note = _section_text(body, "Operator Note") or None
        topic = metadata.get("topic") or _title_from_body(body) or path.stem
        created_at = _parse_datetime(metadata.get("created_at"))
        return KnowledgeRecord(
            id=path.stem,
            topic=topic,
            path=str(path),
            source_url=metadata.get("source_url") or None,
            source_title=metadata.get("source_title") or None,
            credibility=_coerce_credibility(metadata.get("credibility")),
            needs_review=(metadata.get("needs_review") or "true").lower() == "true",
            candidate_pool_id=metadata.get("candidate_pool_id") or None,
            candidate_item_id=metadata.get("candidate_item_id") or None,
            created_at=created_at,
            preview=_preview(content or body),
            operator_note=operator_note,
            content=content or body.strip(),
        )

    def _to_summary(self, record: KnowledgeRecord) -> KnowledgeRecordSummary:
        return KnowledgeRecordSummary(**record.model_dump(exclude={"operator_note", "content"}))


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text, flags=re.UNICODE).strip("-")
    return (slug or "topic")[:40]


def _split_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, raw
    metadata: dict[str, str] = {}
    end_index = None
    for index, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_index = index
            break
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
    if end_index is None:
        return metadata, raw
    return metadata, "\n".join(lines[end_index + 1 :]).strip()


def _section_text(body: str, heading: str) -> str:
    marker = f"## {heading}"
    if marker not in body:
        return ""
    after = body.split(marker, 1)[1]
    next_heading = after.find("\n## ")
    section = after[:next_heading] if next_heading >= 0 else after
    return section.strip()


def _title_from_body(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _coerce_credibility(value: str | None) -> str:
    if value in {"unknown", "low", "medium", "high"}:
        return value
    return "unknown"


def _preview(text: str, length: int = 120) -> str:
    compact = " ".join(text.split())
    if len(compact) <= length:
        return compact
    return compact[: length - 1] + "..."

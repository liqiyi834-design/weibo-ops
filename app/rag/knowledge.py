from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeChunk:
    content: str
    source: str
    chunk_id: str


class KnowledgeLoader:
    def __init__(self, knowledge_dir: Path, extra_files: list[Path] | None = None):
        self.knowledge_dir = knowledge_dir
        self.extra_files = extra_files or []

    def load_chunks(self, chunk_size: int = 900, overlap: int = 120) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        for path in self._iter_markdown_files():
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue
            chunks.extend(self._split_text(text, path.name, chunk_size, overlap))
        return chunks

    def _iter_markdown_files(self) -> list[Path]:
        paths: list[Path] = []
        if self.knowledge_dir.exists():
            paths.extend(sorted(self.knowledge_dir.glob("*.md")))
        paths.extend(path for path in self.extra_files if path.exists())
        return list(dict.fromkeys(paths))

    def _split_text(self, text: str, source: str, chunk_size: int, overlap: int) -> list[KnowledgeChunk]:
        if len(text) <= chunk_size:
            return [KnowledgeChunk(content=text, source=source, chunk_id=f"{source}#0")]

        result: list[KnowledgeChunk] = []
        start = 0
        index = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            result.append(KnowledgeChunk(content=text[start:end], source=source, chunk_id=f"{source}#{index}"))
            if end == len(text):
                break
            start = max(end - overlap, start + 1)
            index += 1
        return result

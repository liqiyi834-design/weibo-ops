from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from app.schemas.notification import ReviewMessageRequest, ReviewMessageResponse


class NotificationService:
    def __init__(
        self,
        hermes_home: Path | None = None,
        dedupe_path: Path | None = None,
    ):
        self.hermes_home = hermes_home or Path(os.getenv("HERMES_HOME", "/home/weiboops/.hermes"))
        self.dedupe_path = dedupe_path or Path("output/notifications/sent_review_messages.jsonl")

    def send_review_message(self, request: ReviewMessageRequest) -> ReviewMessageResponse:
        if request.channel != "telegram":
            return ReviewMessageResponse(
                ok=False,
                channel=request.channel,
                configured=False,
                errors=[f"Unsupported channel: {request.channel}"],
                dedupe_key=request.dedupe_key,
            )

        if request.dedupe_key and self._is_duplicate(request.dedupe_key):
            return ReviewMessageResponse(
                ok=True,
                channel=request.channel,
                configured=True,
                skipped=True,
                dedupe_key=request.dedupe_key,
            )

        config = self._telegram_config()
        token = config.get("TELEGRAM_BOT_TOKEN")
        chat_id = config.get("TELEGRAM_HOME_CHANNEL")
        proxy = config.get("TELEGRAM_PROXY")
        if not token or not chat_id:
            missing = []
            if not token:
                missing.append("TELEGRAM_BOT_TOKEN")
            if not chat_id:
                missing.append("TELEGRAM_HOME_CHANNEL")
            return ReviewMessageResponse(
                ok=False,
                channel=request.channel,
                configured=False,
                errors=[f"Missing {', '.join(missing)}."],
                dedupe_key=request.dedupe_key,
            )

        chunks = self._format_chunks(request)
        message_ids: list[int] = []
        errors: list[str] = []
        for chunk in chunks:
            try:
                payload = self._telegram_send_message(token=token, chat_id=chat_id, text=chunk, proxy=proxy)
            except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                errors.append(str(exc))
                break
            if not payload.get("ok"):
                errors.append(str(payload.get("description") or "Telegram sendMessage returned ok=false."))
                break
            result = payload.get("result") or {}
            message_id = result.get("message_id")
            if isinstance(message_id, int):
                message_ids.append(message_id)

        ok = not errors and len(message_ids) == len(chunks)
        if ok and request.dedupe_key:
            self._record_dedupe_key(request.dedupe_key, request, message_ids)
        return ReviewMessageResponse(
            ok=ok,
            channel=request.channel,
            configured=True,
            chunk_count=len(chunks),
            sent_count=len(message_ids),
            message_ids=message_ids,
            errors=errors,
            dedupe_key=request.dedupe_key,
        )

    def _telegram_config(self) -> dict[str, str]:
        config = self._load_hermes_env()
        for key in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_HOME_CHANNEL", "TELEGRAM_PROXY"]:
            if os.getenv(key):
                config[key] = os.getenv(key, "")
        return config

    def _load_hermes_env(self) -> dict[str, str]:
        env_path = self.hermes_home / ".env"
        if not env_path.exists():
            return {}
        result: dict[str, str] = {}
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            result[key.strip()] = value.strip().strip('"').strip("'")
        return result

    def _format_chunks(self, request: ReviewMessageRequest) -> list[str]:
        prefix = f"[{request.message_type}] {request.title.strip()}\n\n"
        body = request.body.strip()
        limit = max(500, request.max_chars)
        body_limit = max(1, limit - len(prefix) - 20)
        body_chunks = self._split_text(body, body_limit)
        total = len(body_chunks)
        chunks = []
        for index, chunk in enumerate(body_chunks, start=1):
            title = prefix
            if total > 1:
                title = f"[{request.message_type}] {request.title.strip()} ({index}/{total})\n\n"
            chunks.append(f"{title}{chunk}".strip())
        return chunks

    def _split_text(self, text: str, limit: int) -> list[str]:
        if len(text) <= limit:
            return [text]

        chunks: list[str] = []
        current = ""
        for paragraph in text.splitlines():
            candidate = f"{current}\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= limit:
                current = candidate
                continue
            if current:
                chunks.append(current)
                current = ""
            while len(paragraph) > limit:
                chunks.append(paragraph[:limit])
                paragraph = paragraph[limit:]
            current = paragraph
        if current:
            chunks.append(current)
        return chunks or [text[:limit]]

    def _telegram_send_message(self, token: str, chat_id: str, text: str, proxy: str | None) -> dict[str, Any]:
        handlers = []
        if proxy:
            handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
        opener = urllib.request.build_opener(*handlers)
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode(
            {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": "true",
            }
        ).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST")
        with opener.open(request, timeout=25) as response:
            return json.loads(response.read().decode("utf-8"))

    def _is_duplicate(self, dedupe_key: str) -> bool:
        if not self.dedupe_path.exists():
            return False
        for line in self.dedupe_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("dedupe_key") == dedupe_key:
                return True
        return False

    def _record_dedupe_key(
        self,
        dedupe_key: str,
        request: ReviewMessageRequest,
        message_ids: list[int],
    ) -> None:
        self.dedupe_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "dedupe_key": dedupe_key,
            "channel": request.channel,
            "message_type": request.message_type,
            "title": request.title,
            "message_ids": message_ids,
        }
        with self.dedupe_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

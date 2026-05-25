from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class HermesStatusService:
    def __init__(self, hermes_home: Path | None = None):
        self.hermes_home = hermes_home or Path(os.getenv("HERMES_HOME", "/home/weiboops/.hermes"))

    def status(self) -> dict[str, Any]:
        services = self._service_status(["weibo-ops-fastapi", "weibo-ops-streamlit", "hermes-gateway", "mihomo"])
        telegram = self._telegram_status()
        logs = self._recent_gateway_logs()
        mcp = self._mcp_status()
        return {
            "services": services,
            "telegram": telegram,
            "hermes_gateway_logs": logs,
            "mcp": mcp,
        }

    def _service_status(self, names: list[str]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for name in names:
            command = ["systemctl", "is-active", name]
            completed = self._run(command, timeout=8)
            result[name] = {
                "state": completed["stdout"].strip() or "unknown",
                "ok": completed["returncode"] == 0 and completed["stdout"].strip() == "active",
                "available": completed["available"],
                "error": completed["stderr"].strip(),
            }
        return result

    def _telegram_status(self) -> dict[str, Any]:
        env = self._load_hermes_env()
        token = env.get("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
        proxy = env.get("TELEGRAM_PROXY") or os.getenv("TELEGRAM_PROXY")
        if not token:
            return {
                "configured": False,
                "ok": False,
                "pending_update_count": None,
                "last_error_message": "TELEGRAM_BOT_TOKEN not configured for this process.",
            }

        try:
            payload = self._telegram_get_webhook_info(token, proxy)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return {
                "configured": True,
                "ok": False,
                "pending_update_count": None,
                "last_error_message": str(exc),
            }
        except json.JSONDecodeError:
            return {
                "configured": True,
                "ok": False,
                "pending_update_count": None,
                "last_error_message": "Telegram response is not valid JSON.",
            }

        result = payload.get("result") or {}
        return {
            "configured": True,
            "ok": bool(payload.get("ok")),
            "pending_update_count": result.get("pending_update_count"),
            "last_error_message": result.get("last_error_message"),
            "url_set": bool(result.get("url")),
            "allowed_updates_count": len(result.get("allowed_updates") or []),
            "proxy_configured": bool(proxy),
        }

    def _telegram_get_webhook_info(self, token: str, proxy: str | None) -> dict[str, Any]:
        handlers = []
        if proxy:
            handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
        opener = urllib.request.build_opener(*handlers)
        url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        with opener.open(url, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    def _recent_gateway_logs(self) -> dict[str, Any]:
        command = ["journalctl", "-u", "hermes-gateway", "-n", "120", "--no-pager", "-o", "short-iso"]
        completed = self._run(command, timeout=12)
        if completed["returncode"] != 0:
            return {
                "available": completed["available"],
                "ok": False,
                "lines": [],
                "error": completed["stderr"].strip(),
            }
        lines = completed["stdout"].splitlines()
        important = [
            line
            for line in lines
            if any(marker in line for marker in ["ERROR", "WARNING", "NetworkError", "ConnectError", "polling"])
        ]
        return {
            "available": True,
            "ok": True,
            "lines": important[-30:],
            "error": "",
        }

    def _mcp_status(self) -> dict[str, Any]:
        hermes_bin = Path("/home/weiboops/.local/bin/hermes")
        if not hermes_bin.exists():
            return {
                "available": False,
                "ok": False,
                "tools_discovered": None,
                "summary": "Hermes CLI not found at /home/weiboops/.local/bin/hermes.",
            }
        env = os.environ.copy()
        env["HERMES_HOME"] = str(self.hermes_home)
        env["PATH"] = "/home/weiboops/.local/bin:" + env.get("PATH", "")
        completed = self._run(
            [str(hermes_bin), "mcp", "test", "hotcomment_ai"],
            timeout=35,
            env=env,
        )
        output = "\n".join(part for part in [completed["stdout"], completed["stderr"]] if part)
        tools_count = None
        for line in output.splitlines():
            if "Tools discovered:" in line:
                try:
                    tools_count = int(line.rsplit(":", 1)[-1].strip())
                except ValueError:
                    tools_count = None
                break
        return {
            "available": completed["available"],
            "ok": completed["returncode"] == 0,
            "tools_discovered": tools_count,
            "summary": "\n".join(output.splitlines()[:18]),
        }

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

    def _run(
        self,
        command: list[str],
        timeout: int,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=env,
            )
        except FileNotFoundError:
            return {"available": False, "returncode": 127, "stdout": "", "stderr": f"{command[0]} not found"}
        except subprocess.TimeoutExpired as exc:
            return {
                "available": True,
                "returncode": 124,
                "stdout": exc.stdout or "",
                "stderr": f"Command timed out after {timeout}s.",
            }
        return {
            "available": True,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

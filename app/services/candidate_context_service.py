from __future__ import annotations

from collections.abc import Mapping


def build_candidate_background_context(item: Mapping, base_context: str = "") -> str:
    parts: list[str] = []
    if base_context.strip():
        parts.append(base_context.strip())

    section: list[str] = []
    research_summary = str(item.get("research_summary") or "").strip()
    if research_summary:
        section.extend(["候选池背景摘要：", research_summary])

    rerank_reason = str(item.get("rerank_reason") or "").strip()
    if rerank_reason:
        section.append(f"背景重排理由：{rerank_reason}")

    recommended_angle = str(item.get("recommended_angle") or "").strip()
    if recommended_angle:
        section.append(f"建议角度：{recommended_angle}")

    needed_context = _string_list(item.get("needed_context"))
    if needed_context:
        section.append("待核验/需补充：")
        section.extend(f"- {entry}" for entry in needed_context)

    avoid_points = _string_list(item.get("avoid_points"))
    if avoid_points:
        section.append("避坑点：")
        section.extend(f"- {entry}" for entry in avoid_points)

    source_urls = _string_list(item.get("source_urls"))
    if source_urls:
        section.append("候选池背景来源：")
        section.extend(f"- {url}" for url in source_urls)

    if section:
        parts.extend(["", "## 候选池已检索背景", *section])
    return "\n".join(part for part in parts if part is not None).strip()


def _string_list(value: object) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        values = [value]
    else:
        try:
            values = list(value)  # type: ignore[arg-type]
        except TypeError:
            values = [value]
    return [str(item).strip() for item in values if str(item).strip()]

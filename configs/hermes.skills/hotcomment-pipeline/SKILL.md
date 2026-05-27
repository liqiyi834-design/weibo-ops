---
name: hotcomment-pipeline
description: >
  Run HotComment-AI content generation pipelines through MCP tools. Use this
  skill for cron or manual workflows that fetch hot topics, select candidates,
  collect Weibo AiSearch/Exa background, rerank, generate review-ready drafts,
  send concise staged review messages through the configured home channel,
  and handle explicit RAG ingest follow-ups from review messages.
  Never publish or interact with platform accounts.
tags: [hotcomment, weibo, content, pipeline, mcp, notification, rag]
---

## Hard Rules

- Never auto-publish, auto-comment, auto-forward, auto-like, auto-follow, or auto-DM.
- Final cron output must be a short status line only.
- Long review content must be sent via `send_review_message`.
- Do not quote, summarize, or repeat this skill file, the workflow prompt, tool logs, JSON, or MCP raw outputs.
- Use at most 5 coarse candidates and at most 3 final draft topics for scheduled Telegram workflows.
- Do not ingest Weibo AiSearch or Exa research into RAG unless the user explicitly asks for ingest, auto ingest, or confirms source indices.
- Draft review feedback must be recorded with `record_draft_feedback` first. Do not directly convert feedback into persona/style RAG unless the user explicitly asks to extract or ingest style memory.

## Notification Rules

Use `send_review_message` for staged Telegram delivery:

1. Candidate summary after `select_comment_topics`.
2. One review message per final topic after `generate_comment` and `safety_check`.
3. One completion summary after the workflow finishes.

`send_review_message` boundaries:

- It sends only to the configured home channel.
- Do not pass or invent arbitrary Telegram user IDs.
- Use `message_type` values such as `candidate_summary`, `draft_review`, and `workflow_done`.
- Use a stable `dedupe_key` per run and stage when possible. The key must include the current run timestamp or session id, not only the date, so repeated manual tests on the same day do not get skipped.
- Keep each body concise. The service will split long messages, but the agent should still avoid bloat.
- For each draft review message, also mention feedback examples such as:
  `反馈：保留 / 重写，太像AI / 废弃，商业味太重 / 角度对但太硬。`

## Workflow: auto_candidate_to_review_text

1. Fetch hot topics: call `get_hot_topics` with `limit: 30`.
2. Select candidates: call `select_comment_topics` with `max_results: 5`, `source_limit: 20`.
3. Send candidate summary: call `send_review_message` with `message_type: "candidate_summary"`.
4. Research background for candidates:
   - Prefer `research_weibo_aisearch` for Weibo hot-search topics.
   - Also call `research_topic_sources` with `limit: 3`.
   - If sources are irrelevant, do not pass them as factual support.
5. Rerank: call `rerank_topics_with_research` with `max_results: 3`.
6. Classify each selected topic with `classify_topic`.
7. Retrieve local knowledge with `retrieve_knowledge`.
8. Build context with `build_generation_context`.
9. Generate reviewable drafts with `generate_comment`.
10. Run `safety_check` on each final text.
11. For each safe or reviewable topic, call `send_review_message` with `message_type: "draft_review"`.
12. Each `draft_review` and `workflow_done` message must include a short RAG ingest entry:
    `RAG 入库：回复「入库 <话题> 自动入库」，或「入库 <话题> 1,3」。`
13. Send completion summary with `send_review_message`, then make final cron output one short sentence.

## RAG Ingest Follow-up

When the user replies from Telegram or Hermes chat with an ingest request, route it to the existing MCP tools instead of explaining the pipeline.

Recognize these forms:

- `入库 <话题> 自动入库`
- `把 <话题> 的资料入库`
- `入库 <话题> 1,3`
- `入库 1,3` when the previous reviewed topic is unambiguous
- `这条资料入库：... 来源：...`

Tool routing:

1. If the user gives source text, URL, or a prepared note, call `ingest_knowledge`.
2. If the user gives a topic and says `自动入库` / `直接入库` / `按建议入库`, call `ingest_current_research` with `auto_select: true`.
3. If the user gives a topic plus indices, call `ingest_current_research` with `selected_indices`.
4. If the user only gives a topic without auto authorization or indices, first call `research_topic_sources`, list numbered sources concisely, and ask the user to reply with indices or `自动入库`.
5. After ingest, call `retrieve_knowledge` once to verify recall, then reply with ingest count, saved path if available, and a one-line verification summary.

If the topic is ambiguous, use the exact title from the most recent draft review when available. Otherwise ask for the topic title in one short sentence.

## Draft Feedback Follow-up

When the user replies with draft review feedback, record it as a pending feedback item.

Recognize these forms:

- `保留 1`
- `重写 2，太像AI`
- `废弃 3，商业味太重`
- `这条角度对，但太硬`
- `改得更阴阳怪气一点`
- `更克制一点`

Tool routing:

1. Identify the topic or draft from the most recent `draft_review` message. If unclear, ask for the topic or number.
2. Map the feedback to `record_draft_feedback.action`:
   - keep / 保留 -> `keep`
   - rewrite / 重写 / 改写 -> `rewrite`
   - discard / 废弃 / 不要 -> `discard`
   - 太像AI -> `too_ai`
   - 太硬 -> `too_hard`
   - 太软 / 不够锐 -> `too_soft`
   - 角度错 / 跑偏 -> `wrong_angle`
   - 角度对 -> `good_angle`
   - 需要核验 -> `needs_fact_check`
   - otherwise -> `style_note`
3. Call `record_draft_feedback` with `source: "telegram"` or `source: "hermes"`, the topic/draft id, action, and the user's original feedback as `comment`.
4. Reply briefly: `已记录反馈，状态：待审核沉淀。`
5. If the user explicitly says `沉淀为风格记忆` / `提炼风格` / `入风格库`, then call `extract_style_memory` first. Only call `ingest_style_memory` when the user authorizes ingest.

## Output Template For Draft Review Message

### 话题：...

- 风险：...
- 推荐角度：...
- 背景依据：最多 3 条，每条一句话
- 需要核验：最多 2 条

**生成文本**

> ...

**备选表达**

> ...

**审核意见**

- 是否可过目：是/否
- 主要风险：一句话
- RAG 入库：回复「入库 <话题> 自动入库」，或「入库 <话题> 1,3」。
- 反馈入口：回复「保留 / 重写，太像AI / 废弃，商业味太重 / 角度对但太硬」。

## Quality Rules

- Commercial promotion topics are low priority unless there is clear public-interest controversy or consumer-rights value.
- Do not turn uncertain facts into assertions.
- High-risk topics must be restrained and factual.
- Prefer human-review-ready text over process explanation.
- If background search is missing or contradictory, mark the topic as needing verification or skip it.

---
name: hotcomment-pipeline
description: >
  Run HotComment-AI content generation pipelines through MCP tools. Use this
  skill for cron or manual workflows that fetch hot topics, select candidates,
  collect Weibo AiSearch/Exa background, rerank, generate review-ready drafts,
  and send concise staged review messages through the configured home channel.
  Never publish or interact with platform accounts.
tags: [hotcomment, weibo, content, pipeline, mcp, notification]
---

## Hard Rules

- Never auto-publish, auto-comment, auto-forward, auto-like, auto-follow, or auto-DM.
- Final cron output must be a short status line only.
- Long review content must be sent via `send_review_message`.
- Do not quote, summarize, or repeat this skill file, the workflow prompt, tool logs, JSON, or MCP raw outputs.
- Use at most 5 coarse candidates and at most 3 final draft topics for scheduled Telegram workflows.

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
12. Send completion summary with `send_review_message`, then make final cron output one short sentence.

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

## Quality Rules

- Commercial promotion topics are low priority unless there is clear public-interest controversy or consumer-rights value.
- Do not turn uncertain facts into assertions.
- High-risk topics must be restrained and factual.
- Prefer human-review-ready text over process explanation.
- If background search is missing or contradictory, mark the topic as needing verification or skip it.

# 待办

## P0：补齐 MCP 工具（已完成）

目标：让 Codex/MCP 自动化入口对齐总纲。

已实现：

- `classify_topic`
- `retrieve_knowledge`
- `safety_check`
- `search_knowledge`
- `save_draft`
- `list_drafts`
- `get_hot_topics`

## P1：综合池到平台池分发建议

目标：

```text
TopicAsset
-> 规则层平台适配
-> LLM 编辑判断
-> 人工确认进入微博候选池 / 知乎问题池 / 视频创意池
```

建议新增：

- `PlatformRoutingDecision`
- `RuleBasedPlatformRouter`
- `LLMPlatformRouter`

输出字段：

- `topic_asset_id`
- `target_platform`
- `fit_score`
- `decision`
- `reasons`
- `blockers`
- `suggested_angle`
- `required_research`

硬约束仍由规则层负责，高风险话题不应交给 LLM 单独判断。

## P2：知乎问题池

背景：微博热搜候选池不能长期兼作知乎候选池。

建议新增：

- `ZhihuQuestionPool`
- `ZhihuQuestionCandidate`
- `ZhihuQuestionPoolService`
- Streamlit “知乎问题池”页面。

候选来源：

- `manual_url`
- `generated_from_topic`
- `zhihu_hot_list`
- `zhihu_search`
- `zhihu_home_feed`

如果后续使用 Cookie，只读取问题候选和可见数据，不做互动。

知乎评分重点：

- 领域适配。
- 问题质量。
- 关注/浏览与回答供给差。
- 搜索长尾价值。
- 资料支撑。
- 回答空间。

## P3：知识库自动学习与背景资料搜索

当前已完成人工入库。后续可做半自动搜索：

```text
选题确定
-> 搜索公开背景资料
-> 提取摘要、事实点、争议点、时间线、风险提示
-> 标注来源和可信度
-> 人工审查
-> 入库 RAG
```

建议新增：

- `app/services/research_service.py`
- `POST /api/research/topic`
- MCP 工具 `research_topic`
- MCP 工具 `ingest_topic_research`

边界：

- 只采集公开信息。
- 不读取私信、登录态隐私、付费墙或敏感账号信息。
- 未核实信息必须标注待核验。
- 入库前要保留来源 URL、抓取时间、摘要、可信度、是否需要人工确认。

## P4：多平台 HotTopicProvider

目标：统一不同平台热榜读取结果。

待办：

- 抽象 `HotTopicProvider` 接口。
- 将现有微博实现迁移为 `weibo` provider。
- API 支持 `platform=weibo`、`platform=all` 或指定多个平台。
- 候选池保留来源平台、来源链接、原始排名和平台热度字段。
- 第二个平台优先公开、低风险、无需账号操作的来源，例如百度热搜、知乎热榜、B 站热榜。
- 支持跨平台同题聚合。

## P5：自动化任务

自动化任务只生成候选或草稿，不自动发布。

待实现：

- `fetch_hot_topics_job`
- `classify_hot_topics_job`
- `generate_drafts_job`
- `daily_digest_job`

后续可结合 Codex automations 做定时任务。

## P6：AI 视频创意与提示词包产线

这是独立于热点锐评的第二条内容产线。

建议先设计，不急于实现：

- `CreativeIdeaPool`
- `CreativeIdea`
- `VideoScriptDraft`
- `VideoPromptPack`

输出：

- 视频创意。
- 脚本文案。
- 分镜稿。
- 关键帧提示词。
- 视频生成提示词。
- 封面字。
- 发布文案。
- 风险提示。
- 制作备注。

边界：

- 不自动发布视频。
- 不自动批量搬运素材。
- 不生成仿冒真人、侵犯肖像或误导性真实事件视频。

## P7：RAG 升级

可选方向：

- Chroma。
- OpenAI-compatible embedding。
- 更好的中文分词。
- 文档元数据。
- `/api/knowledge/rebuild` 支持指定目录。

# 待办

## P0：补齐 MCP 工具（已完成）

已实现：

- `classify_topic`
- `retrieve_knowledge`
- `safety_check`
- `search_knowledge`
- `save_draft`
- `list_drafts`
- `get_hot_topics`

## P1：综合池到平台池分发建议（LLM MVP 已完成）

已实现：

- `PlatformRoutingDecision`
- `PlatformRoutingResponse`
- `LLMPlatformRouter`
- `POST /api/topic-assets/{asset_id}/routing`
- Streamlit 综合池详情页“生成 LLM 分发建议”

当前流程：

```text
TopicAsset
-> 规则层给出基础分和硬约束
-> LLM 做编辑判断与平台适配解释
-> 输出微博 / 知乎 / 视频三类平台建议
-> 人工确认是否进入具体平台池
```

输出字段：

- `topic_asset_id`
- `target_platform`
- `fit_score`
- `decision`
- `reasons`
- `blockers`
- `suggested_angle`
- `required_research`

硬约束仍由规则层负责，高风险话题不交给 LLM 单独判断。

后续可继续：

- 把“人工确认加入微博池/知乎问题池/视频创意池”做成明确按钮。
- 记录每次分发建议的历史结果。
- 将 LLM 分发建议接入 MCP。

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

当前已完成人工入库，并在工作台补了 Exa 本轮检索结果的人工勾选入库按钮。后续可继续做更完整的半自动搜索：

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

### P3B：微博智搜背景采集（工作台/API/MCP MVP 已接入）

微博话题页的智搜结果是热搜背景资料的高价值来源，适合补充微博站内语境。智搜 URL 形态：

```text
https://s.weibo.com/aisearch?q=<URL percent-encoded #话题名#>&Refer=weibo_aisearch
```

示例构造：

```python
from urllib.parse import quote

topic = "看不到女干部救灾累哑却盯着金耳环"
url = f"https://s.weibo.com/aisearch?q={quote(f'#{topic}#')}&Refer=weibo_aisearch"
```

已实现：

- `app/services/weibo_aisearch_research_service.py`。
- `POST /api/research/weibo-aisearch`。
- MCP 工具 `research_weibo_aisearch`。
- Streamlit 候选池详情页“微博智搜”按钮，可人工勾选入库 RAG。
- 输入候选话题 `keyword`，自动规范成 `#话题#` 后构造智搜 URL。
- 带 `WEIBO_COOKIE` 低频请求 `ai.s.weibo.com/api/wis/show.json`。
- 支持异步轮询，完成后把智搜 Markdown 摘要封装为 `ResearchSource`。
- 失败时返回 notes：未配置 Cookie、登录重定向、话题拒绝、未完成或请求失败。

边界：

- 使用微博站内可见智搜 JSON 接口，不做验证码绕过，不做高频采集。
- 默认只作为临时背景或待审核资料，不自动发布、不自动互动。

接入顺序：

```text
微博候选题
-> 微博智搜 sources
-> Exa sources
-> TopicRerankService 重排
-> 候选池保存 source_urls / needed_context / rerank_score
-> 人工确认后才可入库 RAG
```

后续待做：

- 生成候选池时把微博智搜 sources 与 Exa sources 合并后进入 `TopicRerankService`
- 支持将用户确认后的智搜摘要整理入库 RAG

## P4：多平台 HotTopicProvider

目标：统一不同平台热榜读取结果。

待办：

- 抽象 `HotTopicProvider` 接口。
- 将现有微博实现迁移为 `weibo` provider。
- API 支持 `platform=weibo`、`platform=all` 或指定多个平台。
- 候选池保留来源平台、来源链接、原始排名和平台热度字段。
- 第二个平台优先公开、低风险、无需账号操作的来源，例如百度热搜、知乎热榜、B 站热榜。
- 支持跨平台同题聚合。

## P5：Hermes agents / MCP 自动化编排

Hermes agents 是后续自动化流程的重点编排层。接入方式优先使用现有 MCP Server；如果 Hermes 运行环境不方便启动本地 MCP，再用 FastAPI 作为 HTTP 适配层。

自动化任务只生成候选、检索结果、审查结果、草稿或摘要，不自动发布、不自动互动、不直接操作微博/知乎/视频平台账号。

建议首批 Hermes 工作流：

- `daily_hot_topics_review`：定时读取热搜，筛选适合人工审核的话题，生成候选池摘要。
- `draft_generation_queue`：从已选候选生成微博短评或知乎回答草稿，保存到草稿箱。
- `safety_review_digest`：汇总高风险话题、blocked 草稿、安全审查问题和待人工处理项。
- `knowledge_research_assist`：为人工选题生成公开资料搜索清单和入库候选，但入库前必须人工确认。

Hermes 可调用的现有 MCP 工具：

- `get_hot_topics`
- `select_comment_topics`
- `classify_topic`
- `retrieve_knowledge`
- `generate_comment`
- `save_draft`
- `list_drafts`
- `safety_check`

待实现：

- Hermes MCP 启动脚本或配置样例。
- Hermes 工作流提示词与工具白名单。
- 自动化运行日志与失败记录。
- 每日任务生成数量上限与节流策略。
- `fetch_hot_topics_job`
- `classify_hot_topics_job`
- `generate_drafts_job`
- `daily_digest_job`

边界：

- 不暴露 `publish_to_weibo`、自动评论、自动转发、自动点赞、自动关注、自动私信等工具。
- 不让 Hermes 读取或输出 API key、Cookie、token、真实账号隐私。
- 高风险话题只允许生成理性版候选或审查摘要，不能生成煽动性草稿。
- 所有草稿默认进入草稿箱，由人编辑、审核、发布和复盘。

后续可结合 Codex automations 做定时唤起，也可由 Hermes 自身调度。

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

### P7-Style：风格记忆库（MVP 已完成）

已实现：

- `StyleMemoryService`
- `POST /api/style-memory/extract`
- `POST /api/style-memory/ingest`
- `GET /api/style-memory/cards`
- Streamlit “风格记忆库” tab
- MCP 工具 `extract_style_memory`、`ingest_style_memory`
- Hermes workflow `style_memory_ingest`

后续可继续：

- 配置相关博主 allowlist。
- 为自有/授权账号做定时自动提炼。
- 给风格卡增加 reviewed/archived 状态。
- 生成时对风格记忆和事实资料做分路检索与 rerank。

### P7-Persona：人格判断框架与人味反馈

目标：让生成文本不只“像某种写法”，而是有稳定观察位置、价值排序和反应方式。

当前已具备：

- 事实背景层：Exa、本地 RAG、`build_generation_context`、`retrieve_knowledge`。
- 账号风格层：多账号配置、persona、情绪上限、风险降温。
- 风格记忆库 MVP：可提炼公开/授权文本中的写法观察并入库。
- 安全与人工审核：`safety_check`、草稿箱、工作台、Hermes 待过目输出。

待补齐：

- `PersonaJudgmentProfile`：按账号沉淀价值排序和默认判断框架。
  - 品牌公关：优先看用户是否被话术转移成本。
  - 商业促销：默认警惕规则不透明、门槛隐藏和注意力占用。
  - 娱乐话题：少站队，多看叙事机制、粉丝情绪和平台放大。
  - 公共争议：先核事实，再谈责任边界和制度成本。
- 好稿/坏稿反馈库：审核时记录“像我/不像我/太 AI/角度对/判断太满/梗别再用”。
- 人味评估器：生成后检查是否模板化、是否只有资料摘要、是否缺少具体经验感、是否符合账号判断习惯。
- RAG 分路：
  - `fact_rag`：事实、资料、背景和待核验点。
  - `style_rag`：句法、节奏、表达习惯和禁用表达。
  - `persona_rag`：价值排序、判断框架、复盘经验和好坏稿反馈。
- 工作台入口：在草稿审核区加入一键反馈按钮，把人工编辑意见沉淀回人格/风格记忆。
- Hermes 入口：允许 Hermes 汇总本轮草稿反馈，但只写入待审核反馈记录，不直接改人格规则。

第一版建议：

```text
草稿生成
-> 人工审核
-> 标记像/不像、角度、强度、模板感
-> 写入 feedback record
-> 周期性汇总为 PersonaJudgmentProfile 草案
-> 人工确认后进入 persona_rag
```

边界：

- 不模仿某个外部博主本人，只沉淀授权账号或公开文本的抽象写法和判断习惯。
- 不保存大段原文。
- 人格规则变更必须可追溯、可回滚、可人工确认。

可选方向：

- Chroma。
- OpenAI-compatible embedding。
- 更好的中文分词。
- 文档元数据。
- `/api/knowledge/rebuild` 支持指定目录。

### P7A：Hybrid RAG + Rerank（优先）

当前 RAG 是 Vanilla Vector RAG + 关键词 fallback。下一步优先升级为真正的 Hybrid RAG：

```text
query
-> vector retrieve top_k
-> keyword/BM25 retrieve top_k
-> merge + dedupe
-> rerank
-> return compact context
```

第一版 rerank 可以先用简单规则：

- 查询词命中数。
- chunk 来源优先级。
- `credibility`。
- `needs_review`。
- recency。
- 向量相似度。

后续再升级为 LLM rerank 或 cross-encoder rerank。

目标：减少无关写作公式被召回，提高人格规则、事实资料、安全边界的匹配精度。

### P7B：轻量 Self-RAG

在生成前增加“资料充足性判断”：

```text
RAG context + Exa context
-> LLM 判断 enough / weak / insufficient
-> insufficient 时不硬生成，输出需要补资料清单
```

适用场景：

- 事故、刑案、未成年人、公共安全等高风险话题。
- RAG 只召回写作公式，没有召回具体事实。
- Exa 结果来源不足或互相矛盾。

### P7C：Corrective RAG

在召回后增加结果过滤：

- 相关性过低的 chunk 丢弃。
- 过时资料降权。
- `needs_review=true` 的事实资料生成时必须标注待核验。
- 低可信来源只作为线索，不作为确定事实。

### P7D：Graph RAG（暂缓）

暂不优先实现 Graph RAG。只有当项目开始长期维护人物、公司、作品、事件、平台规则之间的关系库时，再考虑实体抽取、关系图谱和社区摘要。

## P3A：微博智搜 + Exa 参与选题评分与临时背景（MVP 已接入）

在现有硬规则评分基础上，已新增候选池生成时的微博智搜站内背景、Exa 外部背景检索和 `TopicRerankService` rerank。

当前流程：

```text
get_hot_topics
-> select_comment_topics 粗筛 8-10 条
-> research_weibo_aisearch 调微博智搜补站内语境
-> research_topic_sources 调 Exa 检索背景
-> TopicRerankService 输出重排分、决策、理由、角度、风险和待核验点
-> CandidatePool 保存 rerank_score / rerank_decision / source_urls
```

第一版仍不自动入库 RAG。微博智搜和 Exa 摘要只作为当次评分依据和候选池审查材料。

已具备：

- `EXA_API_KEY`
- `app/services/exa_research_service.py`
- `POST /api/research/exa`
- `POST /api/research/weibo-aisearch`
- MCP 工具 `research_topic_sources`
- MCP 工具 `research_weibo_aisearch`
- MCP 工具 `rerank_topics_with_research`
- Streamlit 候选池生成入口的背景检索重排开关

后续待补：

- 继续优化生成草稿时的候选背景摘要截断、来源展示和待核验提示。
- Hermes 定时工作流已显式调用微博智搜 + Exa + rerank，后续可继续接入保存候选池的自动化动作。

RAG 入库放在用户确认之后：

- 资料值得长期复用时再写入 `app/knowledge/inbox/`。
- 入库内容必须保留来源 URL、标题、检索时间和人工备注。
- 未核实资料不能自动升级为高可信资料。

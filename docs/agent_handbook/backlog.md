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
-> 输出微博 / 知乎 / 视频 / 公众号四类平台建议
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

- 把“人工确认加入微博池/知乎问题池/视频创意池/公众号文章池”做成明确按钮。
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

## P3：知识库自动学习与背景资料搜索（MVP 已完成）

当前已完成背景资料搜索和人工审查入库的主链路：

- Exa 公开资料检索。
- 微博智搜站内背景采集。
- 候选池生成时可选“微博智搜 + Exa + `TopicRerankService`”背景检索重排。
- 工作台/API/MCP 支持把本轮公开资料作为临时背景使用。
- 工作台支持人工勾选 Exa/微博智搜资料后入库 RAG。
- 生成微博草稿或知乎回答时可复用候选池保存的背景摘要、来源和待核验点。
- MCP 已提供 `research_topic_sources`、`research_weibo_aisearch`、`rerank_topics_with_research`、`ingest_current_research` 等入口。

当前稳定原则：

```text
选题确定
-> 搜索公开背景资料
-> 提取摘要、事实点、争议点、时间线、风险提示
-> 标注来源和可信度
-> 人工审查
-> 入库 RAG
```

后续只作为体验增强继续推进：

- 继续优化生成草稿时的候选背景摘要截断、来源展示和待核验提示。
- 视需要统一早期命名，把 `research_topic_sources` / `ingest_current_research` 包装成更泛化的 `research_topic` / `ingest_topic_research`。
- 优化资料卡的可信度、时间戳、来源类型和人工备注展示。
- 保持默认不自动入库 RAG；只有用户明确确认或授权后才入库。

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

后续可继续：

- 优化智搜摘要截断、来源类型展示和待核验提示。
- 持续保持用户确认后才整理入库 RAG。

## P4：多平台 HotTopicProvider（MVP 已接入）

目标：统一不同平台热榜读取结果。当前已完成第一版 provider 抽象和统一入口，微博热榜已迁移到 `weibo` provider 路径，并参考 DailyHotApi 的公开实现移植了 `baidu`、`zhihu`、`bilibili` provider。

已实现：

- `HotTopicProvider` / `BaseHotSearchProvider` 统一 provider 接口。
- `HotSearchService.get_hot_topics(platform=..., limit=...)` 统一入口。
- `GET /api/hot?platform=weibo|baidu|zhihu|bilibili|all` 统一热榜 API。
- `GET /api/hot/clusters?platform=all` 跨平台同题聚合 API。
- 保留兼容入口 `GET /api/hot/weibo`。
- MCP `get_hot_topics` / `get_hot_topic_clusters` / `select_comment_topics` 支持 `platform` / `source_platform` 参数，默认仍为 `weibo`。
- 热榜 item、选题、候选池条目保留 `platform`、`source`、`url`、`rank`、`original_rank` 和 `hot_value`。
- `platform=all` 当前聚合 `weibo`、`baidu`、`zhihu` 与 `bilibili`。
- `HotTopicClusterService` 已支持标题规范化、短标题包含和 token overlap 的保守聚合。

后续待办：

- 继续接入更多公开、低风险、无需账号操作的来源，例如 36氪、澎湃新闻、今日头条等。
- 将跨平台 cluster 接入候选池评分，加上跨平台出现加分。
- 继续优化同题聚合的中文分词、别名归一和误合并防护。
- 补充 DailyHotApi MIT License attribution / NOTICE。

## P5：Hermes agents / MCP 自动化编排（基本完成）

Hermes agents 已基本接入为自动化编排层。接入方式优先使用现有 MCP Server；如果 Hermes 运行环境不方便启动本地 MCP，再用 FastAPI 作为 HTTP 适配层。

自动化任务只生成候选、检索结果、审查结果、草稿或摘要，不自动发布、不自动互动、不直接操作微博/知乎/视频平台账号。

已具备：

- Hermes MCP 启动脚本：`tools/Start-HermesMcp.ps1`。
- Linux Hermes MCP 启动脚本：`tools/start_hermes_mcp.sh`。
- 本机配置片段生成：`tools/New-HermesMcpConfig.ps1`。
- Hermes 前置检查：`tools/Test-HermesProjectPrereqs.ps1`。
- Hermes workflow prompt：`configs/hermes.workflows/`。
- Hermes skill：`configs/hermes.skills/hotcomment-pipeline/SKILL.md`。
- 本地工作流调用：`tools/Invoke-HermesWorkflow.ps1`。
- 分段推送工具：`send_review_message`。
- 草稿反馈记录工具：`record_draft_feedback`。
- Exa/RAG 受控入库入口：`ingest_current_research`。

已定义/接入的主要工作流：

- `daily_hot_topics_review`：定时读取热搜，筛选适合人工审核的话题，生成候选摘要。
- `auto_candidate_to_review_text`：端到端生成待过目文本。
- `style_memory_ingest`：提炼并在确认后写入风格记忆。
- `draft_feedback_review`：记录保留、重写、废弃、太像 AI、太硬、角度对/错等反馈。
- `ingest_current_research_to_rag`：在用户确认编号或明确授权后，把公开资料入库 RAG。

后续只作为运行稳定性和体验增强继续推进：

- 继续固化服务器 cron job，例如每日候选、草稿生成、审核摘要。
- 优化自动化运行日志、失败记录和 Telegram 投递错误定位。
- 细化每日任务生成数量上限与节流策略。
- 持续收紧工具白名单和输出长度，避免把 prompt、日志或敏感配置发到 Telegram。
- 视需要补充 `fetch_hot_topics_job`、`classify_hot_topics_job`、`generate_drafts_job`、`daily_digest_job` 等命名化 job。

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

## P6B：微信公众号中长文产线

公众号产线用于中等长度文章，重点服务人文、情感、关系、生活观察和具有账号特色的栏目化表达。

建议新增：

- `WeChatArticlePool`
- `WeChatArticleCandidate`
- `WeChatColumnProfile`
- `WeChatArticleDraft`

第一版流程：

```text
TopicAsset / 人工选题
-> 公众号适配评分
-> 公众号文章池
-> 人工选择账号、栏目和风格
-> 补充资料、案例和观察
-> 生成大纲
-> 人工确认大纲
-> 生成中等长度文章草稿
-> 草稿箱人工编辑、审核、发布记录
```

评分重点：

- 账号定位和栏目适配。
- 人文/情感承载力。
- 具体场景、人物处境和生活经验。
- 是否有独特观察，而不是公共观点复述。
- 资料和案例是否足够支撑 1200-2500 字文章。
- 风险等级和事实可核验程度。

边界：

- 不自动发布公众号文章。
- 不自动群发、留言、私信或涨粉。
- 不批量搬运公号文章，不复刻外部作者。
- 多账号只用于少数自有/朋友账号的差异化配置。

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

已推进：

- Hermes/MCP 已新增 `record_draft_feedback`，先把 Telegram/Hermes 反馈写入 `output/draft_feedback/feedback.jsonl`。
- Hermes workflow `draft_feedback_review` 已定义“保留/重写/废弃/太像 AI/太硬/角度对”等反馈语义。

网页待办：

- Streamlit 草稿箱增加反馈按钮：保留、重写、废弃、太像 AI、太硬、角度对/错。
- 网页按钮调用同一个 `DraftFeedbackService` / `/api/draft-feedback`，不要另建反馈格式。
- 草稿详情页展示最近反馈记录，并保留“提炼为风格记忆”的人工确认按钮。

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

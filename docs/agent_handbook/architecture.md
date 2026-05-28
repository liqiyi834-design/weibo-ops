# 架构

## 分层原则

```text
API / MCP / Streamlit
-> app/services
-> app/llm、app/rag、app/hot_sources
-> 文件存储和配置
```

规则：

- 路由只做请求接收、响应返回和服务调用。
- MCP 只做工具适配，不复制业务逻辑。
- Streamlit 只做工作台 UI，不复制核心业务逻辑。
- 真实模型调用只通过 `app/llm`。
- RAG 只通过 `app/rag` 和 `KnowledgeService`。

## 双入口原则

新功能默认同时考虑两类使用者：

- 真人：通过 Streamlit 工作台、FastAPI 或文档化命令完成选择、审核、确认和修正。
- Hermes：通过 MCP/FastAPI 调用同一套服务能力，完成定时、批处理、检索、摘要和待审核产物生成。

实现顺序推荐：

```text
app/services 核心能力
-> API schema / route
-> Streamlit 真人入口
-> MCP tool / Hermes workflow
-> tests
```

除非功能明确只属于本地维护脚本，否则不要只做 UI 入口，也不要只做 Hermes 工具入口。这样可以保证同一条业务能力既能由人手动操作，也能被 Hermes 编排复用。

## 关键目录

```text
app/
  api/
  core/
  hot_sources/
  llm/
  rag/
  schemas/
  services/
app_ui/
  streamlit_app.py
mcp_server/
  server.py
  tools.py
configs/
accounts/
output/
tests/
docs/
```

## 平台分发

综合池到平台池的分发建议由 `app/services/platform_router.py` 负责。

当前实现：

- `LLMPlatformRouter`
- 规则层基础分与硬约束。
- LLM 编辑判断和平台适配解释。
- API：`POST /api/topic-assets/{asset_id}/routing`

分发建议只供人工确认，不自动加入平台池，不自动生成发布内容。

## 核心生成链路

```text
topic + context_text
-> FactSummarizer
-> TopicClassifier
-> RAG 检索
-> OpinionGenerator
-> PersonaRewriter / style rewrite
-> SafetyChecker
-> GenerateCommentResponse
```

## 热搜来源

当前：

- `WeiboCookieHotSearchProvider`
- `VisibleCaptureHotSearchProvider`
- `MockHotSearchProvider`

`HotSearchService` 对外提供：

- `get_weibo_hot_topics`
- `get_weibo_ent_topics`

后续应抽象多平台 `HotTopicProvider`，让微博、知乎、百度、B 站等来源统一返回结构化热榜结果。

## 数据存储

当前主要使用文件存储：

- 候选池：`output/topic_candidates/`
- 综合池：`output/topic_assets/`
- 草稿箱：`output/drafts/`
- 人工背景资料：`app/knowledge/inbox/`
- 风格记忆库：`app/knowledge/style_memory/`
- 草稿反馈流水：`output/draft_feedback/feedback.jsonl`
- RAG 索引：`.rag_index/`

注意：

- `.rag_index/` 不提交。
- `.env` 不提交。
- Streamlit Community Cloud 文件系统只适合试用，不适合长期协作数据库。

## 配置

DeepSeek 使用 OpenAI-compatible 客户端：

```text
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
USE_OPENAI_EMBEDDINGS=false
```

微博 Cookie：

```text
WEIBO_COOKIE=...
```

不要把真实 key 或 Cookie 写入仓库。

## RAG 与 Exa 分工

当前项目内的 RAG 主要是“编辑部记忆”，不是实时新闻搜索引擎。

现有 `app/knowledge/` 更偏向：

- 人格型 RAG：账号人设、语气、常用句式、禁用句式。
- 风格记忆库：从公开或授权文本提炼出的 hook、节奏、论证结构、修辞手法、适用话题和禁用点。
- 安全规则 RAG：事实核查标准、来源可信度、风险表达替换、红线。
- 写作公式 RAG：微博锐评结构、评论钩子、保守表达模板。

它当前不主要承担具体热点事实背景，例如某个当日事故、争议、作品热搜的完整时间线和公开来源。实时背景资料更适合由 Exa 等搜索能力临时提供。

推荐分工：

```text
Exa = 当前事实、外部公开资料、临时背景
RAG = 长期风格、判断框架、安全边界、已确认可复用资料
LLM = 综合 Exa 临时背景 + RAG 编辑记忆，完成评分、生成和审核摘要
```

生成文本时应同时使用：

```text
context_text = Exa 临时检索摘要 + RAG 检索结果
```

RAG 入库不应作为实时检索的默认副作用。只有资料经过人工确认，或被判断为长期可复用时，才进入 `app/knowledge/inbox/` 并 rebuild 索引。

## 三类 RAG 记忆层

当前底层仍是一个 `.rag_index/index.json` 索引，但业务上已经分成三类记忆层。实现时先用目录、元数据和工具边界区分，暂不急着拆成三套物理索引。

```text
背景资料 RAG
-> app/knowledge/inbox/
-> 事实、来源、资料卡、长期可复用背景

风格记忆 RAG
-> app/knowledge/style_memory/
-> hook、节奏、句式、论证结构、禁用表达

反馈 RAG
-> output/draft_feedback/feedback.jsonl
-> summarize_draft_feedback
-> 人工确认
-> app/knowledge/inbox/ 或未来 persona_memory/
```

### 背景资料 RAG

背景资料 RAG 只保存经过人工确认或明确授权的长期资料，不保存每次搜索拿到的全部临时网页结果。

入口：

- `ingest_knowledge`
- `ingest_current_research`
- Streamlit “把本轮资料入库 RAG”
- Hermes “入库 <话题> 自动入库 / 1,3”

适合保存：

- 可靠来源摘要。
- 时间线和关键事实。
- 已核验的长期背景。
- 以后多个话题都可能复用的资料卡。

不适合保存：

- 低质量转载。
- 未核实爆料。
- 只服务当天情绪的小八卦。
- 搜索结果原始 JSON。

### 风格记忆 RAG

风格记忆 RAG 保存“怎么写”，不保存大段原文，也不复刻某个外部博主本人。

入口：

- `extract_style_memory`
- `ingest_style_memory`
- 工作台风格记忆入口
- Hermes `style_memory_ingest`

适合保存：

- 开头 hook。
- 句子节奏。
- 论证结构。
- 修辞偏好。
- 适用话题。
- 禁用表达和避雷点。

外部公开文本默认 `permission_level=public_reference` 且 `needs_review=true`。自有或授权文本可以更主动沉淀，但仍只保存抽象规则和短例句。

### 反馈 RAG

反馈 RAG 不是把 `feedback.jsonl` 原样入库，而是把人工审稿反馈先当作“流水记录”，再提炼成长期规则草案。

入口：

- `record_draft_feedback`
- `summarize_draft_feedback`

流程：

```text
Telegram/工作台反馈
-> record_draft_feedback
-> output/draft_feedback/feedback.jsonl
-> summarize_draft_feedback(use_llm=false, auto_ingest=false)
-> 生成可审核 Markdown 草案
-> 用户确认
-> summarize_draft_feedback(auto_ingest=true)
-> KnowledgeIngestionService 写入 RAG
```

反馈 RAG 适合沉淀：

- “太像 AI”的具体原因。
- “太硬/太软”的语气边界。
- “角度对/角度错”的判断框架。
- 商业推广、公共争议、娱乐话题等类别的取舍偏好。
- 事实未核清时应降低定性强度的经验。

边界：

- 原始 JSONL 不直接进入 RAG。
- 单条反馈不直接变成人格规则。
- 默认 `summarize_draft_feedback(use_llm=false)`，降低额度消耗。
- `auto_ingest=true` 只在用户确认后使用。

## RAG 技术范式判断

当前实现属于朴素 RAG：

```text
Markdown 知识库
-> chunk
-> 本地向量索引
-> 向量检索
-> 无结果时关键词 fallback
```

技术分类上更接近：

- Vanilla RAG。
- Vector RAG。
- Keyword fallback。

当前还不是：

- Corrective RAG：没有对召回结果做自动纠错、过滤、二次检索。
- Self-RAG：模型没有系统性判断是否需要检索、检索是否足够、是否应该拒绝生成。
- Graph RAG：没有实体、关系图谱和社区摘要。
- Reranking RAG：没有 cross-encoder、LLM rerank 或融合排序。
- 完整 Hybrid RAG：现在只是向量无结果后关键词兜底，不是向量和关键词并行召回后统一排序。

推荐升级路线：

```text
1. Hybrid RAG + Rerank
2. 轻量 Self-RAG
3. Corrective RAG
4. Graph RAG 暂缓
```

原因：

- Hybrid + Rerank 最适合当前 Markdown 知识库，能立刻改善“召回写作公式但缺少真正相关内容”的问题。
- 轻量 Self-RAG 适合内容生产：让模型判断资料是否足够，不足时输出“需要补资料”，而不是硬写。
- Corrective RAG 适合热点事实：过滤过时、低相关、低可信资料。
- Graph RAG 适合长期人物、公司、作品、事件关系库；当前数据规模和维护成本暂不匹配。

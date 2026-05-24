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

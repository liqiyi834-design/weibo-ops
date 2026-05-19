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

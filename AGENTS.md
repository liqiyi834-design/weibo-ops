# AGENTS.md

## 项目目标

把现有微博运营资料升级为 HotComment-AI：一个支持热点输入、背景材料整理、本地知识库检索、人格化锐评生成、安全审查、MCP 工具调用和自动化草稿生产的中文内容生产系统。

项目定位不是“自动发微博机器人”，而是：

```text
热点锐评草稿生成工具 + MCP 工具服务 + 自动化草稿任务 + 人工审核机制
```

默认只生成可审核草稿，不自动发布、不自动评论、不批量互动、不绕过平台风控。

## 最新方案文档

最新技术框架和实现路径以仓库内这份文档为准：

```text
docs/HotComment-AI技术方案.md
```

这份文档来自用户更新的：

```text
微博热点人格化锐评AI项目技术框架及实现路径_MCP自动化更新版.md
```

重点阅读章节：

- `3A. 现实工程实现路径与 GitHub 参考方案`
- `3B. Codex / MCP 插件化与自动化任务设计`
- `3B.4 MCP 工具服务设计`
- `3B.11 自动化任务设计`
- `3B.13 草稿箱机制设计`
- `3B.16 给 Codex 的新增任务：实现 MCP Server`
- `3B.17 给 Codex 的新增任务：实现自动化草稿系统`
- `3B.18 给 Codex 的新增任务：实现草稿箱`

## 当前已完成

### 文档

- 已把用户的完整技术方案整理进 `docs/HotComment-AI技术方案.md`。
- 已更新 `docs/README.md`，说明项目已进入 MCP / 自动化方向。
- README 已包含 FastAPI、RAG、DeepSeek 和 MCP 的基础启动说明。

### FastAPI 核心服务

已实现：

- `GET /`
- `GET /health`
- `GET /api/hot/weibo`
- `POST /api/comment/generate`
- `GET /api/comment/personas`
- `POST /api/knowledge/rebuild`
- `POST /api/knowledge/search`

核心链路：

```text
topic + context_text
-> FactSummarizer
-> TopicClassifier
-> RAG 检索
-> OpinionGenerator
-> PersonaRewriter
-> SafetyChecker
-> GenerateCommentResponse
```

### 真实模型接入

已实现 OpenAI-compatible LLM client：

```text
app/llm/client.py
```

当前可用 DeepSeek：

```text
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
USE_OPENAI_EMBEDDINGS=false
```

API key 只放 `.env`，不要提交。

### RAG

已实现本地 RAG：

- `app/rag/knowledge.py`
- `app/rag/retriever.py`
- `app/rag/embeddings.py`
- `app/rag/vector_store.py`
- `app/services/knowledge_service.py`

当前策略：

- 默认使用本地 hash embedding，不依赖外部 embedding API。
- 可选 OpenAI-compatible embedding：`USE_OPENAI_EMBEDDINGS=true`。
- `.rag_index/` 为本地索引目录，已忽略，不提交。
- 没有向量索引时 fallback 到 `KeywordRetriever`。

当前会索引：

- `app/knowledge/*.md`
- `04_人设与风格规则.md`
- `06_草稿生成提示词.md`
- `08_高热博文公开样本研究.md`
- `10_爆款博文写作公式.md`
- `12_事实核查与风险分级.md`
- `24_高互动正文分析标准.md`

已验证一次索引统计：

```text
document_count: 9
chunk_count: 21
```

### MCP 最小版

已新增：

```text
mcp_server/server.py
mcp_server/tools.py
```

当前 MCP 工具：

- `get_hot_topics`
- `generate_comment`
- `rebuild_knowledge`
- `search_knowledge`

启动：

```powershell
python -m mcp_server.server
```

已验证：

```text
python -c "from mcp_server.server import mcp; print(mcp.name)"
```

输出：

```text
weibo-ops-hotcomment
```

### 测试

当前测试：

```text
tests/test_api.py
tests/test_pipeline.py
tests/test_rag.py
tests/test_safety_checker.py
tests/test_mcp_tools.py
```

已验证：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

结果：

```text
9 passed
```

## 当前待提交改动

当前工作区包含尚未提交的 MCP 和文档更新。提交前必须确认：

- `.env` 不提交。
- `.rag_index/` 不提交。
- `__pycache__/` 不提交。
- `pytest_tmp/` 不提交。

建议提交信息：

```text
完善MCP工具服务与自动化方案文档
```

## 重要经验与踩坑记录

### DeepSeek 配置

DeepSeek 通过 OpenAI-compatible 客户端接入。

`.env` 示例：

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-你的真实DeepSeekKey
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
USE_OPENAI_EMBEDDINGS=false
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
REQUEST_TIMEOUT_SECONDS=30
KNOWLEDGE_DIR=app/knowledge
RAG_INDEX_PATH=.rag_index/index.json
```

注意：

- `OPENAI_API_KEY` 必须是真实 key，不能含中文、空格或引号。
- `OPENAI_BASE_URL` 必须是 `https://api.deepseek.com`，不是 key。
- DeepSeek 聊天模型已通过真实调用验证。

### 代理问题

本机环境曾有代理变量指向 `127.0.0.1`，但代理未启动，导致 SDK 报：

```text
LLM request failed: Connection error.
```

已在代码中通过 `httpx.Client(..., trust_env=False)` 让 LLM 和 embedding client 不继承坏代理环境变量。

### PowerShell 中文显示

PowerShell 中 `Invoke-RestMethod | ConvertTo-Json` 可能显示中文乱码，但服务返回结构和模型调用本身正常。不要仅凭 PowerShell 控制台乱码判断接口失败。

### pytest 临时目录

Windows 环境里 pytest cache/temp 目录曾出现权限问题。测试命令建议使用：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

### 文档同步

用户可能在仓库外层更新方案文档。若出现新版本，先查找：

```powershell
Get-ChildItem -Path E:\work\lqy -Filter '*微博热点人格化锐评AI项目技术框架及实现路径*.md'
```

再同步到：

```text
docs/HotComment-AI技术方案.md
```

## 下一步优先级

### P0：补齐 MCP 工具

根据最新方案文档，下一批 MCP 工具应实现：

- `classify_topic`
- `retrieve_knowledge`
- `safety_check`
- `save_draft`
- `list_drafts`

其中 `get_hot_topics` 已完成；`retrieve_knowledge` 已由 `search_knowledge` 基本覆盖，但名称可后续对齐文档。

### P1：接入微博热搜 Provider

参考项目：

```text
RusianHu/weibo_hotsearch_mcp
```

推荐吸收其微博移动版接口思路，不建议直接照搬整个 MCP 服务。

待实现目录：

```text
app/hot_sources/
  base.py
  mock.py
  weibo_mobile.py
```

已实现接口：

```text
GET /api/hot/weibo
```

已实现 MCP 工具：

```text
get_hot_topics
```

实现说明：

- 已删除微博移动 API 和无 Cookie 网页 HTML Provider，因为当前环境下不稳定。
- 当前热搜 fallback 链为：`WeiboCookieHotSearchProvider -> VisibleCaptureHotSearchProvider -> MockHotSearchProvider`。
- Cookie 只允许通过本地 `.env` 的 `WEIBO_COOKIE` 传入，不提交、不写进代码。
- `VisibleCaptureHotSearchProvider` 读取 `samples/inbox` 和 `samples/processed` 中由 `tools/weibo_visible_capture.js` 导出的 JSON，只解析可见文本，不碰 Cookie 或登录态。
- 所有真实来源失败时 fallback 到 `MockHotSearchProvider`，避免自动化流程中断。

### P2：草稿箱

根据最新方案文档，实现草稿箱机制。

推荐目录：

```text
drafts/
```

推荐能力：

- 保存生成结果为 Markdown 或 JSON。
- 记录 topic、persona、risk_level、source、created_at。
- 不自动发布。

待实现工具：

- `save_draft`
- `list_drafts`

### P3：自动化任务

自动化任务只生成候选草稿，不自动发布。

待实现：

- `fetch_hot_topics_job`
- `classify_hot_topics_job`
- `generate_drafts_job`
- `daily_digest_job`

后续可以结合 Codex automations 做定时任务。

### P4：RAG 升级

当前 RAG 是本地 hash embedding。后续可以考虑：

- Chroma
- OpenAI-compatible embedding
- 更好的中文分词
- 文档元数据
- `/api/knowledge/rebuild` 支持指定目录

## 开发规则

- git 提交信息使用中文。
- 不在代码中硬编码 API key。
- API key 通过 `.env` 或环境变量传入。
- 真实模型调用必须通过 `app/llm` 抽象层。
- 路由只负责接收请求和调用服务，不混入业务逻辑。
- MCP 只作为适配层，核心逻辑应复用 `app/services`。
- 高风险话题必须降低情绪强度。
- 所有生成结果默认进入草稿或返回待审核，不自动发布。
- 不实现自动发布、自动评论、批量互动或绕过平台风控能力。

## AGENTS.md 维护原则

`AGENTS.md` 是本项目跨线程交接的主入口。每当项目状态发生实质变化时，都要同步更新它，确保新线程读完后能知道当前做到哪里、下一步做什么、有什么坑不能踩。

### 必须更新的情况

- 新增或删除核心模块、目录、API、MCP 工具、自动化任务。
- 修改项目架构、技术路线、运行方式或环境变量。
- 接入新的外部服务，例如 DeepSeek、微博热搜 Provider、Chroma、搜索 API。
- 新增重要文档，或用户更新 `docs/HotComment-AI技术方案.md`。
- 测试命令、启动命令、验证方式发生变化。
- 发现新的关键踩坑、平台限制、安全边界或代理/编码/权限问题。
- 完成某个 P0/P1/P2 待办，或调整待办优先级。
- 提交前后如果有重要未提交状态、忽略文件、敏感文件风险，也要记录。

### 应该写入的内容

- 当前已完成能力。
- 当前未完成但已明确的待办事项。
- 最新方案文档的位置和重点章节。
- 关键文件路径。
- 运行、测试、重建 RAG、启动 MCP 的命令。
- 已验证结果，例如 `9 passed`、真实 DeepSeek 调用已成功。
- 关键经验，例如代理变量导致连接失败、PowerShell 中文乱码、pytest 权限问题。
- 安全边界：不自动发布、不自动评论、不绕过平台限制。

### 不应该写入的内容

- API key、token、cookie、私密账号信息。
- `.env` 的真实内容。
- 可用于绕过平台风控、批量互动、自动发布的具体操作指南。
- 与当前项目无关的临时想法。

### 更新风格

- 用中文写。
- 保持简洁，但要足够让新线程接手。
- 优先写事实状态，不写含糊口号。
- 待办事项按 P0/P1/P2/P3 排序。
- 如果某项已完成，要从待办中移走或标注为已完成。
- 如果同步了外部更新版文档，要记录来源文件名和同步到仓库的位置。

## 常用命令

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

启动 FastAPI：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开接口文档：

```text
http://127.0.0.1:8000/docs
```

重建 RAG：

```text
POST /api/knowledge/rebuild
```

启动 MCP：

```powershell
python -m mcp_server.server
```

运行测试：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

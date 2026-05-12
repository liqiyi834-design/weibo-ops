# AGENTS.md

## 项目目标

把现有微博运营资料升级为 HotComment-AI：一个支持热点输入、背景材料整理、本地知识库检索、人格化锐评生成、安全审查、MCP 工具调用和自动化草稿生产的中文内容生产系统。

项目定位不是“自动发微博机器人”，而是：

```text
热点锐评草稿生成工具 + MCP 工具服务 + 自动化草稿任务 + 人工审核机制
```

默认只生成可审核草稿，不自动发布、不自动评论、不批量互动、不绕过平台风控。

## 最新方案文档

最新技术框架和实现路径以仓库根目录这份用户总纲为准：

```text
微博热点人格化锐评AI项目技术框架及实现路径_MCP自动化更新版.md
```

这份文档是项目的最高优先级产品/技术总文档，用于指导 Codex、AI Agent 和开发者理解项目目标、边界、架构和实现路径。

仓库内另有同步整理版：

```text
docs/HotComment-AI技术方案.md
```

如果两份文档内容出现冲突，以根目录 `微博热点人格化锐评AI项目技术框架及实现路径_MCP自动化更新版.md` 为准，再同步更新 `docs/HotComment-AI技术方案.md` 和 `AGENTS.md`。

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

- 已将根目录 `微博热点人格化锐评AI项目技术框架及实现路径_MCP自动化更新版.md` 确立为项目总纲和最高优先级方案文档。
- `docs/HotComment-AI技术方案.md` 作为同步整理版，用于保持 docs 目录内的技术方案索引连续。
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

用户可能更新根目录项目总纲。若出现新版本，先查找：

```powershell
Get-ChildItem -Path E:\work\lqy -Filter '*微博热点人格化锐评AI项目技术框架及实现路径*.md'
```

主文档应保留/更新为：

```text
微博热点人格化锐评AI项目技术框架及实现路径_MCP自动化更新版.md
```

再同步整理到：

```text
docs/HotComment-AI技术方案.md
```

同步后还要更新 `AGENTS.md` 的“当前已完成”“下一步优先级”和关键踩坑记录。若根目录总纲与 docs 整理版冲突，以根目录总纲为准。

## 下一步优先级

### P0：补齐 MCP 工具

根据最新方案文档，下一批 MCP 工具应实现：

- `classify_topic`
- `retrieve_knowledge`
- `safety_check`
- `save_draft`
- `list_drafts`

其中 `get_hot_topics` 已完成；`retrieve_knowledge` 已由 `search_knowledge` 基本覆盖，但名称可后续对齐文档。

### P1：实现“值得锐评选题”推荐

用户新增目标：

```text
爬取微博热搜前 50
-> AI 从事实性、争议度、表达空间、风险、账号匹配度、时效性等角度评价
-> 推荐 3-5 个最值得锐评的选题
-> 给出推荐理由、风险提示、建议角度
-> 最终由人决定选题
```

实现建议：

- 新增 `app/services/topic_selection_service.py`。
- 输入 `HotSearchItem` 列表，默认来自 `GET /api/hot/weibo?limit=50`。
- 输出候选评分：`score`、`reason`、`risk_level`、`recommended_angle`、`avoid_points`。
- 高风险政治、未成年人、隐私、司法、灾难等话题默认降权或只给谨慎角度。
- 只做“推荐选题”，不自动生成发布内容，不自动发布。
- 可增加 API：`POST /api/topics/select`。
- 可增加 MCP 工具：`select_comment_topics`。
- 测试应覆盖：50 条输入、3-5 条输出、风险降权、理由字段非空。

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

### P3：知识库自动学习与背景资料入库

用户新增目标：

```text
选题确定后
-> AI / Codex 智能体自动搜索相关背景信息、公开消息、来源链接
-> 提取摘要、事实点、争议点、时间线、风险提示
-> 保存进本地知识库
-> 重建或增量更新 RAG
-> 后续生成草稿时可检索查阅
```

实现说明：

- 这项能力必须只采集公开信息，不读取私信、登录态隐私、付费墙或敏感账号信息。
- 资料入库前要保存来源 URL、抓取时间、摘要、可信度、是否需要人工确认。
- 未核实信息不得写成确定事实，应该标注“待核验”。
- 推荐新增目录：`app/knowledge/inbox/` 或 `app/knowledge/topics/`。
- 推荐新增服务：`app/services/research_service.py`、`app/services/knowledge_ingestion_service.py`。
- 推荐新增 MCP 工具：`research_topic`、`ingest_topic_research`。
- 推荐新增 API：`POST /api/research/topic`、`POST /api/knowledge/ingest`。
- 入库后调用现有 `KnowledgeService.rebuild()` 或后续增量索引。
- 自动搜索需要明确来源白名单/黑名单、请求频率和失败 fallback，避免把低质搬运内容污染 RAG。

### P4：热搜 Provider 与热榜清洗

当前微博热搜 Cookie 抓取已可用，已验证 `GET /api/hot/weibo?limit=50` 能返回 50 条。

已实现接口：

```text
GET /api/hot/weibo
```

已实现 MCP 工具：

```text
get_hot_topics
```

后续清洗待办：

- 修复 `hot_value` 偶尔混入分类词的问题，例如 `综艺 126022`。
- 根据运营策略决定是否过滤置顶、政务、低评论空间话题。
- 增加热度字段解析测试。

### P5：自动化任务

自动化任务只生成候选草稿，不自动发布。

待实现：

- `fetch_hot_topics_job`
- `classify_hot_topics_job`
- `generate_drafts_job`
- `daily_digest_job`

后续可以结合 Codex automations 做定时任务。

### P6：RAG 升级

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

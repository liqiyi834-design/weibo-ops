# AGENTS.md

## 项目定位

HotComment-AI 是面向少数自有/朋友账号的人机协同内容运营工作台，用于热点选题、背景资料整理、本地知识库检索、风格化锐评草稿生成、安全审查、MCP 工具调用和人工审核。

项目不是自动发微博机器人，也不是矩阵号、刷量或批量互动系统。

明确不做：

- 自动发布微博、知乎回答、视频内容或公众号文章。
- 自动评论、自动转发、自动点赞、自动关注、自动私信。
- 批量互动、刷量、养号矩阵。
- 规避平台风控或限制。
- 诱导网暴、搬运谣言或扩散未经核验的敏感信息。

AI 负责提高选题、资料整理和草稿生产效率；人负责判断、审核、修改和发布。

## 权威文档

当前 Agent 交接入口：

```text
AGENTS.md
docs/agent_handbook/README.md
```

历史完整方案 / 同步整理版：

```text
docs/HotComment-AI技术方案.md
```

Agent 交接分卷：

```text
docs/agent_handbook/README.md
docs/agent_handbook/current_status.md
docs/agent_handbook/workflow.md
docs/agent_handbook/architecture.md
docs/agent_handbook/backlog.md
docs/agent_handbook/hermes_agents.md
docs/agent_handbook/pitfalls.md
docs/agent_handbook/deployment.md
docs/agent_handbook/platform_weibo.md
docs/agent_handbook/platform_zhihu.md
docs/agent_handbook/platform_video.md
docs/agent_handbook/platform_wechat.md
```

如文档冲突，以 `AGENTS.md` 和 `docs/agent_handbook/` 的当前状态、工作流、架构和部署分卷为准；`docs/HotComment-AI技术方案.md` 作为历史完整方案参考。

## 当前状态摘要

已完成：

- FastAPI 核心服务与生成链路。
- 微博热搜 Cookie 抓取、登录失效识别、fallback 和热度字段清洗。
- 多平台 HotTopicProvider MVP：已提供统一 `GET /api/hot` 和 `HotSearchService.get_hot_topics(platform=...)`，微博已迁移为 `weibo` provider 路径，并新增 `baidu`、`zhihu`、`bilibili` 公开热榜 provider；`GET /api/hot/clusters` 支持保守同题聚合。
- 热搜选题推荐与微博候选池 MVP。
- TopicAsset 综合池 MVP，已接入 LLM 平台分发建议。
- Streamlit 工作台第一版。
- 草稿箱第一版。
- 本地 RAG 与人工背景资料入库。
- 背景资料搜索/入库 MVP：Exa、微博智搜、候选池重排、人工勾选入库和生成时复用临时背景已接入。
- 风格记忆库 MVP：工作台/API/MCP 支持把公开或授权文本提炼成写法规则并入库 RAG。
- Hermes 草稿反馈记录 MVP：Telegram/Hermes 可记录保留、重写、废弃、太像 AI、太硬、角度对/错等待审核反馈。
- MCP 工具服务，已补齐 `classify_topic`、`retrieve_knowledge`、`safety_check`、`ingest_knowledge`、`ingest_current_research`、`send_review_message`、`record_draft_feedback`。
- Hermes agents / MCP 自动化编排基本完成：已提供启动脚本、配置样例、工作流 prompt、分段推送、草稿反馈和受控 RAG 入库入口。
- 轻量多账号配置与表达风格配置。
- 知乎回答草稿 MVP 与知乎垂直领域适配。
- 公众号产线已纳入分发建议与文档设计：定位为中等长度文章，重点服务人文、情感、多账号、多风格和栏目化表达。

最新验证：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

当前结果：

```text
97 passed
```

详情见 [current_status.md](docs/agent_handbook/current_status.md)。

## 下一步优先级

当前最值得推进的是：

1. P2：新增独立知乎问题池，停止把微博候选池长期兼作知乎候选池。
2. P4 后续：把跨平台 cluster 接入候选池评分，并继续优化同题聚合。
3. P6B：设计并实现公众号文章池、栏目配置和中等长度文章草稿生成器。
4. P7A：升级 Hybrid RAG + Rerank，减少无关写作公式召回，提高事实资料、风格规则和安全边界匹配精度。
5. P6：继续细化视频创意池，但不急于实现生成链路。
6. P1/P3/P5 收尾：分发历史、背景资料展示、Hermes cron 稳定性、日志和节流策略。

完整待办见 [backlog.md](docs/agent_handbook/backlog.md)。

## 当前工作流

简版流程：

```text
微博热搜/后续多平台热榜
-> 候选评分
-> 微博候选池
-> 人工选择 selected/researched
-> 可加入综合池 TopicAsset
-> 人工补充背景资料并入库 RAG
-> 生成微博短评、知乎回答或公众号文章草稿
-> 草稿箱人工编辑、审核、发布记录和复盘
```

综合池不是平台池。微博、知乎、视频、公众号的候选逻辑应逐步拆开。详情见 [workflow.md](docs/agent_handbook/workflow.md)。

Hermes agents 定位为自动化编排层，只调用 MCP 或 FastAPI 完成候选、检索、审查、资料入库、草稿和摘要任务，不直接操作平台账号。

## 开发规则

- git 提交信息使用中文。
- 涉及业务代码、架构、接口、数据结构、测试策略等代码改动前，必须先与用户讨论实现路径、影响范围和验证方式；用户确认后再改代码。
- 不在代码中硬编码 API key、Cookie、token 或私密账号信息。
- API key、Cookie 只通过 `.env`、Streamlit secrets 或环境变量传入。
- 真实模型调用必须通过 `app/llm` 抽象层。
- 路由只负责接收请求和调用服务，不混入业务逻辑。
- MCP 只作为适配层，核心逻辑复用 `app/services`。
- Hermes agents 只能作为编排器调用 MCP/FastAPI，不能拥有自动发布、自动互动或平台账号操作能力。
- 功能开发默认同时考虑真人工作台入口与 Hermes/MCP 自动化入口：核心能力先沉到 `app/services`，再分别接 Streamlit/API/MCP。
- 高风险话题必须降低情绪强度。
- 所有生成结果默认进入草稿或返回待审核，不自动发布。
- 多账号只用于少数自有/朋友账号的差异化配置，不用于矩阵号、养号或批量操控。
- 测试默认只跑与本次改动相关的定向测试；只有大范围重构、发布前验证、依赖升级或用户明确要求时，才跑全量 `python -m pytest tests -q -p no:cacheprovider`。

## 常用命令

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

启动 FastAPI：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动 Streamlit：

```powershell
streamlit run app_ui/streamlit_app.py
```

启动 MCP：

```powershell
python -m mcp_server.server
```

启动 Hermes 使用的 MCP：

```powershell
.\tools\Start-HermesMcp.ps1
```

Linux 服务器启动 Hermes 使用的 MCP：

```bash
bash tools/start_hermes_mcp.sh --python /opt/weibo-ops/.venv/bin/python
```

为当前 clone 生成 Hermes MCP 配置片段：

```powershell
.\tools\New-HermesMcpConfig.ps1
```

运行 Hermes 工作流：

```powershell
.\tools\Invoke-HermesWorkflow.ps1 -Workflow daily_hot_topics_review
```

端到端生成待过目文本：

```powershell
.\tools\Invoke-HermesWorkflow.ps1 -Workflow auto_candidate_to_review_text
```

运行 Hermes 风格记忆入库：

```powershell
.\tools\Invoke-HermesWorkflow.ps1 -Workflow style_memory_ingest
```

运行 Hermes 草稿反馈记录：

```powershell
.\tools\Invoke-HermesWorkflow.ps1 -Workflow draft_feedback_review
```

Hermes 分段推送工具：

```text
send_review_message
record_draft_feedback
```

`send_review_message` 只发送到已配置的 home channel，用于候选摘要、话题待过目和完成摘要；不得让 Hermes 指定任意收件人或执行平台互动。

`record_draft_feedback` 只记录待审核反馈，不直接改写人格规则或自动入库风格记忆。

`summarize_draft_feedback` 把原始反馈 JSONL 提炼成可审核长期记忆草案；默认不使用 LLM、不入库，只有明确确认后才 `auto_ingest=true` 写入 RAG。

运行测试：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

## AGENTS 维护规则

`AGENTS.md` 只保留入口、硬规则、当前摘要和下一步。实质变化写入对应分卷：

- 当前进度、测试结果、最近提交：`current_status.md`
- 工作流变化：`workflow.md`
- 架构变化：`architecture.md`
- 待办和优先级：`backlog.md`
- Hermes agents / MCP 自动化编排：`hermes_agents.md`
- 坑点与经验：`pitfalls.md`
- 部署方式：`deployment.md`
- Linux 云服务器部署：`deployment/linux/README.md`
- 平台产线：`platform_weibo.md`、`platform_zhihu.md`、`platform_video.md`、`platform_wechat.md`

不要把 API key、Cookie、token、真实账号隐私或可用于绕过平台限制的操作指南写入任何文档。

长期记忆库位于：E:\work\Obsidian

使用规则：
- 开始重要任务前，优先读取相关项目页、工作流和经验记录
- 如果本次任务产生了可复用经验、重要决策、稳定工作流或项目约定，任务结束时询问是否写入长期记忆库
- 不要把完整对话原样写入知识库
- 只沉淀结构化结论、适用场景、推荐做法、限制和相关项目链接

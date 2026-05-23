# AGENTS.md

## 项目定位

HotComment-AI 是面向少数自有/朋友账号的人机协同内容运营工作台，用于热点选题、背景资料整理、本地知识库检索、风格化锐评草稿生成、安全审查、MCP 工具调用和人工审核。

项目不是自动发微博机器人，也不是矩阵号、刷量或批量互动系统。

明确不做：

- 自动发布微博、知乎回答或视频内容。
- 自动评论、自动转发、自动点赞、自动关注、自动私信。
- 批量互动、刷量、养号矩阵。
- 规避平台风控或限制。
- 诱导网暴、搬运谣言或扩散未经核验的敏感信息。

AI 负责提高选题、资料整理和草稿生产效率；人负责判断、审核、修改和发布。

## 权威文档

最高优先级产品/技术总文档：

```text
微博热点人格化锐评AI项目技术框架及实现路径_MCP自动化更新版.md
```

同步整理版：

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
```

如果根目录总纲与其他文档冲突，以根目录总纲为准，再同步更新 docs 和本文件。

## 当前状态摘要

已完成：

- FastAPI 核心服务与生成链路。
- 微博热搜 Cookie 抓取、登录失效识别、fallback 和热度字段清洗。
- 热搜选题推荐与微博候选池 MVP。
- TopicAsset 综合池 MVP，已接入 LLM 平台分发建议。
- Streamlit 工作台第一版。
- 草稿箱第一版。
- 本地 RAG 与人工背景资料入库。
- MCP 工具服务，已补齐 `classify_topic`、`retrieve_knowledge`、`safety_check`。
- 已确认 Hermes agents 支持 MCP，可作为后续自动化编排器接入现有 MCP 工具。
- 轻量多账号配置与表达风格配置。
- 知乎回答草稿 MVP 与知乎垂直领域适配。

最新验证：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

当前结果：

```text
56 passed
```

详情见 [current_status.md](docs/agent_handbook/current_status.md)。

## 下一步优先级

当前最值得推进的是：

1. P2：新增独立知乎问题池，停止把微博候选池长期兼作知乎候选池。
2. P3：设计背景资料搜索/入库的人工审查流程，暂不做全自动网页抓取。
3. P4：继续抽象多平台 HotTopicProvider，优先选择公开、低风险来源。
4. P5：优先接入 Hermes agents / MCP 自动化编排，覆盖每日热点候选、草稿生成和审核摘要；只生成候选或草稿，不自动发布。
5. P6：继续细化视频创意池，但不急于实现生成链路。

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
-> 生成微博短评或知乎回答草稿
-> 草稿箱人工编辑、审核、发布记录和复盘
```

综合池不是平台池。微博、知乎、视频的候选逻辑应逐步拆开。详情见 [workflow.md](docs/agent_handbook/workflow.md)。

Hermes agents 定位为自动化编排层，只调用 MCP 或 FastAPI 完成候选、检索、审查、草稿和摘要任务，不直接操作平台账号。

## 开发规则

- git 提交信息使用中文。
- 不在代码中硬编码 API key、Cookie、token 或私密账号信息。
- API key、Cookie 只通过 `.env`、Streamlit secrets 或环境变量传入。
- 真实模型调用必须通过 `app/llm` 抽象层。
- 路由只负责接收请求和调用服务，不混入业务逻辑。
- MCP 只作为适配层，核心逻辑复用 `app/services`。
- Hermes agents 只能作为编排器调用 MCP/FastAPI，不能拥有自动发布、自动互动或平台账号操作能力。
- 高风险话题必须降低情绪强度。
- 所有生成结果默认进入草稿或返回待审核，不自动发布。
- 多账号只用于少数自有/朋友账号的差异化配置，不用于矩阵号、养号或批量操控。

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
- 平台产线：`platform_weibo.md`、`platform_zhihu.md`、`platform_video.md`

不要把 API key、Cookie、token、真实账号隐私或可用于绕过平台限制的操作指南写入任何文档。

长期记忆库位于：E:\work\Obsidian

使用规则：
- 开始重要任务前，优先读取相关项目页、工作流和经验记录
- 如果本次任务产生了可复用经验、重要决策、稳定工作流或项目约定，任务结束时询问是否写入长期记忆库
- 不要把完整对话原样写入知识库
- 只沉淀结构化结论、适用场景、推荐做法、限制和相关项目链接

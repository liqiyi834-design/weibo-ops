# Hermes agents 接入

Hermes agents 是 HotComment-AI 后续自动化流程的重点编排层。它只负责调度现有 MCP/FastAPI 能力，不能绕过 `app/services`，也不能直接操作微博、知乎或视频平台账号。

## 定位

推荐链路：

```text
Hermes agents
-> MCP Server 或 FastAPI
-> app/services
-> 候选池 / TopicAsset / RAG / 草稿箱
-> Streamlit 人工审核
-> 人工发布与复盘
```

Hermes 可以做：

- 定时读取热搜并生成候选池摘要。
- 对话题做分类、风险判断和本地知识库检索。
- 从已选候选生成微博短评或知乎回答草稿。
- 保存草稿到草稿箱。
- 汇总待审核草稿、高风险话题和安全审查问题。

Hermes 不可以做：

- 自动发布微博、知乎回答或视频。
- 自动评论、转发、点赞、关注、私信。
- 批量互动、养号、刷量或规避平台限制。
- 读取、输出或保存 API key、Cookie、token、真实账号隐私。
- 跳过人工审核把草稿当成最终发布内容。

## MCP 启动

项目已提供 Hermes 可调用的 MCP 启动脚本：

```powershell
.\tools\Start-HermesMcp.ps1
```

该脚本会切到项目根目录并运行：

```powershell
python -m mcp_server.server
```

如果需要指定 Python：

```powershell
.\tools\Start-HermesMcp.ps1 -Python "C:\Path\To\python.exe"
```

脚本会设置 `FASTMCP_LOG_LEVEL=ERROR`，避免 FastMCP 的启动日志写入 stdout 并污染 MCP stdio 协议。

## Clone 后部署流程

每个协作者 clone 项目后，在项目根目录执行：

```powershell
python -m pip install -r requirements.txt
.\tools\Test-HermesProjectPrereqs.ps1
.\tools\New-HermesMcpConfig.ps1
```

`Test-HermesProjectPrereqs.ps1` 会检查：

- `python` 是否可用。
- `hermes` CLI 是否已安装。
- 项目 MCP Server 是否能被 Python 导入。

如果 `hermes` 不存在，先安装 Hermes CLI，再重新运行检查。Hermes 是用户级工具，不写入本项目 `requirements.txt`。

`New-HermesMcpConfig.ps1` 会生成本机专用配置片段：

```text
configs/hermes.mcp.local.yaml
```

该文件包含当前 clone 路径，已加入 `.gitignore`，不要提交。

生成内容也会写入当前 `python.exe` 的绝对路径，避免 Hermes 启动 MCP 子进程时因为环境变量收窄而找不到项目 Python。

## Hermes 配置样例

配置样例见：

```text
configs/hermes.mcp.example.yaml
```

协作者通常不直接复制模板，而是复制 `configs/hermes.mcp.local.yaml` 中生成好的 `mcp_servers.hotcomment_ai` 段落到 `~/.hermes/config.yaml`。不要把 API key、Cookie 或账号 token 写进 Hermes 配置；这些仍然只放 `.env`、系统环境变量或 Streamlit secrets。

推荐工具白名单：

- `get_hot_topics`
- `select_comment_topics`
- `classify_topic`
- `research_topic_sources`
- `research_weibo_aisearch`
- `rerank_topics_with_research`
- `retrieve_knowledge`
- `extract_style_memory`
- `ingest_style_memory`
- `ingest_knowledge`
- `ingest_current_research`
- `build_generation_context`
- `generate_comment`
- `save_draft`
- `list_drafts`
- `safety_check`

暂不开放的工具方向：

- `publish_to_weibo`
- 自动评论、转发、点赞、关注、私信
- 任何读取或导出平台登录凭据的工具

## 首批工作流

项目内 workflow prompt 位于：

```text
configs/hermes.workflows/
```

本地调用脚本：

```powershell
.\tools\Invoke-HermesWorkflow.ps1 -Workflow daily_hot_topics_review
```

端到端自动生成候选文本：

```powershell
.\tools\Invoke-HermesWorkflow.ps1 -Workflow auto_candidate_to_review_text
```

如果只想检查 prompt，不调用模型：

```powershell
.\tools\Invoke-HermesWorkflow.ps1 -Workflow daily_hot_topics_review -DryRun
```

### daily_hot_topics_review

目标：生成每日人工审核用热点候选。

流程：

```text
get_hot_topics
-> select_comment_topics
-> research_weibo_aisearch
-> research_topic_sources
-> rerank_topics_with_research
-> classify_topic
-> 输出候选摘要和风险提示
```

输出要求：

- 最多推荐 5 个话题。
- 微博智搜和 Exa 只作为本轮临时背景，不默认入库 RAG。
- 标注风险等级、推荐角度和避雷点。
- 高风险话题只给理性观察角度，不生成情绪化表达。

### draft_generation_queue

目标：从人工已选候选生成草稿。

流程：

```text
retrieve_knowledge
-> generate_comment 或 save_draft
-> safety_check
-> 保存到草稿箱
```

输出要求：

- 默认使用 `save_draft`。
- 每批限制草稿数量。
- blocked 风险不进入可发布建议，只进入待处理摘要。

### safety_review_digest

目标：生成每日审核摘要。

流程：

```text
list_drafts
-> safety_check
-> 汇总 blocked/high/medium 风险项
```

输出要求：

- 列出需要人工优先处理的草稿。
- 说明风险原因。
- 不输出任何发布指令。

### knowledge_research_assist

目标：辅助人工整理公开背景资料。

流程：

```text
retrieve_knowledge
-> 给出缺失资料清单
-> 人工补充来源
-> 后续人工入库
```

输出要求：

- 只生成搜索方向、事实核验点和入库建议。
- 入库前必须保留来源 URL、可信度和是否需要人工确认。

### ingest_current_research_to_rag

目标：把本轮 Exa 公开资料入库 RAG。

流程：

```text
research_topic_sources
-> 按 1-based 编号列出来源
-> 等待用户确认编号，或在用户明确授权自动入库时自动选择可信来源
-> ingest_current_research
-> retrieve_knowledge 验证
```

输出要求：

- 默认先列资料清单并等待确认。
- 如果用户明确说“自动入库”“直接入库”“按建议入库”，Hermes 可以自动选择有 URL、有摘要、可信度较高的来源入库。
- `selected_indices` 使用展示给用户的 1-based 编号。
- 汇报入库条数、文件路径和一次检索验证摘要。

### style_memory_ingest

目标：把公开或授权文本提炼为风格记忆卡，并按用户确认或授权写入 RAG。

流程：

```text
extract_style_memory
-> 用户确认或 auto_ingest
-> ingest_style_memory
-> retrieve_knowledge 验证
```

输出要求：

- 提炼 hook、句式节奏、论证结构、修辞、适用话题和禁用点。
- 不保存大段原文，不要求模型模仿某个博主本人。
- 外部公开博主默认 `permission_level=public_reference` 且 `needs_review=true`。

## 验证清单

接入 Hermes 后，先验证：

- Hermes 能发现 `hotcomment_ai` MCP server。
- Hermes 只能看到白名单工具。
- `configs/hermes.mcp.local.yaml` 中的路径指向当前 clone。
- MCP 启动命令包含当前机器的 `python.exe` 绝对路径。
- `get_hot_topics` 可返回真实或 fallback 热点。
- `save_draft` 只保存草稿，不发布。
- 高风险话题经过 `classify_topic` 和 `safety_check` 后会降温或进入人工审核。
- 配置文件、日志和输出中没有 API key、Cookie、token 或真实账号隐私。

## Cron 输出与 Telegram 投递

Hermes cron 的“任务执行成功”和“消息投递成功”需要分开判断。

优先看：

```bash
sudo -u weiboops env PATH=/home/weiboops/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HERMES_HOME=/home/weiboops/.hermes /home/weiboops/.local/bin/hermes cron list
```

判断规则：

- `Last run ... ok` 只表示 agent 任务完成。
- 如果同一 job 下方出现 `Delivery failed`，说明 Telegram 等投递通道失败。
- `~/.hermes/cron/output/<job_id>/*.md` 是完整运行存档，通常包含 `## Prompt` 和 skill 注入内容；这不等于 Telegram 一定发送了整段 prompt。
- 判断最终内容时重点看 `## Result` 后的结果，以及 `cron list` 中是否有投递错误。

Telegram 推送类 job 必须在 skill 和 job prompt 中同时写硬性输出约束：

```text
最终回复只输出本次推荐结果，不要复述 skill、系统提示、工具调用过程、JSON 或原始日志。
总长度控制在 2500 个中文字符以内。
最多保留 2 个话题；每个话题只给 1 条生成文本 + 1 条备选表达。
如果结果仍然过长，优先删除过程解释和“暂不采用”项，不要删除生成文本。
```

如果出现 Telegram timeout，先区分：

- 模型或工具调用是否还在运行。
- cron 是否已经 `ok` 但 `Delivery failed`。
- 输出文件是否过大。
- `hermes-gateway` 是否存在 Telegram 网络或代理错误。

不要只凭 output 文件里出现 `## Prompt` 就判断“Telegram 发送了 prompt 全文”。

## Exa + RAG 的 Hermes 编排原则

Hermes 后续接入 Exa 时，推荐把 Exa 作为“临时背景检索工具”，把 RAG 作为“长期编辑记忆”。

定时任务或手动工作流中，Hermes 可以：

```text
get_hot_topics
-> select_comment_topics 粗筛
-> research_topic_sources 调 Exa 获取公开资料摘要
-> 基于 Exa 摘要做 LLM rerank
-> retrieve_knowledge 获取人格化写法、安全边界和已沉淀资料
-> generate_comment 使用 Exa 临时背景 + RAG 结果
-> safety_check
-> 输出待过目文本和参考资料
```

Hermes 不应默认把 Exa 结果写入 RAG。RAG 入库应作为独立动作：默认等待用户确认；如果用户明确授权自动入库，可以由 Hermes 自动选择可信来源并调用入库工具。

当前已提供两个受控入库工具：

- `ingest_knowledge`：把用户提供或整理好的单条资料写入 RAG。
- `ingest_current_research`：Telegram 友好的短参数入库工具，只传 `topic`、编号或 `auto_select`，由工具内部重新检索并写入 RAG。

当前项目内 RAG 的优先作用：

- 账号人格和表达风格。
- 选题判断框架。
- 安全边界和避雷经验。
- 已确认的长期背景资料。
- 复盘沉淀。

Exa 的优先作用：

- 当前事实和外部公开资料。
- 热点背景摘要。
- 评分前的轻量资料补全。
- 生成时的临时上下文。

RAG 技术路线不追求一步到位。Hermes 编排优先配合：

- Hybrid RAG + Rerank：提高召回质量，减少无关风格 chunk 干扰。
- 轻量 Self-RAG：让 Hermes 在资料不足时输出补资料清单，而不是硬生成。
- Corrective RAG：对低相关、过时、低可信资料做过滤或降权。

Graph RAG 暂缓，等项目有稳定实体关系库需求后再评估。

## 摘要型背景来源

背景来源分为两类：

- 链接型来源：Exa、新闻网页、官方公告等，通常有 URL。
- 摘要型来源：微博智搜、平台内智能总结、人工整理笔记、授权文本摘要等，不一定有单条 URL。

MCP schema 和服务层必须允许两类来源并存。`ResearchSource.url` 不应强制要求非空；`source_urls` 只收集存在 URL 的来源。

Hermes 调用时注意：

- `research_topic_sources` 的结果通常可以作为链接型 `research_sources`。
- `research_weibo_aisearch` 的结果更像摘要型背景，可作为 `context_text`、背景依据或无 URL 的 `research_sources`。
- 不能因为智搜摘要没有 URL 就让 `build_generation_context` 参数校验失败。
- 最终给人过目的文本仍应标注来源类型，例如“微博智搜摘要”“Exa/域名来源”“人工整理”。

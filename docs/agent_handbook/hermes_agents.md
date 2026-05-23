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
- `retrieve_knowledge`
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
-> classify_topic
-> 输出候选摘要和风险提示
```

输出要求：

- 最多推荐 5 个话题。
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

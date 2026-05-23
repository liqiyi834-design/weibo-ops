# 部署

## 本地开发

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

Hermes agents 调用 MCP 时推荐使用项目脚本：

```powershell
.\tools\Start-HermesMcp.ps1
```

多人协作时，每个 clone 本地生成自己的 Hermes 配置片段：

```powershell
.\tools\Test-HermesProjectPrereqs.ps1
.\tools\New-HermesMcpConfig.ps1
```

Hermes 配置模板见：

```text
configs/hermes.mcp.example.yaml
```

生成的本机配置片段为 `configs/hermes.mcp.local.yaml`，已加入 `.gitignore`，不要提交。

该片段会包含当前 clone 路径和当前 `python.exe` 绝对路径。Hermes 安装或项目路径变化后，重新运行 `.\tools\New-HermesMcpConfig.ps1` 并刷新 `~/.hermes/config.yaml`。

运行 Hermes 工作流：

```powershell
.\tools\Invoke-HermesWorkflow.ps1 -Workflow daily_hot_topics_review
```

运行测试：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

## Linux 云服务器

单台 Ubuntu 部署说明见：

```text
deployment/linux/README.md
```

包含：

- FastAPI systemd 服务。
- Streamlit systemd 服务。
- Hermes gateway/cron systemd 服务。
- Nginx 反向代理样例。
- Linux 版 Hermes MCP 配置生成脚本。

## Streamlit Community Cloud

当前短期部署建议：方案 B。

```text
Streamlit Community Cloud
-> 本地服务模式直接调用 app/services
-> 不单独部署 FastAPI
MCP 暂时本地跑
```

配置：

```text
Repository: liqiyi834-design/weibo-ops
Branch: main
Main file path: app_ui/streamlit_app.py
```

Secrets 至少配置：

```toml
OPENAI_API_KEY = "..."
OPENAI_BASE_URL = "https://api.deepseek.com"
OPENAI_MODEL = "deepseek-v4-flash"
USE_OPENAI_EMBEDDINGS = "false"
WEIBO_COOKIE = "..."
```

默认不填：

```toml
API_BASE_URL = ""
```

这样工作台会直接调用 `app/services`。后续如果单独部署 FastAPI，再填 `API_BASE_URL` 并切换到 FastAPI 模式。

## MCP 部署边界

MCP 暂时本地跑，不暴露公网。

原因：

- MCP 主要服务 Codex 自动化和本地工具调用。
- Hermes agents 也应优先通过本地 MCP 白名单调用。
- 当前不需要给 Streamlit Cloud 远程调用 MCP。
- 避免把本地工具能力暴露到公网。

## 持久化提醒

当前文件存储位置：

- `output/topic_candidates/`
- `output/topic_assets/`
- `output/drafts/`
- `app/knowledge/inbox/`

Streamlit Community Cloud 文件系统不适合长期多人协作。正式协作后建议：

- 独立 FastAPI 后端。
- 外部数据库。
- 对象存储或托管文件存储。
- 独立 RAG 索引服务。

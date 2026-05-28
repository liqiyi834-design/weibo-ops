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

### 国内云服务器下载策略

如果云服务器位于中国大陆或访问 GitHub 很慢，不要让服务器直接从 GitHub release、raw.githubusercontent.com 或其他大文件源下载依赖。

推荐流程：

```text
本机/海外网络下载 release 包
-> scp 上传到云服务器 /tmp
-> 服务器本地解压、安装、校验版本
```

例如安装 mihomo/Clash 内核时，优先在本机下载 Linux amd64 release 包，再上传到服务器安装：

```powershell
curl.exe -L -o .codex_tmp\mihomo-linux-amd64-v1.gz <GitHub release asset URL>
scp -i $HOME\.ssh\weibo_ops_server .codex_tmp\mihomo-linux-amd64-v1.gz root@<server-ip>:/tmp/mihomo.gz
```

服务器侧只负责解压和安装：

```bash
gzip -d -f /tmp/mihomo.gz
install -m 0755 /tmp/mihomo /usr/local/bin/mihomo
ln -sf /usr/local/bin/mihomo /usr/local/bin/clash
mihomo -v
```

这个策略同样适用于 Hermes wheel、浏览器驱动、模型工具二进制和其他 GitHub release 大文件。除非已经确认服务器访问源站稳定，否则不要把服务器直连 GitHub 下载作为默认部署路径。

### 云服务器 Git 防分叉规则

云服务器默认是运行现场，不是开发现场。Git 历史以本机/GitHub 为准。

`/opt/weibo-ops` 默认应保持为部署工作树。不要把它长期当成临时代码修改目录；`.env`、`.venv`、`.rag_index`、`output/`、运行中产生的风格记忆或样本文件必须放在忽略路径、部署目录外，或写入服务器本地 `.git/info/exclude`。

标准更新路径：

```text
本机改代码
-> 本机测试
-> 本机 commit
-> 本机 push
-> 服务器 git pull --ff-only
-> 重启服务
```

服务器更新命令优先使用：

```bash
sudo -iu weiboops
cd /opt/weibo-ops
git status --short --branch
git pull --ff-only origin main
python -m pytest tests -q -p no:cacheprovider
sudo systemctl restart weibo-ops-fastapi weibo-ops-streamlit hermes-gateway
```

如果服务器访问 GitHub 慢或断：

```text
本机生成已提交版本的文件 / patch / bundle
-> scp 上传服务器
-> 服务器只同步工作树或对齐到本机已存在提交
-> 不在服务器制造新 commit
```

如果服务器本地代理可用，部署前先测试直连和代理两条链路：

```bash
curl -I --max-time 20 https://github.com
curl -x http://127.0.0.1:7890 -I --max-time 20 https://github.com
git ls-remote --heads https://github.com/liqiyi834-design/weibo-ops.git main
env https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 \
  git ls-remote --heads https://github.com/liqiyi834-design/weibo-ops.git main
```

只要 `git ls-remote` 能稳定返回目标 SHA，优先用服务器 `git pull --ff-only`。如果直连失败但代理成功，再给单次 Git 命令加 `http_proxy/https_proxy`。如果两者都不稳，回退到本机 bundle/scp。

硬规则：

- 不在服务器随手 `git commit` / `git am`，除非明确准备把该提交推回主仓库。
- 服务器有临时改动时，先备份 `git status` 和 diff，再决定保留、丢弃或移植到本机提交。
- 紧急 `scp` 覆盖可以用，但事后必须回到本机提交并让服务器对齐。
- 部署拉取使用 `git pull --ff-only`；不能快进时先停下来查，不要 merge。
- Windows 生成 patch 要显式 UTF-8，避免 PowerShell `>` 写成 UTF-16。
- 服务器工作区大量 modified 时，先用 `git diff --name-only --ignore-cr-at-eol origin/main` 判断真实内容差异，避免被 CRLF/LF 换行噪声误导。
- 大版本对齐优先使用影子目录：从 bundle 或远端检出到 `/opt/weibo-ops-next-<sha>`，复制必要运行态资源，跑定向测试和 health check，再停服务整体换名切换。
- 切换后保留旧目录，例如 `/opt/weibo-ops-before-<sha>-<timestamp>`，确认稳定后再人工清理。

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

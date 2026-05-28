# 踩坑记录

## DeepSeek 配置

DeepSeek 通过 OpenAI-compatible 客户端接入。

`.env` 示例：

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-你的真实Key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
USE_OPENAI_EMBEDDINGS=false
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
REQUEST_TIMEOUT_SECONDS=30
KNOWLEDGE_DIR=app/knowledge
RAG_INDEX_PATH=.rag_index/index.json
WEIBO_COOKIE=...
```

注意：

- `OPENAI_API_KEY` 必须是真实 key，不能含中文、空格或引号。
- `OPENAI_BASE_URL` 必须是 `https://api.deepseek.com`，不是 key。
- 不要提交 `.env`。

## 代理问题

本机环境曾有代理变量指向 `127.0.0.1`，但代理未启动，导致 SDK 报：

```text
LLM request failed: Connection error.
```

代码中已通过 `httpx.Client(..., trust_env=False)` 让 LLM 和 embedding client 不继承坏代理环境变量。

## LLM JSON 重试

真实模型偶发会返回 `{}` 或缺少必要字段，导致 Pydantic 报 `Field required`，例如：

```text
OpinionDraft.core_conflict
```

已新增：

```text
app/services/json_retry.py
```

观点生成和风格改写会先检查必要字段；如果缺字段，会带缺失字段列表重试一次。第二次仍失败才合并默认兜底，避免前端直接 500。

## PowerShell 中文显示

PowerShell 中 `Invoke-RestMethod | ConvertTo-Json` 可能显示中文乱码，但服务返回结构和模型调用本身正常。

不要只凭 PowerShell 控制台乱码判断接口失败。

## pytest 临时目录

Windows 环境里 pytest cache/temp 目录曾出现权限问题。测试命令建议使用：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

## 微博 Cookie

Cookie 可能过期。当前代码已识别：

- 重定向到 `login.sina.com.cn`。
- 重定向到 `passport.weibo`。
- HTML 中出现 `sso/login` 或登录页特征。

失效时会 fallback，并在 error 中提示 Cookie 失效。

## 热搜字段

微博热搜热度曾出现：

```text
综艺 126022
剧集 539439
```

当前已拆分：

- `hot_value`: 纯数字热度。
- `category_label`: `综艺`、`剧集`、`电影` 等分类。

## Streamlit Community Cloud

当前推荐方案 B：

```text
Streamlit Community Cloud
-> 本地服务模式直接调用 app/services
-> 不单独部署 FastAPI
MCP 暂时本地跑
```

注意：

- Community Cloud 文件系统只适合试用和轻量协作。
- 候选池、草稿箱、综合池当前仍是文件存储。
- 正式协作后续应接外部持久化存储或独立后端。

## 文档同步

当前交接入口是：

```text
AGENTS.md
docs/README.md
docs/agent_handbook/README.md
```

`docs/HotComment-AI技术方案.md` 保留为历史完整方案 / 同步整理版，不再要求根目录保留旧总纲。

同步原则：

- 当前状态、工作流、架构、部署和踩坑写入 `docs/agent_handbook/` 对应分卷。
- 早期人工运营素材归档在 `docs/legacy_ops/`，只作为知识源参考。
- 如果历史方案、README 和 handbook 冲突，以 `AGENTS.md` 与 `docs/agent_handbook/` 当前分卷为准。

## 国内云服务器访问 GitHub 慢

现象：

```text
curl GitHub release 大文件速度很慢，几分钟只能下载一部分，最终 Operation timed out
curl raw.githubusercontent.com 安装脚本长时间卡住
```

原因通常不是项目问题，而是云服务器所在网络访问 GitHub、GitHub release asset 或 raw.githubusercontent.com 不稳定。

处理原则：

- 不要默认让中国大陆云服务器直连 GitHub 下载大文件。
- 优先在网络更好的本机下载 release 包，再用 `scp` 上传服务器。
- 服务器侧只做解压、安装、权限设置和版本校验。
- 可断点续传时使用 `curl -C -`，但如果速度长期低于可接受范围，应改走本机下载上传。

推荐路径：

```text
本机下载
-> scp 上传 /tmp
-> install 到 /usr/local/bin 或项目指定目录
-> 运行 --version 校验
```

这个经验适用于 mihomo/Clash、Hermes 发行包、浏览器自动化二进制、CLI 工具和其他 GitHub release 资产。

## 服务器部署目录不要混成第二个开发源

现象：

```text
服务器 /opt/weibo-ops 的 HEAD 落后 GitHub main
git status 显示大量 modified/untracked
但其中很多文件其实只是换行差异或运行态文件
```

本次实际原因是服务器部署目录同时承担了代码目录、运行态数据目录和临时代码修改目录：

- 服务器 `HEAD` 停在旧提交，但部分文件被手工或脚本同步到后续状态。
- `.env`、`.venv`、`.rag_index`、`output/`、风格记忆、样本文件等运行态内容混在工作树里。
- Windows 和 Linux 之间 CRLF/LF 换行差异把 modified 数量放大。
- 服务器访问 GitHub 不稳定，直接 `git pull` 不能作为唯一部署手段。

处理原则：

- 本机/GitHub 是 Git 历史权威，服务器只做部署工作树。
- 服务器有脏工作区时，先完整备份：

```bash
git status --short --branch
git status --porcelain=v1
git diff --binary
git diff --stat
git ls-files --others --exclude-standard
```

- 用下面命令区分真实内容差异和换行噪声：

```bash
git diff --name-only --ignore-cr-at-eol origin/main
git diff --stat --ignore-cr-at-eol origin/main
```

- 服务器独有但有价值的代码逻辑，先移植回本机最新代码、补测试、提交并 push，再部署。
- 大版本对齐优先用影子目录：

```text
/opt/weibo-ops-next-<sha>
-> 复制 .env/.venv/.rag_index/output 等运行态资源
-> 跑定向测试和 /health
-> 停服务
-> 旧 /opt/weibo-ops 改名备份
-> next 改名为 /opt/weibo-ops
-> 启动服务并验证
```

- 必须留在部署目录内的运行态目录写入服务器本地 `.git/info/exclude`，例如：

```text
app/knowledge/style_memory/
```

不要在当前运行目录里直接 `reset --hard`，除非已经确认所有改动已备份、服务可停、目标提交明确。

## SSH 传文件卡住先查登录用户

现象：

```text
scp 很小的文件到服务器却长时间无输出，像是传输极慢。
```

本次实际原因不是文件大，也不是网络带宽慢，而是使用了错误的 SSH 登录用户：

```text
weiboops@47.99.102.24 + C:/Users/DenseFog/.ssh/weibo_ops_server
-> 认证失败或等待认证

root@47.99.102.24 + C:/Users/DenseFog/.ssh/weibo_ops_server
-> 正常登录
```

处理原则：

- 传输卡住时，先用短命令验证同一组 `user + key + host` 是否能登录。
- 不要只根据“卡住”判断为网络慢；小文件 scp 超过几十秒就应优先怀疑认证、DNS、代理或 known_hosts 交互。
- 当前服务器密钥默认按 `root` 登录可用；需要写项目文件时，用 `root` 上传/安装后再 `chown weiboops:weiboops`。
- 运行 Hermes、项目服务和 cron 时仍使用 `weiboops` 用户，不要把服务常态改成 root。

推荐验证：

```powershell
ssh -i $HOME\.ssh\weibo_ops_server root@47.99.102.24 "hostname; id"
```

推荐上传路径：

```text
本机 scp 到 /tmp
-> root install 到 /opt/weibo-ops 或 /home/weiboops/.hermes
-> chown weiboops:weiboops
-> grep/命令验证目标文件内容
```

### PowerShell patch 编码

在 Windows PowerShell 里不要用普通重定向生成给 Linux/Git 使用的 patch：

```powershell
git format-patch -1 --stdout HEAD > fix.patch
```

Windows PowerShell 的 `>` 可能把文本写成 UTF-16 LE。上传到 Linux 后，`git apply` / `git am` 会看到空字节或无法识别补丁，典型表现包括：

```text
No valid patches in input
patch does not apply
file ... Unicode text, UTF-16, little-endian text
```

推荐做法：

```powershell
git format-patch -1 --stdout HEAD | Set-Content -LiteralPath fix.patch -Encoding utf8
```

或直接跳过 patch，使用 `scp` 上传改动后的具体文件，再在服务器上跑测试确认。

如果已经把 UTF-16 patch 上传到 Linux，可临时转码：

```bash
iconv -f UTF-16LE -t UTF-8 fix.patch > fix.utf8.patch
git apply --check fix.utf8.patch
git apply fix.utf8.patch
```

但如果服务器工作树与本地 commit 上下文不一致，patch 仍可能无法应用；这时优先上传具体文件覆盖，再跑定向测试。

## Hermes Telegram Gateway 假活

现象：

```text
systemctl is-active hermes-gateway
-> active

但 Telegram 群里 @ bot 没有回复。
```

常见原因不是 MCP 工具或业务代码坏了，而是 Hermes Gateway 进程仍在，但 Telegram long polling 已经因为网络/代理异常中断或卡死。此时 systemd 只看到主进程还活着，不代表 Telegram polling 正常。

排查顺序：

1. 看服务状态和最近日志：

```bash
systemctl is-active hermes-gateway weibo-ops-fastapi mihomo
journalctl -u hermes-gateway -n 160 --no-pager -o short-iso
```

重点搜索：

```text
telegram.error.NetworkError
httpx.ConnectError
Telegram polling retry failed
```

2. 查 Telegram 是否有未消费 update：

```bash
sudo -u weiboops sh -lc 'set -a; . /home/weiboops/.hermes/.env; set +a; curl -sS -x "$TELEGRAM_PROXY" --max-time 20 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"'
```

只看 `pending_update_count` 和 `last_error_message`，不要输出 token。

3. 查 Telegram 代理链路：

```bash
curl -x http://127.0.0.1:7890 -I --max-time 20 https://api.telegram.org
```

如果 `pending_update_count > 0`，而 Hermes 日志在用户 @ 的时间窗没有处理记录，通常说明 Gateway 没有正常拉取 update。

临时修复：

```bash
systemctl restart hermes-gateway
```

重启后再次检查 `pending_update_count` 是否下降，以及 Hermes MCP 是否仍可连接：

```bash
sudo -u weiboops env PATH=/home/weiboops/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HERMES_HOME=/home/weiboops/.hermes /home/weiboops/.local/bin/hermes mcp test hotcomment_ai
```

后续建议：

- 增加轻量健康检查：定期检查 Telegram `pending_update_count`、最近 gateway 日志和代理连通性。
- 如果 pending 持续堆积或连续出现 `Telegram polling retry failed`，自动重启 `hermes-gateway`。
- 不要只依赖 `systemctl active` 判断 Telegram 入口是否健康。

## Hermes cron 存档不等于 Telegram 实际消息

现象：

```text
~/.hermes/cron/output/<job_id>/<time>.md
```

文件中包含 `## Prompt`，甚至包含完整 skill 内容，看起来像把流程说明也发出去了。

实际判断要分开：

- `cron/output` 是完整运行存档，会保留 prompt、skill 注入和结果。
- Telegram 是否成功要看 `hermes cron list` 里的 `Delivery failed`。
- 最终可读结果通常在 `## Result` 后面，不要把 `## Prompt` 误判成推送正文。

如果 Telegram 推送超时：

1. 先看 `hermes cron list` 是否 `Last run ... ok`。
2. 再看是否有 `Delivery failed: Telegram send failed: Timed out`。
3. 检查最新 output 文件大小和 `## Result` 内容是否过长。
4. 检查 `journalctl -u hermes-gateway` 中的 Telegram 网络和代理错误。

修复方向：

- 在 Hermes skill 中加入硬性输出约束。
- 在具体 cron job prompt 中再次约束总字数、话题数量和输出模板。
- 禁止最终回复复述 skill、系统提示、工具日志、JSON 或 MCP 原始输出。

## 摘要型来源没有 URL

现象：

```text
GenerationContextRequest
research_sources.0.url
Field required
```

常见原因：微博智搜、人工整理笔记或平台智能摘要是摘要型来源，不一定有单条 URL。如果 schema 强制所有 `ResearchSource` 都必须有 URL，Hermes 在把摘要作为背景传给 `build_generation_context` 时会失败。

处理原则：

- `ResearchSource.url` 允许为空字符串。
- `source_urls` 只记录非空 URL。
- 摘要型来源仍要记录 `title`、`domain/source_type`、`summary`、`credibility`。
- 最终文本标注来源类型，避免把无 URL 摘要伪装成网页引用。

## Codex 额度：默认跑定向测试

现象：

```text
Codex 额度消耗明显变快。
```

常见原因不是单次代码修改本身，而是同一轮里反复执行大输出命令、全量测试、服务器日志读取、部署验证和长上下文讨论。全量测试虽然可靠，但每次都会产生额外命令、输出和上下文消耗。

处理原则：

- 默认只跑与本次改动相关的定向测试。
- 大范围重构、核心链路修改、依赖升级、发布/部署前验证，或用户明确要求时，再跑全量测试。
- 全量测试命令仍保留为：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

推荐节奏：

```text
小改动
-> rg/静态检查
-> 相关测试文件
-> 必要时 dry-run

大改动或发布前
-> 相关测试
-> 全量测试
-> 部署验证
```

同时避免无边界输出：

- 不用 `Get-ChildItem -Recurse` 扫全仓库；优先 `rg --files`。
- 日志默认 `tail -40` 或按时间窗过滤。
- 服务器验证只看关键状态，不 dump 大段日志。

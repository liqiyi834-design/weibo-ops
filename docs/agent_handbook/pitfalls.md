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

用户可能更新根目录总纲。若出现新版本，先查找：

```powershell
Get-ChildItem -Path E:\work\lqy -Filter '*微博热点人格化锐评AI项目技术框架及实现路径*.md'
```

主文档应保留/更新为：

```text
微博热点人格化锐评AI项目技术框架及实现路径_MCP自动化更新版.md
```

再同步：

```text
docs/HotComment-AI技术方案.md
AGENTS.md
docs/agent_handbook/*.md
```

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

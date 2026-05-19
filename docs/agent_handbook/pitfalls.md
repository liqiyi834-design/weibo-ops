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

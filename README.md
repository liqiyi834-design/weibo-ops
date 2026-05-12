# 微博发文系统

这是一个面向“博学、紧跟热搜、风趣犀利但理性像真人”的微博账号工作台。每天按下面流程走，目标是稳定产出 10 条以上可发布微博。

## AI 项目方案

本仓库已纳入 HotComment-AI 项目方案，用于把现有微博运营资料升级为“热点输入 + 知识库检索 + 人格化锐评生成 + 风险审查”的 AI 内容生产系统。

- `docs\HotComment-AI技术方案.md`：完整技术框架、MVP 边界、模块设计、API 设计、数据模型和 Codex 分阶段开发任务
- `docs\README.md`：项目文档索引，以及现有运营资料如何转成 AI 系统的知识库、Prompt 和安全规则

当前建议路线：先保留现有人工运营流程，同时把 `04_人设与风格规则.md`、`06_草稿生成提示词.md`、`10_爆款博文写作公式.md`、`12_事实核查与风险分级.md` 等资料整理为后续 AI MVP 的核心输入。

## HotComment-AI MVP 启动

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

配置真实模型 API：

```powershell
Copy-Item .env.example .env
```

然后在 `.env` 中填写：

```text
OPENAI_API_KEY=你的API Key
OPENAI_MODEL=gpt-4o-mini
```

如果使用 OpenAI-compatible 服务，可以额外填写：

```text
OPENAI_BASE_URL=https://你的兼容接口地址/v1
OPENAI_MODEL=对应模型名
```

启动服务：

```powershell
python -m uvicorn app.main:app --reload
```

健康检查：

```text
GET http://127.0.0.1:8000/health
```

生成接口：

```text
POST http://127.0.0.1:8000/api/comment/generate
```

示例请求：

```json
{
  "topic": "某品牌母亲节文案翻车",
  "persona": "pr_critic",
  "emotion_level": 7,
  "use_rag": true,
  "context_text": "这里粘贴已核实背景材料。"
}
```

不配置 `OPENAI_API_KEY` 时，系统会自动使用 `MockLLMClient` 跑通链路，方便本地测试。

重建本地 RAG 索引：

```text
POST http://127.0.0.1:8000/api/knowledge/rebuild
```

当前会索引 `app/knowledge/` 以及仓库中已沉淀的重点运营文档，包括人设规则、草稿提示词、爆款公式、事实核查规则和高互动样本分析。默认使用本地 hash embedding，不依赖外部 embedding API；如需使用 OpenAI-compatible embedding，将 `.env` 中的 `USE_OPENAI_EMBEDDINGS` 改为 `true`。

搜索本地 RAG 知识库：

```text
POST http://127.0.0.1:8000/api/knowledge/search
```

示例请求：

```json
{
  "query": "品牌文案翻车如何安全锐评",
  "top_k": 5
}
```

## MCP 工具服务

本仓库也提供 MCP 工具服务，方便 Codex、Claude Desktop、Cursor 等 Agent 客户端直接调用核心能力。

启动：

```powershell
python -m mcp_server.server
```

当前工具：

- `get_hot_topics`：获取微博热搜，失败时 fallback 到 mock 热点
- `generate_comment`：生成微博锐评草稿，返回事实摘要、RAG 检索、观点、人格化输出和安全审查
- `rebuild_knowledge`：重建本地 RAG 索引
- `search_knowledge`：搜索本地知识库

MCP 服务内部复用 `app/services`，FastAPI 和 MCP 共用同一套生成、RAG 和安全审查逻辑。

微博热搜接口：

```text
GET http://127.0.0.1:8000/api/hot/weibo?limit=20
```

当前热搜来源 fallback 链：

```text
WEIBO_COOKIE 登录态网页热搜
-> Edge 可见页面采集 JSON
-> mock 热点
```

微博移动 API 和无 Cookie 网页 HTML 方案不稳定，当前已不作为热搜来源。真实热搜优先使用本地 `.env` 中的 `WEIBO_COOKIE` 请求 `s.weibo.com/top/summary`；如果 Cookie 缺失或失效，会自动尝试 Edge 可见采集 JSON，再失败则返回 mock 热点。

Cookie 配置只放本地 `.env`，不要提交：

```text
WEIBO_COOKIE=你的微博网页 Cookie
```

如果要用已登录 Edge 页面辅助采集：

1. 用 Edge 打开微博热搜或话题页。
2. 手动滚动，让要采集的内容出现在页面里。
3. 打开开发者工具 Console。
4. 粘贴运行 `tools\weibo_visible_capture.js`。
5. 把下载的 JSON 放入 `samples\inbox\`。
6. 再调用 `GET /api/hot/weibo?limit=20`。

该方式只读取你当前页面可见文字，不读取 Cookie、密码、验证码、私信或浏览器历史。

## 每日流程

1. 打开微博热搜，记录 15-30 个候选热点到 `01_热搜追踪模板.md`。
2. 从候选热点里挑 10-15 个，填入 `02_选题库.csv`。
3. 用 `03_每日十条草稿模板.md` 逐条写草稿。
4. 对照 `04_人设与风格规则.md` 做一轮润色。
5. 最后用 `05_发布复盘.md` 记录发布时间、互动数据和下次优化点。
6. 把同类热点写入 `data\news_history.csv`，运行 `tools\Get-HotPriority.ps1` 找出优先制作的高热度新闻。

## 快速生成每日草稿

在 PowerShell 里运行：

```powershell
.\tools\New-DailyWeibo.ps1
```

它会在 `daily\` 目录下生成当天的草稿文件，例如：

```text
daily\2026-05-08-10-weibo-drafts.md
```

## 内容节奏建议

每天 10 条可以按这个结构分配：

- 3 条：实时热搜快评
- 2 条：热点背景科普
- 2 条：犀利观点/反常识角度
- 1 条：幽默吐槽
- 1 条：长文预告或深度拆解
- 1 条：互动提问/投票引导

核心原则：快，但不要乱；犀利，但不失真；幽默，但不油腻。

## 热点优先级算法

运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\Get-HotPriority.ps1
```

系统会读取 `data\news_history.csv`，按 1 天、3 天、7 天、15 天、30 天、90 天、180 天、365 天内同类新闻复现次数打分，并输出：

```text
output\hot_priority_2026-05-08.csv
```

优先制作 `level` 为 `S` 或 `A` 的新闻。

## 爆款研究与评论区

- `08_高热博文公开样本研究.md`：公开高热博文写法拆解
- `09_评论区互动SOP.md`：发布后如何拉评论、接评论、控节奏
- `10_爆款博文写作公式.md`：社会、科技、娱乐、科普等模板公式
- `data\public_weibo_research_samples.csv`：公开样本来源与可复制点

## 运营前置条件

- `11_自媒体前置条件清单.md`：账号边界、发布节奏、复盘制度
- `12_事实核查与风险分级.md`：事实核查、来源等级、风险表达
- `13_账号运营周计划.md`：每日、每周、每月运营动作
- `14_发布排期.csv`：每天 10 条微博的排期表
- `15_素材来源与引用规范.md`：配图、截图、引用规范
- `16_增长指标看板.csv`：粉丝、阅读、互动数据记录
- `17_内容栏目设计.md`：固定栏目和标签池
- `18_账号视觉与主页装修.md`：昵称、简介、头像、置顶微博、背景图
- `19_每日执行清单.md`：每天从热搜到复盘的完整步骤
- `20_运营交接与权限清单.md`：我和你分别负责什么、需要什么权限
- `21_运营控制台.md`：每天运营的总控面板
- `22_Edge微博样本采集助手.md`：用已登录 Edge 安全导出可见微博样本
- `23_Telegram拉取说明.md`：只保留 Telegram 消息手动拉取能力
- `24_高互动正文分析标准.md`：围绕正文、日期、转评赞分析高互动样本
- `data\weibo_post_samples.csv`：高互动博文正文样本库
- `tools\Analyze-WeiboSamples.ps1`：按互动分分析样本
- `data\source_log.csv`：事实来源留档
- `data\risk_register.csv`：高风险选题登记

# 微博热点人格化锐评 AI 项目技术框架及实现路径

> 文档用途：  
> 本文档用于指导 Codex / AI Agent / 开发者完成一个“微博热点人格化锐评 AI”项目。  
> 项目目标是构建一个能够采集微博热点、结合本地知识库、生成具有真人表达风格的锐评内容的 AI 内容生产系统。

---

## 1. 项目概述

### 1.1 项目名称

**HotComment-AI：微博热点人格化锐评生成系统**

### 1.2 项目定位

本项目不是一个普通的新闻摘要工具，也不是简单的 AI 文案生成器，而是一个结合热点采集、事实整理、知识库检索、人格化表达和风险审查的内容生成系统。

系统需要具备以下能力：

1. 获取微博热搜或用户输入的话题。
2. 搜集与话题相关的背景信息。
3. 对事件进行事实摘要。
4. 从本地知识库中检索相关案例、观点、话术和舆论分析模型。
5. 生成具有明确立场、情绪和表达风格的锐评内容。
6. 在输出前进行安全与事实风险审查。
7. 支持多种人格风格，例如毒舌公关观察者、暴躁网友、冷笑知识分子、阴阳怪气型评论者等。

### 1.3 核心目标

项目最终应实现：

```text
微博热点 / 用户输入话题
        ↓
热点采集与背景搜索
        ↓
事实整理
        ↓
知识库检索
        ↓
观点生成
        ↓
人格化改写
        ↓
风险审查
        ↓
输出可发布的锐评内容
```

### 1.4 项目核心原则

本项目的核心原则是：

> 事实要稳，观点要狠，表达要像人，边界要守住。

也就是说：

- 事实层必须保守，不能编造。
- 观点层可以尖锐，可以有立场。
- 表达层要尽量像真实互联网用户，而不是 AI 公文。
- 风险层必须拦截造谣、人身攻击、隐私泄露、歧视表达和违法内容。

---

## 2. 系统整体架构

### 2.1 总体架构图

```text
┌────────────────────────────┐
│ 用户 / 定时任务 / Codex Agent │
│  输入话题 / 抓热搜 / 调工具    │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│       Hot Search Service    │
│       热点采集模块           │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│       Context Collector     │
│       背景资料收集模块        │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│       Fact Summarizer       │
│       事实摘要模块           │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│       Topic Classifier      │
│       话题分类与风险策略模块   │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│       RAG Retriever         │
│       知识库检索模块          │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│       Opinion Generator     │
│       观点生成模块           │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│       Persona Rewriter      │
│       人格化改写模块          │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│       Safety Checker        │
│       风险审查模块           │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│       Final Output          │
│       最终锐评内容           │
└────────────────────────────┘
```

### 2.2 推荐技术栈

#### MVP 版本

适合快速原型开发。

| 模块 | 推荐方案 |
|---|---|
| 语言 | Python 3.11+ |
| Web 框架 | FastAPI |
| 前端 | Streamlit 或 Vue3 |
| 向量数据库 | Chroma |
| 本地数据库 | SQLite |
| 大模型接口 | OpenAI / DeepSeek / Qwen / Claude |
| 知识库格式 | Markdown / TXT / JSON |
| 定时任务 | APScheduler |
| 环境管理 | uv / pip / poetry |
| 部署 | Docker |

#### 进阶版本

适合后续扩展成完整产品。

| 模块 | 推荐方案 |
|---|---|
| 前端 | Vue3 + Element Plus |
| 后端 | FastAPI |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 向量数据库 | Qdrant / Milvus |
| 任务队列 | Celery + Redis |
| 模型服务 | 多模型适配层 |
| 部署 | Docker Compose / Kubernetes |
| 日志监控 | Loguru + Prometheus + Grafana |

### 2.3 MVP 优先选择

建议第一版不要做太复杂，优先使用：

```text
Python + FastAPI + Streamlit + SQLite + Chroma + 大模型 API
```

理由：

1. 开发速度快。
2. 便于调试 Prompt。
3. 容易接入本地 Markdown 知识库。
4. 适合 Codex 逐步生成代码。
5. 后续可以平滑迁移到 Vue + FastAPI + Qdrant 架构。

---

## 3. 项目功能范围

## 3A. 现实工程实现路径与 GitHub 参考方案

> 本节根据现实开源项目的常见实现方式，对本项目的落地路线进行补充。  
> 核心判断：本项目不应该从“自动发布微博评论机器人”开始，而应该从“热点输入 + 知识库检索 + 人格化锐评草稿生成 + 安全审查”的内容生产工具开始。

---

### 3A.1 现实中通常不是从零训练模型

本项目的现实实现路径通常不是：

```text
收集大量微博评论
↓
训练一个专门会锐评的模型
↓
自动评论微博
```

原因：

1. 训练成本高。
2. 数据质量难控。
3. 微博评论数据涉及合规问题。
4. 自动发布容易引发平台规则和舆论操控风险。
5. 微调无法解决实时事实更新问题。
6. 微调模型也仍然需要安全审查。

更现实的路线是：

```text
热点采集 / 用户输入
↓
事实摘要
↓
知识库 RAG 检索
↓
观点生成
↓
人格化 Prompt 改写
↓
安全审查
↓
人工审核发布
```

也就是说，本项目的第一目标不是“自动发微博”，而是“生成可审核、可编辑、可追溯依据的锐评草稿”。

---

### 3A.2 推荐现实路线：四阶段推进

#### 阶段一：本地 MVP，不接真实微博爬虫

第一阶段只做：

```text
用户输入话题
用户粘贴背景材料
读取本地 Markdown 知识库
生成事实摘要
检索相关知识
生成观点草稿
人格化改写
规则版安全审查
输出多版本锐评
```

第一阶段不要做：

```text
真实微博爬虫
自动发微博
评论区采集
多平台舆情分析
复杂 Agent 调度
```

原因：

1. 先验证生成链路是否成立。
2. 降低反爬和平台规则风险。
3. 方便 Codex 快速完成可运行版本。
4. 便于后续替换 Mock 模块为真实模块。

#### 阶段二：接入微博热搜来源

第二阶段只接热搜榜，不做自动发评。

```text
GET /api/hot/weibo
↓
返回热搜列表
↓
用户点击某个热搜
↓
进入生成页面
↓
生成锐评草稿
```

这一阶段可以参考以下 GitHub 项目：

| 仓库 | 用途 | 可借鉴内容 |
|---|---|---|
| `justjavac/weibo-trending-hot-search` | 微博热搜历史记录 | 每小时抓取、按天归档、历史热搜数据组织 |
| `arandomguyhere/weibo-daily-hot-search` | 微博热搜趋势追踪 | 5 分钟级抓取、生命周期、热度速度分析 |
| `RusianHu/weibo_hotsearch_mcp` | 微博热搜 MCP 工具 | 将热搜封装成 AI Agent 可调用工具 |
| `hellodk34/weibo_hot_search` | 热搜推送系统 | 定时任务、数据库存储、推送链路 |

#### 阶段三：加入热点分类和风险策略

第三阶段让系统自动判断热点类型。

```text
微博热搜
↓
TopicClassifier
↓
判断类型
↓
推荐人格
↓
限制最大情绪强度
↓
决定是否允许锐评
```

建议分类：

```text
brand_pr             品牌公关
entertainment        娱乐八卦
gender_issue         性别议题
social_issue         社会议题
crime_case           刑事案件
disaster             灾难事故
minor_related        未成年人相关
political_sensitive  政治敏感
unknown              未知
```

策略示例：

| 类型 | 是否允许情绪化锐评 | 推荐人格 | 最大情绪强度 |
|---|---|---|---|
| brand_pr | 是 | pr_critic | 9 |
| entertainment | 谨慎允许 | ironic_observer | 7 |
| gender_issue | 允许，但需克制 | rational_critic | 7 |
| social_issue | 允许，但需事实限定 | rational_critic | 6 |
| crime_case | 不建议 | rational_critic | 3 |
| disaster | 不允许玩梗 | rational_critic | 2 |
| minor_related | 不允许攻击 | rational_critic | 2 |
| political_sensitive | 高度谨慎 | rational_critic | 2 |
| unknown | 默认克制 | rational_critic | 5 |

#### 阶段四：做成 AI Agent 工具链

第四阶段才考虑 MCP / Agent 化。

```text
Codex / Claude / Cursor / 其他 Agent
↓
调用 hot_search_tool
↓
调用 context_collector
↓
调用 knowledge_retriever
↓
调用 comment_generator
↓
调用 safety_checker
↓
返回可审核草稿
```

此时项目不只是一个 Web 应用，而是一个“热点评论 Agent 工具链”。

---

### 3A.3 GitHub 参考仓库矩阵

以下仓库不是让项目直接照抄，而是用于拆分参考。

#### 微博热搜采集类

| 仓库 | 地址 | 说明 | 本项目借鉴点 |
|---|---|---|---|
| `justjavac/weibo-trending-hot-search` | `https://github.com/justjavac/weibo-trending-hot-search` | 微博热搜榜历史记录项目，从 2020-11-24 开始记录，每小时抓取一次并按天归档。 | 热搜历史归档、定时抓取、数据组织方式 |
| `arandomguyhere/weibo-daily-hot-search` | `https://github.com/arandomguyhere/weibo-daily-hot-search` | 轻量 Deno 微博趋势抓取项目，约 5 分钟抓取一次，支持生命周期和速度分析。 | 热点生命周期、RISING/HOT/FALLING 等状态判断 |
| `RusianHu/weibo_hotsearch_mcp` | `https://github.com/RusianHu/weibo_hotsearch_mcp` | 基于 fastmcp 的微博热搜 MCP 服务，可被 Claude 等 AI 助手调用。 | MCP 工具封装、Agent 可调用接口 |
| `hellodk34/weibo_hot_search` | `https://github.com/hellodk34/weibo_hot_search` | 微博热搜实时推送项目，使用 Spring Boot、MySQL 等。 | 定时任务、数据库存储、推送链路 |

#### 热搜分析与过滤类

| 仓库 | 地址 | 说明 | 本项目借鉴点 |
|---|---|---|---|
| `17fx/weibo-hotsearch-analyse` | `https://github.com/17fx/weibo-hotsearch-analyse` | 微博热搜历史记录分析项目，使用 NLP 对热搜进行分类。 | 热点分类、文本标签化、舆情类型判断 |
| `festoney8/Weibo-Hot-No-Shit` | `https://github.com/festoney8/Weibo-Hot-No-Shit` | 微博热搜净化脚本，支持关键词和正则过滤。 | 热搜过滤、关键词黑白名单、无价值话题剔除 |

#### RAG 知识库类

| 仓库 | 地址 | 说明 | 本项目借鉴点 |
|---|---|---|---|
| `javcanti/ContextAgent` | `https://github.com/javcanti/ContextAgent` | 基于 FastAPI、LangChain、OpenAI Embeddings、ChromaDB 的文档问答后端。 | FastAPI + Chroma + RAG 后端结构 |
| `notadev-iamaura/OneRAG` | `https://github.com/notadev-iamaura/OneRAG` | 生产级 RAG 框架，支持多向量库和多模型切换。 | 多模型适配、多向量库适配、工程化结构 |

#### 舆情监控与多 Agent 类

| 仓库 | 地址 | 说明 | 本项目借鉴点 |
|---|---|---|---|
| `sansan0/TrendRadar` | `https://github.com/sansan0/TrendRadar` | AI 驱动的舆情与趋势监控项目，支持多平台聚合、RSS、智能提醒和 MCP。 | 热点聚合、AI 筛选、推送机制 |
| `666ghj/MindSpider` | `https://github.com/666ghj/MindSpider` | 基于 Agent 的智能舆情爬虫系统，先识别热点，再多平台深度爬取。 | Search Agent + 深度爬虫的两阶段思路 |
| `666ghj/BettaFish` | `https://github.com/666ghj/BettaFish` | 多 Agent 舆情分析系统，覆盖多个社交平台和评论数据。 | 多 Agent 舆情分析、高级产品形态 |

#### 个性化微博与自动化类

| 仓库 | 地址 | 说明 | 本项目借鉴点 |
|---|---|---|---|
| `QuestNova502/weibo-autopilot-generator` | `https://github.com/QuestNova502/weibo-autopilot-generator` | 为 Claude Code 打造的微博自动化 Skill 生成器，支持风格学习、自动评论和自动转发。 | 个性化风格、Skill 化、AI Agent 工作流 |

---

### 3A.4 本项目与参考项目的关系

本项目不是单纯复刻任何一个仓库，而是组合多个方向：

```text
微博热搜来源：
justjavac/weibo-trending-hot-search
arandomguyhere/weibo-daily-hot-search
RusianHu/weibo_hotsearch_mcp

RAG 知识库：
ContextAgent
OneRAG

舆情分析高级形态：
TrendRadar
MindSpider
BettaFish

个性化评论与 Agent 化：
weibo-autopilot-generator
```

组合后的本项目形态：

```text
HotComment-AI
= 热点输入
+ 热点筛选
+ 事实摘要
+ 本地知识库
+ RAG 检索
+ 观点生成
+ 人格化改写
+ 安全审查
+ 人工审核
```

---

### 3A.5 与开源项目相比，本项目的差异化

多数微博热搜项目只解决：

```text
抓取热搜
保存热搜
推送热搜
分析热搜分类
```

多数 RAG 项目只解决：

```text
上传文档
检索知识
回答问题
```

多数 AI 舆情项目更偏：

```text
舆情报告
情绪分析
趋势监控
评论采集
```

本项目的差异化在于：

```text
不是回答问题，而是生成有立场的评论。
不是单纯抓热点，而是判断热点是否值得锐评。
不是追求绝对中立，而是构建受事实约束的人格化表达。
不是自动操控舆论，而是辅助人类生成可审核草稿。
```

---

### 3A.6 现实工程优先级

#### P0：必须先做

```text
1. 输入话题
2. 输入背景材料
3. 读取本地知识库
4. 生成事实摘要
5. 检索相关知识
6. 生成观点草稿
7. 人格化改写
8. 安全审查
9. 输出多版本文案
```

P0 的目标是：

```text
不依赖真实微博。
不依赖复杂爬虫。
不依赖自动发布。
只要输入话题和背景，就能生成稳定草稿。
```

#### P1：第二优先级

```text
1. 微博热搜 Mock Provider
2. 微博热搜真实 Provider
3. 人格模板管理
4. 知识库重建接口
5. 生成历史记录
6. Streamlit 前端
```

#### P2：第三优先级

```text
1. 热点生命周期判断
2. 自动定时采集
3. 热点分类
4. 情绪倾向分析
5. 舆情摘要
6. 推荐人格与最大情绪强度
```

#### P3：最后再考虑

```text
1. 自动发布
2. 多账号运营
3. 自动评论区互动
4. 评论区大规模采集
5. 多 Agent 舆情分析
6. Kubernetes 微服务部署
```

---

### 3A.7 新增模块：TopicClassifier

在原架构基础上，建议新增一个话题分类模块。

文件：

```text
app/services/topic_classifier.py
```

职责：

1. 判断热点类型。
2. 判断是否适合情绪化锐评。
3. 推荐人格模板。
4. 限制最大情绪强度。
5. 标记风险等级。

输入：

```json
{
  "topic": "某品牌母亲节文案争议",
  "fact_summary": {},
  "context_text": ""
}
```

输出：

```json
{
  "topic_type": "brand_pr",
  "risk_level": "medium",
  "recommended_persona": "pr_critic",
  "allow_emotional_comment": true,
  "max_emotion_level": 9,
  "reason": "该话题主要涉及品牌公关和广告表达争议，允许较强情绪批评，但应避免无证据指控。"
}
```

对应 Pydantic 模型：

```python
class TopicClassification(BaseModel):
    topic_type: Literal[
        "brand_pr",
        "entertainment",
        "gender_issue",
        "social_issue",
        "crime_case",
        "disaster",
        "minor_related",
        "political_sensitive",
        "unknown",
    ]
    risk_level: Literal["low", "medium", "high", "blocked"]
    recommended_persona: str
    allow_emotional_comment: bool
    max_emotion_level: int
    reason: str
```

生成链路应更新为：

```text
输入话题 / 热搜
↓
ContextCollector
↓
FactSummarizer
↓
TopicClassifier
↓
RAGRetriever
↓
OpinionGenerator
↓
PersonaRewriter
↓
SafetyChecker
↓
FinalOutput
```

---

### 3A.8 新增模块：HotSearchProvider 抽象层

不要让系统直接耦合某个微博接口。应设计 provider 抽象层。

目录建议：

```text
app/hot_sources/
├── __init__.py
├── base.py
├── mock_provider.py
├── weibo_mobile_provider.py
├── github_archive_provider.py
└── provider_factory.py
```

基础接口：

```python
class BaseHotSearchProvider(Protocol):
    def get_hot_topics(self, limit: int = 20) -> list[HotTopic]:
        ...
```

第一版实现：

```text
MockHotSearchProvider
```

第二版实现：

```text
WeiboMobileHotSearchProvider
```

第三版实现：

```text
GitHubArchiveHotSearchProvider
```

设计原则：

1. 外部接口失败时 fallback 到 mock。
2. 所有请求必须设置 timeout。
3. 返回统一 HotTopic schema。
4. 不要在业务代码里写死微博接口。
5. 不要在第一版做复杂登录态爬虫。

---

### 3A.9 新增模块：HotTopicLifecycleTracker

如果后期要做热点生命周期，可以新增：

文件：

```text
app/services/hot_topic_lifecycle_tracker.py
```

职责：

1. 记录话题首次出现时间。
2. 记录话题最后出现时间。
3. 计算排名变化。
4. 计算热度变化速度。
5. 判断话题状态。

状态枚举：

```text
NEW       新出现
RISING    正在上升
HOT       高热稳定
FALLING   正在下降
GONE      已消失
REVIVED   二次升温
```

数据模型：

```python
class HotTopicLifecycle(BaseModel):
    keyword: str
    first_seen_at: datetime
    last_seen_at: datetime
    current_rank: int | None
    previous_rank: int | None
    velocity: float | None
    status: Literal["NEW", "RISING", "HOT", "FALLING", "GONE", "REVIVED"]
```

生成策略：

| 状态 | 生成策略 |
|---|---|
| NEW | 快速短评 |
| RISING | 情绪化锐评 |
| HOT | 长短结合 |
| FALLING | 复盘评论 |
| GONE | 舆情总结 |
| REVIVED | 二次争议分析 |

---

### 3A.10 更新后的 MVP 边界

更新后的 MVP 明确为：

```text
可做：
1. 用户输入话题。
2. 用户输入或粘贴背景材料。
3. 本地知识库检索。
4. 事实摘要。
5. 话题分类。
6. 观点生成。
7. 人格化锐评。
8. 安全审查。
9. Streamlit 展示。
10. FastAPI 接口。

暂不做：
1. 自动发微博。
2. 自动评论微博。
3. 大规模爬取评论区。
4. 多账号运营。
5. 自动引战型内容生成。
6. 绕过平台风控。
7. 复杂登录态微博爬虫。
```

---

### 3A.11 给 Codex 的现实分阶段任务

#### 任务 1：先实现本地 MVP

```text
请先实现 HotComment-AI 的本地 MVP。

不要接真实微博爬虫。
不要做自动发布。
不要做复杂前端。

要求：
1. FastAPI 后端。
2. Streamlit 简单前端。
3. 用户可以输入 topic 和 context_text。
4. 从 app/knowledge 读取 Markdown 知识库。
5. 使用 KeywordRetriever 检索相关知识。
6. 使用 MockLLMClient 跑通链路。
7. 实现 FactSummarizer。
8. 实现 TopicClassifier。
9. 实现 OpinionGenerator。
10. 实现 PersonaRewriter。
11. 实现 SafetyChecker。
12. 实现 GenerationPipeline。
13. 实现 POST /api/comment/generate 接口。
14. 返回完整 JSON，包括 fact_summary、topic_classification、retrieved_knowledge、opinion、output、safety。
```

验收标准：

```text
1. 不配置真实 LLM 也可以用 mock 跑通。
2. 输入任意 topic 和 context_text 能返回完整结构。
3. 所有模块都有基础测试。
4. SafetyChecker 可以识别明显高风险表达。
```

#### 任务 2：接入微博热搜 Provider

```text
请实现 HotSearchProvider 抽象层。

要求：
1. 创建 app/hot_sources。
2. 定义 BaseHotSearchProvider。
3. 实现 MockHotSearchProvider。
4. 实现 WeiboMobileHotSearchProvider，但失败时要 fallback 到 mock。
5. 所有 provider 返回统一 HotTopic schema。
6. 添加 GET /api/hot/weibo 接口。
7. 外部请求必须设置 timeout。
8. 不要实现自动发布。
```

#### 任务 3：替换为 Chroma RAG

```text
请将 KeywordRetriever 扩展为 ChromaRetriever。

要求：
1. 添加 embedding 抽象层。
2. 支持 OpenAI embedding。
3. 提供本地 fallback embedding 或保留 KeywordRetriever fallback。
4. 实现 ChromaVectorStore。
5. 实现 /api/knowledge/rebuild。
6. 支持从 app/knowledge 读取 Markdown 文档并构建索引。
7. retrieve(query, top_k) 返回 content、source、score。
8. 添加测试。
```

#### 任务 4：加入热点分类策略

```text
请完善 TopicClassifier。

要求：
1. 支持 brand_pr、entertainment、gender_issue、social_issue、crime_case、disaster、minor_related、political_sensitive、unknown。
2. 每种类型返回 recommended_persona。
3. 每种类型返回 max_emotion_level。
4. 高风险类型限制情绪化表达。
5. 将分类结果传入 PersonaRewriter 和 SafetyChecker。
```

#### 任务 5：加入生命周期追踪

```text
请实现 HotTopicLifecycleTracker。

要求：
1. 使用 SQLite 保存热搜历史。
2. 记录 first_seen_at、last_seen_at、rank、hot_value。
3. 计算 rank_delta 和 velocity。
4. 输出 NEW、RISING、HOT、FALLING、GONE、REVIVED。
5. 根据生命周期状态调整生成策略。
```

---

### 3A.12 现实风险提醒

这个项目最容易走偏的方向是：

```text
自动批量评论
自动引战
自动攻击个人
自动蹭热点造谣
绕过微博平台规则
```

因此工程上要强制设计以下约束：

1. 默认只生成草稿，不自动发布。
2. 所有输出显示风险等级。
3. 高风险话题强制降低情绪。
4. 涉及未成年人、灾难、死亡、刑事案件时禁止玩梗。
5. 不允许生成“号召大家去冲”“去骂他”等动员式内容。
6. 不允许绕过平台反爬、验证码或登录限制。
7. 不允许将未证实爆料写成事实。
8. 最终发布动作必须由人确认。

---



### 3.1 第一阶段功能

第一阶段只做最小可用版本。

必须实现：

1. 用户输入一个热点话题。
2. 系统调用搜索模块或热榜模块获取相关背景信息。
3. 系统对背景信息进行事实摘要。
4. 系统从本地知识库中检索相关材料。
5. 系统生成以下几类内容：
   - 一句话锐评
   - 微博短评版
   - 情绪拉满版
   - 理性拆解版
   - 阴阳怪气版
   - 评论区短句
6. 系统对输出内容做一次风险检查。
7. 最终在 Web 页面或 API 中返回结果。

### 3.2 第二阶段功能

第二阶段增加自动化能力。

可实现：

1. 自动抓取微博热搜榜。
2. 支持用户选择某个热搜进行评论生成。
3. 支持多种人格模板。
4. 支持知识库上传。
5. 支持生成历史记录保存。
6. 支持人工编辑和重新生成。
7. 支持输出 Markdown / TXT 格式。

### 3.3 第三阶段功能

第三阶段做成完整系统。

可实现：

1. 定时抓取热搜。
2. 自动判断热点类型。
3. 自动匹配历史案例。
4. 自动生成多版本草稿。
5. 人工审核后发布。
6. 支持团队协作。
7. 支持多模型切换。
8. 支持内容质量评分。
9. 支持爆款潜力评分。
10. 支持 Kubernetes 部署。

---


## 3B. Codex / MCP 插件化与自动化任务设计

> 本节用于补充项目的 Agent 化方向。  
> 结论：本项目适合做成 Codex / AI Agent 可调用的工具链，但不建议做成全自动发微博机器人。  
> 推荐形态是：**热点锐评草稿生成工具 + MCP 工具服务 + 自动化草稿任务 + 人工审核机制**。

---

### 3B.1 为什么适合做成 Codex / Agent 工具

本项目天然适合被 Codex、Claude Code、Cursor 或其他 AI Agent 调用，原因是它不是单次问答，而是一条可重复执行的工作流：

```text
获取热点
↓
收集背景
↓
事实摘要
↓
话题分类
↓
知识库检索
↓
观点生成
↓
人格化改写
↓
风险审查
↓
保存草稿
```

如果只做成普通网页，用户每次都需要手动点击、复制和重复输入。  
如果做成 Agent 工具，则可以让 Codex 直接调用你的项目能力，例如：

```text
请获取当前微博热搜，筛选适合品牌公关锐评的话题，生成 5 条草稿，但不要发布。
```

Agent 调用工具后可以自动完成：

```text
1. 获取热搜。
2. 过滤高风险话题。
3. 找出适合评论的话题。
4. 生成多个版本。
5. 进行安全审查。
6. 保存到草稿箱。
7. 返回待审核列表。
```

因此，本项目不只是一个 Web 应用，也可以逐步演化为一个“热点内容生产 Agent 工具链”。

---

### 3B.2 不建议做成全自动微博机器人

需要明确区分两种项目形态。

#### 推荐形态

```text
自动抓热点
自动分析
自动生成草稿
自动安全审查
自动保存草稿
人工审核发布
```

这是内容生产辅助工具。

#### 不推荐形态

```text
自动抓热点
自动锐评
自动发布微博
自动评论别人
自动转发互动
自动批量引导舆论
```

这是高风险自动化。

不推荐全自动发布的原因：

1. 微博热点信息经常不完整。
2. 自动发布容易把猜测写成事实。
3. 涉及真人、未成年人、灾难、刑事案件时风险很高。
4. 自动评论和自动转发容易被视为平台滥用。
5. 批量情绪化内容容易引发网暴或舆论操控问题。
6. 项目会从“内容辅助”滑向“自动攻击工具”。

因此，项目应强制遵守：

```text
默认只生成草稿。
默认不自动发布。
默认不自动评论。
默认不绕过平台限制。
最终发布必须由人确认。
```

---

### 3B.3 推荐三层架构

项目后期建议从单体 Web 工具升级为三层结构：

```text
第一层：业务后端
HotComment-AI FastAPI 服务

第二层：Agent 工具层
MCP Server / Codex Tool Adapter

第三层：自动化任务层
定时抓热搜、筛选话题、生成草稿、每日复盘
```

整体架构如下：

```text
┌────────────────────────────────────┐
│    Codex / Claude / Cursor / 用户    │
└──────────────────┬─────────────────┘
                   ↓
┌────────────────────────────────────┐
│          MCP Server 工具层           │
│ get_hot_topics / generate_comment   │
│ safety_check / save_draft           │
└──────────────────┬─────────────────┘
                   ↓
┌────────────────────────────────────┐
│          HotComment-AI API           │
│              FastAPI                 │
└──────────────────┬─────────────────┘
                   ↓
┌────────────────────────────────────┐
│        Generation Pipeline           │
│ FactSummarizer / TopicClassifier     │
│ RAGRetriever / PersonaRewriter       │
│ SafetyChecker                        │
└──────────────────┬─────────────────┘
                   ↓
┌────────────────────────────────────┐
│             Draft Queue              │
│           草稿箱 / 人工审核           │
└────────────────────────────────────┘
```

这种设计的好处：

1. 后端业务逻辑独立，不绑定某个 Agent 平台。
2. MCP 只是适配层，后期可以替换或扩展。
3. 自动化任务可以单独开关。
4. 所有入口都必须经过 SafetyChecker。
5. 生成结果进入草稿箱，而不是直接发布。
6. Codex 可以作为开发代理，也可以作为工具调用者。

---

### 3B.4 MCP 工具服务设计

建议新增一个独立目录：

```text
mcp_server/
```

该目录负责把 HotComment-AI 的能力暴露给 Codex / Agent。

#### MCP 工具列表

| 工具名 | 作用 | 是否允许自动调用 | 风险等级 |
|---|---|---|---|
| `get_hot_topics` | 获取微博热搜列表 | 是 | 低 |
| `classify_topic` | 判断话题类型和风险 | 是 | 低 |
| `retrieve_knowledge` | 检索本地知识库 | 是 | 低 |
| `generate_comment` | 生成锐评草稿 | 是，但必须审查 | 中 |
| `safety_check` | 检查文案风险 | 是 | 低 |
| `save_draft` | 保存草稿 | 是 | 低 |
| `list_drafts` | 查看草稿箱 | 是 | 低 |
| `daily_digest` | 生成每日热点复盘 | 是 | 中 |
| `export_draft` | 导出草稿 Markdown | 是 | 低 |
| `publish_to_weibo` | 发布到微博 | 不建议实现 | 高 |

项目第一版 MCP 不实现 `publish_to_weibo`。

---

### 3B.5 MCP 工具：get_hot_topics

作用：获取微博热搜列表。

输入：

```json
{
  "source": "weibo",
  "limit": 20,
  "include_lifecycle": true
}
```

输出：

```json
{
  "items": [
    {
      "rank": 1,
      "keyword": "某品牌文案争议",
      "hot_value": "1234567",
      "url": "",
      "status": "RISING",
      "first_seen_at": "",
      "last_seen_at": ""
    }
  ]
}
```

实现要求：

1. 第一版调用 MockHotSearchProvider。
2. 第二版调用 WeiboMobileHotSearchProvider。
3. 如果真实接口失败，fallback 到 mock 或历史缓存。
4. 不要求登录微博。
5. 不绕过验证码或平台限制。

---

### 3B.6 MCP 工具：classify_topic

作用：判断话题类型、风险等级和适合的人格。

输入：

```json
{
  "topic": "某品牌母亲节文案争议",
  "context_text": ""
}
```

输出：

```json
{
  "topic_type": "brand_pr",
  "risk_level": "medium",
  "recommended_persona": "pr_critic",
  "allow_emotional_comment": true,
  "max_emotion_level": 8,
  "reason": "该话题主要涉及品牌公关和广告表达争议，允许较强批评，但应避免无证据指控。"
}
```

实现要求：

1. 可先使用规则分类。
2. 后续可接 LLM 分类。
3. 高风险话题必须限制情绪强度。
4. 分类结果必须传给后续生成模块。

---

### 3B.7 MCP 工具：retrieve_knowledge

作用：从本地知识库中检索观点依据。

输入：

```json
{
  "query": "品牌 母亲节 文案 母职叙事 情绪营销",
  "top_k": 5
}
```

输出：

```json
{
  "results": [
    {
      "content": "品牌在母亲节营销中常见的问题是将母亲价值等同于牺牲……",
      "source": "brand_pr_cases.md",
      "score": 0.86
    }
  ]
}
```

实现要求：

1. 第一版可使用 KeywordRetriever。
2. 第二版接 Chroma。
3. 每条结果保留 source。
4. 结果只作为观点依据，不当作绝对事实。

---

### 3B.8 MCP 工具：generate_comment

作用：生成完整锐评草稿。

输入：

```json
{
  "topic": "某品牌母亲节文案争议",
  "context_text": "",
  "persona": "pr_critic",
  "emotion_level": 8,
  "output_formats": [
    "one_liner",
    "short_comment",
    "emotional_version",
    "rational_version",
    "ironic_version",
    "comment_replies"
  ],
  "save_to_draft": true
}
```

输出：

```json
{
  "topic": "某品牌母亲节文案争议",
  "fact_summary": {},
  "topic_classification": {},
  "retrieved_knowledge": [],
  "opinion": {},
  "output": {
    "one_liner": "",
    "short_comment": "",
    "emotional_version": "",
    "rational_version": "",
    "ironic_version": "",
    "comment_replies": []
  },
  "safety": {
    "is_safe": true,
    "risk_level": "medium",
    "issues": []
  },
  "draft": {
    "saved": true,
    "draft_id": "draft_20260511_0001"
  }
}
```

实现要求：

1. 必须调用完整 GenerationPipeline。
2. 必须经过 SafetyChecker。
3. 如果风险等级为 high，只保存理性版。
4. 如果风险等级为 blocked，不保存情绪版。
5. 默认不发布，只保存草稿。

---

### 3B.9 MCP 工具：safety_check

作用：单独检查某段文案是否安全。

输入：

```json
{
  "topic": "某品牌母亲节文案争议",
  "text": "这不是文案翻车，这是价值观裸奔。",
  "context_text": ""
}
```

输出：

```json
{
  "is_safe": true,
  "risk_level": "low",
  "issues": [],
  "suggestion": "",
  "revised_text": ""
}
```

检查维度：

1. 是否有未证实事实。
2. 是否有定罪式表达。
3. 是否攻击普通人。
4. 是否泄露隐私。
5. 是否包含歧视性表达。
6. 是否煽动网暴。
7. 是否涉及灾难、死亡、刑事案件、未成年人等高风险主题。

---

### 3B.10 MCP 工具：save_draft 与 list_drafts

#### save_draft

输入：

```json
{
  "topic": "某品牌母亲节文案争议",
  "content": "……",
  "persona": "pr_critic",
  "risk_level": "medium",
  "source": "mcp_generate_comment",
  "metadata": {}
}
```

输出：

```json
{
  "draft_id": "draft_20260511_0001",
  "status": "pending_review"
}
```

#### list_drafts

输入：

```json
{
  "status": "pending_review",
  "limit": 20
}
```

输出：

```json
{
  "drafts": [
    {
      "draft_id": "draft_20260511_0001",
      "topic": "某品牌母亲节文案争议",
      "persona": "pr_critic",
      "risk_level": "medium",
      "created_at": "",
      "status": "pending_review"
    }
  ]
}
```

草稿状态建议：

```text
pending_review     待审核
approved           已通过
rejected           已拒绝
needs_revision     需修改
exported           已导出
archived           已归档
```

---

### 3B.11 自动化任务设计

建议新增目录：

```text
automations/
```

自动化任务只负责“生成候选草稿”，不负责自动发布。

#### 自动化任务 1：fetch_hot_topics_job

执行频率：

```text
每 30 分钟
```

任务流程：

```text
1. 获取微博热搜 Top 50。
2. 保存到数据库。
3. 对比上一轮结果。
4. 更新生命周期状态。
5. 记录 NEW / RISING / HOT / FALLING / GONE。
```

#### 自动化任务 2：classify_hot_topics_job

执行频率：

```text
每次热搜更新后
```

任务流程：

```text
1. 读取最新热搜。
2. 调用 TopicClassifier。
3. 标记话题类型。
4. 标记风险等级。
5. 过滤不适合评论的话题。
```

过滤规则：

```text
1. 灾难死亡话题默认不生成情绪化锐评。
2. 未成年人相关话题默认不生成情绪化锐评。
3. 刑事案件默认只做理性摘要。
4. 品牌公关、消费争议、平台争议优先生成。
5. 娱乐八卦默认降低优先级。
```

#### 自动化任务 3：generate_drafts_job

执行频率：

```text
每次分类完成后，或每小时执行一次
```

任务流程：

```text
1. 读取低风险或中风险话题。
2. 按推荐人格生成草稿。
3. 控制 emotion_level 不超过 max_emotion_level。
4. 调用 SafetyChecker。
5. 保存安全草稿到 Draft Queue。
6. 高风险草稿只保留理性版。
```

#### 自动化任务 4：daily_digest_job

执行频率：

```text
每天晚上
```

任务流程：

```text
1. 汇总当日热搜。
2. 列出最高热度话题。
3. 列出最适合锐评话题。
4. 列出高风险不建议评论话题。
5. 总结新增案例。
6. 输出每日复盘 Markdown。
```

---

### 3B.12 自动化策略与安全策略

建议新增目录：

```text
automations/policies/
```

#### topic_filter_policy.py

职责：

```text
1. 判断话题是否适合生成。
2. 判断是否需要跳过。
3. 判断是否只允许理性摘要。
```

规则示例：

```python
if topic_type in ["disaster", "minor_related", "crime_case"]:
    allow_emotional_comment = False
    max_emotion_level = min(max_emotion_level, 3)
```

#### risk_policy.py

职责：

```text
1. 根据风险等级决定输出范围。
2. high 风险只保存理性版。
3. blocked 风险不保存草稿。
4. medium 风险需要人工重点审核。
```

规则示例：

```python
if risk_level == "blocked":
    return "skip"

if risk_level == "high":
    return "save_rational_only"

if risk_level == "medium":
    return "save_with_warning"

return "save_all"
```

#### draft_generation_policy.py

职责：

```text
1. 控制每轮生成数量。
2. 避免同一话题重复生成。
3. 避免过度追逐单一争议。
4. 控制每日草稿上限。
```

建议限制：

```text
每 30 分钟最多生成 3 个话题草稿。
每个话题每天最多生成 2 次。
每日最多自动生成 30 条草稿。
高风险话题不进入自动生成队列。
```

---

### 3B.13 草稿箱机制设计

草稿箱是项目从“自动生成”到“人工发布”的关键缓冲层。

建议数据表：

```sql
CREATE TABLE drafts (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    persona TEXT,
    risk_level TEXT,
    status TEXT DEFAULT 'pending_review',
    source TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

草稿字段说明：

| 字段 | 说明 |
|---|---|
| id | 草稿 ID |
| topic | 热点话题 |
| content | 草稿内容 |
| persona | 使用的人格 |
| risk_level | 风险等级 |
| status | 审核状态 |
| source | 来源，例如 mcp、automation、manual |
| metadata_json | 事实摘要、知识来源、生成参数 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

人工审核操作：

```text
approve_draft      通过
reject_draft       拒绝
revise_draft       修改
export_draft       导出
archive_draft      归档
```

第一版只需要实现：

```text
save_draft
list_drafts
update_draft_status
export_draft_to_markdown
```

---

### 3B.14 更新后的项目目录结构

在原项目结构基础上，建议新增：

```text
hot-comment-ai/
├── app/
│   ├── ...
│   └── services/
│       ├── generation_pipeline.py
│       ├── topic_classifier.py
│       ├── safety_checker.py
│       └── draft_service.py
│
├── mcp_server/
│   ├── __init__.py
│   ├── server.py
│   ├── config.py
│   ├── schemas.py
│   ├── client.py
│   └── tools/
│       ├── __init__.py
│       ├── get_hot_topics.py
│       ├── classify_topic.py
│       ├── retrieve_knowledge.py
│       ├── generate_comment.py
│       ├── safety_check.py
│       ├── save_draft.py
│       ├── list_drafts.py
│       └── daily_digest.py
│
├── automations/
│   ├── __init__.py
│   ├── scheduler.py
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── fetch_hot_topics_job.py
│   │   ├── classify_hot_topics_job.py
│   │   ├── generate_drafts_job.py
│   │   └── daily_digest_job.py
│   └── policies/
│       ├── __init__.py
│       ├── topic_filter_policy.py
│       ├── risk_policy.py
│       └── draft_generation_policy.py
│
├── drafts/
│   ├── README.md
│   └── exported/
│
└── docs/
    ├── mcp_design.md
    ├── automation_design.md
    └── draft_review_workflow.md
```

---

### 3B.15 Codex 在本项目中的角色边界

Codex 应该被定位为：

```text
开发代理 + 工具调用者 + 流程编排者
```

不应该被定位为：

```text
自动舆论操控者
```

Codex 适合做：

```text
1. 创建项目结构。
2. 编写 FastAPI 接口。
3. 编写 MCP server。
4. 编写自动化任务。
5. 编写测试。
6. 调试 Prompt。
7. 整理知识库。
8. 重构生成流水线。
9. 生成草稿。
10. 保存草稿。
```

Codex 不应该做：

```text
1. 自动发布微博。
2. 自动评论他人微博。
3. 自动追踪普通人。
4. 自动组织攻击。
5. 绕过平台限制。
6. 批量制造争议。
```

---

### 3B.16 给 Codex 的新增任务：实现 MCP Server

```text
请为 HotComment-AI 新增 MCP Server 支持。

要求：
1. 创建 mcp_server 目录。
2. 实现 MCP server 基础入口 server.py。
3. MCP 工具通过调用 FastAPI 服务或内部 service 实现。
4. 第一版实现以下工具：
   - get_hot_topics
   - classify_topic
   - retrieve_knowledge
   - generate_comment
   - safety_check
   - save_draft
   - list_drafts
5. 不实现 publish_to_weibo。
6. 所有生成类工具必须返回 safety 信息。
7. generate_comment 默认 save_to_draft=true。
8. blocked 风险不保存草稿。
9. high 风险只保存 rational_version。
10. 添加基础测试和 README。
```

验收标准：

```text
1. MCP server 可以本地启动。
2. Codex / MCP client 可以发现工具列表。
3. 调用 generate_comment 能返回完整结构。
4. 调用 save_draft 能保存草稿。
5. 调用 list_drafts 能查看草稿。
6. 不存在自动发布能力。
```

---

### 3B.17 给 Codex 的新增任务：实现自动化草稿系统

```text
请为 HotComment-AI 新增自动化草稿系统。

要求：
1. 创建 automations 目录。
2. 使用 APScheduler 实现本地定时任务。
3. 实现 fetch_hot_topics_job。
4. 实现 classify_hot_topics_job。
5. 实现 generate_drafts_job。
6. 实现 daily_digest_job。
7. 自动化任务只保存草稿，不发布。
8. 添加 topic_filter_policy、risk_policy、draft_generation_policy。
9. 每个任务都要有日志。
10. 每个任务失败时不能影响主服务。
```

验收标准：

```text
1. 可以手动触发每个 job。
2. 可以配置定时频率。
3. 热搜能保存到数据库。
4. 合适的话题能生成草稿。
5. 高风险话题不会生成情绪化草稿。
6. 每日复盘可以导出 Markdown。
```

---

### 3B.18 给 Codex 的新增任务：实现草稿箱

```text
请为 HotComment-AI 实现 DraftService。

要求：
1. 使用 SQLite 保存草稿。
2. 实现 Draft 数据模型。
3. 实现 save_draft。
4. 实现 list_drafts。
5. 实现 get_draft。
6. 实现 update_draft_status。
7. 实现 export_draft_to_markdown。
8. 草稿必须保存 topic、content、persona、risk_level、status、source、metadata。
9. 默认状态为 pending_review。
10. 不实现自动发布。
```

验收标准：

```text
1. 可以保存草稿。
2. 可以查看草稿列表。
3. 可以更新审核状态。
4. 可以导出 Markdown。
5. generate_comment 可以选择保存到草稿箱。
```

---

### 3B.19 推荐最终演进路线

综合前文，本项目最终演进路线建议为：

```text
阶段 1：本地 MVP
FastAPI + Streamlit + MockLLM + KeywordRetriever + SafetyChecker

阶段 2：RAG 增强
Chroma + Markdown 知识库 + Embedding + /knowledge/rebuild

阶段 3：微博热搜接入
HotSearchProvider + Mock Provider + Weibo Provider + 热点缓存

阶段 4：TopicClassifier
话题分类 + 风险策略 + 推荐人格 + 情绪上限

阶段 5：MCP 工具化
mcp_server + get_hot_topics + generate_comment + save_draft

阶段 6：自动化草稿
APScheduler + 热搜定时抓取 + 自动分类 + 自动生成草稿

阶段 7：审核工作台
草稿箱 + 审核状态 + 导出 Markdown + 人工确认

阶段 8：高级舆情
生命周期追踪 + 每日复盘 + 案例沉淀 + 多平台扩展
```

---

### 3B.20 本节结论

本项目做成 Codex / Agent 插件化工具是正确方向，但正确边界是：

```text
让 Agent 帮你抓热点、筛话题、生成草稿、做安全审查、保存草稿。
```

不是：

```text
让 Agent 自动发微博、自动评论、自动引战。
```

最终推荐产品形态：

```text
HotComment-AI
= FastAPI 业务后端
+ RAG 知识库
+ 人格化生成器
+ SafetyChecker
+ MCP 工具服务
+ 自动化草稿任务
+ 草稿箱与人工审核
```

一句话总结：

> 这个项目最适合做成“Codex / MCP 可调用的热点锐评草稿生成工具”，再配一套自动化任务，让系统自动发现热点和生成候选草稿，但最终发布权始终留在人手里。


## 4. 目录结构设计

推荐项目目录如下：

```text
hot-comment-ai/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_comment.py
│   │   ├── routes_hot.py
│   │   └── routes_knowledge.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── comment.py
│   │   ├── hot_topic.py
│   │   └── knowledge.py
│   │
│   ├── hot_sources/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── mock_provider.py
│   │   ├── weibo_mobile_provider.py
│   │   ├── github_archive_provider.py
│   │   └── provider_factory.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── hot_search_service.py
│   │   ├── context_collector.py
│   │   ├── fact_summarizer.py
│   │   ├── topic_classifier.py
│   │   ├── rag_retriever.py
│   │   ├── opinion_generator.py
│   │   ├── persona_rewriter.py
│   │   ├── safety_checker.py
│   │   ├── draft_service.py
│   │   └── generation_pipeline.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── openai_client.py
│   │   ├── deepseek_client.py
│   │   └── qwen_client.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── splitter.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   │
│   ├── prompts/
│   │   ├── system_prompt.md
│   │   ├── fact_summary_prompt.md
│   │   ├── opinion_prompt.md
│   │   ├── safety_prompt.md
│   │   └── personas/
│   │       ├── angry_netizen.md
│   │       ├── ironic_observer.md
│   │       ├── rational_critic.md
│   │       └── pr_critic.md
│   │
│   ├── knowledge/
│   │   ├── brand_pr_cases.md
│   │   ├── gender_discourse.md
│   │   ├── rhetoric_templates.md
│   │   ├── internet_slang.md
│   │   └── safety_rules.md
│   │
│   ├── data/
│   │   ├── sqlite/
│   │   └── vector_db/
│   │
│   └── utils/
│       ├── logger.py
│       ├── text_cleaner.py
│       ├── web_search.py
│       └── time_utils.py
│
├── frontend/
│   ├── streamlit_app.py
│   └── assets/
│
├── tests/
│   ├── test_fact_summarizer.py
│   ├── test_rag_retriever.py
│   ├── test_safety_checker.py
│   └── test_generation_pipeline.py
│
└── docs/
    ├── architecture.md
    ├── api.md
    ├── prompt_design.md
    ├── roadmap.md
    ├── mcp_design.md
    ├── automation_design.md
    └── draft_review_workflow.md
```

---

## 5. 核心模块说明

### 5.1 热点采集模块：Hot Search Service

文件：

```text
app/services/hot_search_service.py
```

职责：

1. 获取微博热搜榜。
2. 获取单个热点的基础信息。
3. 标准化热搜数据结构。
4. 支持后续切换不同数据源。

输入示例：

```json
{
  "source": "weibo",
  "limit": 20
}
```

输出示例：

```json
[
  {
    "rank": 1,
    "keyword": "某品牌母亲节文案翻车",
    "hot_value": "1234567",
    "url": "https://example.com/topic",
    "source": "weibo",
    "timestamp": "2026-05-11T18:00:00+09:00"
  }
]
```

开发要求：

1. 第一版可以使用 mock 数据。
2. 后续再接入第三方热榜 API。
3. 不要在第一版强依赖微博爬虫。
4. 所有外部请求必须有超时设置。
5. 请求失败时返回明确错误信息，不要让系统崩溃。

---

### 5.2 背景资料收集模块：Context Collector

文件：

```text
app/services/context_collector.py
```

职责：

1. 根据热点关键词搜索相关背景信息。
2. 汇总标题、摘要、链接、发布时间。
3. 清洗重复内容。
4. 将信息交给事实摘要模块。

输入示例：

```json
{
  "topic": "某品牌母亲节文案翻车",
  "max_results": 5
}
```

输出示例：

```json
{
  "topic": "某品牌母亲节文案翻车",
  "items": [
    {
      "title": "某品牌母亲节文案引争议",
      "snippet": "网友认为相关文案存在母职工具化表达……",
      "url": "https://example.com/news",
      "source": "web",
      "published_at": "2026-05-11"
    }
  ]
}
```

开发要求：

1. 第一版可以让用户手动粘贴背景材料。
2. 第二版再加入搜索 API。
3. 对来源不明的信息要标记为 uncertain。
4. 不要将网友爆料直接当作事实。

---

### 5.3 事实摘要模块：Fact Summarizer

文件：

```text
app/services/fact_summarizer.py
```

职责：

1. 从背景资料中抽取可确认事实。
2. 区分事实、观点和猜测。
3. 总结争议点。
4. 输出结构化事件摘要。

输入：

```json
{
  "topic": "某品牌母亲节文案翻车",
  "context_items": []
}
```

输出：

```json
{
  "topic": "某品牌母亲节文案翻车",
  "confirmed_facts": [
    "品牌发布母亲节相关文案。",
    "部分网友认为文案存在母职工具化表达。",
    "相关内容引发争议。"
  ],
  "controversy_points": [
    "文案是否强化母亲无条件牺牲的叙事。",
    "品牌是否借亲情叙事进行情绪营销。"
  ],
  "uncertain_points": [
    "文案具体审核流程暂不明确。",
    "品牌内部决策过程暂不明确。"
  ],
  "public_sentiment": "负面为主",
  "risk_level": "medium"
}
```

Prompt 要求：

```text
只总结可确认事实。
不要进行情绪化评价。
不要猜测当事人动机。
如果信息不足，明确标记“公开信息不足”。
```

---

### 5.4 知识库检索模块：RAG Retriever

文件：

```text
app/services/rag_retriever.py
```

职责：

1. 加载本地 Markdown 知识库。
2. 将知识库切分为文本块。
3. 生成向量。
4. 存入向量数据库。
5. 根据热点和事实摘要检索相关内容。

知识库内容类型：

```text
1. 品牌公关案例
2. 社会议题分析
3. 互联网锐评话术
4. 情绪化表达模板
5. 舆论分析框架
6. 风险边界规则
```

检索输入：

```json
{
  "query": "母亲节文案 品牌公关 女性工具化 情绪营销",
  "top_k": 5
}
```

检索输出：

```json
[
  {
    "content": "品牌在母亲节营销中常见的问题是将母亲价值等同于牺牲……",
    "source": "brand_pr_cases.md",
    "score": 0.87
  }
]
```

开发要求：

1. 第一版使用 Chroma。
2. 支持重新构建索引。
3. 支持增量添加知识库文档。
4. 每条检索结果保留来源文件名。
5. 不要把知识库内容当作绝对事实，只作为评论参考。

---

### 5.5 观点生成模块：Opinion Generator

文件：

```text
app/services/opinion_generator.py
```

职责：

1. 根据事实摘要和知识库内容生成观点。
2. 判断事件核心矛盾。
3. 形成评论主轴。
4. 不直接输出最终文案，而是输出观点草稿。

输入：

```json
{
  "fact_summary": {},
  "retrieved_knowledge": []
}
```

输出：

```json
{
  "core_conflict": "这件事的核心不是文案措辞失误，而是品牌将母亲价值等同于无条件奉献，并借此完成情感营销。",
  "critique_angles": [
    "母职牺牲叙事",
    "品牌情绪营销",
    "公关话术与真实价值观之间的错位"
  ],
  "usable_lines": [
    "这不是感恩母亲，是消费母职。",
    "品牌不是不会表达爱，它是只会表达母亲的使用价值。"
  ]
}
```

开发要求：

1. 输出必须基于事实摘要。
2. 不得添加事实摘要中不存在的事实。
3. 可以进行价值判断，但必须避免定罪式断言。
4. 所有观点都应该能回到事实和知识库依据。

---

### 5.6 人格化改写模块：Persona Rewriter

文件：

```text
app/services/persona_rewriter.py
```

职责：

1. 将观点草稿改写成指定人格风格。
2. 控制情绪强度。
3. 控制讽刺程度。
4. 输出多种平台适配文案。

输入：

```json
{
  "opinion": {},
  "persona": "angry_netizen",
  "emotion_level": 8,
  "output_format": "weibo"
}
```

输出：

```json
{
  "one_liner": "这不是文案翻车，这是价值观裸奔。",
  "short_comment": "不是，2026 年了，还有品牌觉得把女性按进“妈妈必须牺牲”的模具里很感人？这不叫母亲节文案，这叫把旧观念重新包装成消费场景。",
  "emotional_version": "每次看到这种文案都想笑。嘴上说感恩母亲，实际字里行间全是“母亲就该忍、就该扛、就该无条件付出”。这不是歌颂母爱，这是给旧观念刷了一层商业滤镜。",
  "rational_version": "这类文案的问题不只是表达粗糙，而是它将母亲的价值与牺牲深度绑定。品牌以为自己在制造情感共鸣，实际上是在重复一种早已被质疑的家庭伦理叙事。",
  "ironic_version": "挺会写的，把母亲写得像家庭服务器，全年无休，自动续费，坏了还得先反思自己是不是不够伟大。",
  "comment_replies": [
    "这不是感恩，是消费。",
    "母亲节不是母职 KPI 展示日。",
    "它不是不懂用户，它是太懂怎么消费情绪了。"
  ]
}
```

开发要求：

1. 表达可以尖锐，但不能低级辱骂。
2. 优先攻击结构、话术、决策逻辑。
3. 不攻击无关个人。
4. 不攻击普通素人。
5. 不使用歧视性表达。
6. 不把猜测说成事实。

---

### 5.7 风险审查模块：Safety Checker

文件：

```text
app/services/safety_checker.py
```

职责：

1. 检查输出是否包含未证实事实。
2. 检查是否存在人身攻击。
3. 检查是否存在隐私泄露。
4. 检查是否存在歧视性表达。
5. 检查是否存在煽动网暴。
6. 对高风险内容进行降级改写。

输入：

```json
{
  "draft": {},
  "fact_summary": {}
}
```

输出：

```json
{
  "is_safe": true,
  "risk_level": "low",
  "issues": [],
  "revised_output": {}
}
```

风险等级：

| 等级 | 含义 |
|---|---|
| low | 基本安全 |
| medium | 有轻微风险，需要提示 |
| high | 不建议输出，需要改写 |
| blocked | 禁止输出 |

审查规则：

```text
1. 不能说“某人一定是故意的”，除非事实中明确存在证据。
2. 不能说“某品牌违法犯罪”，除非有权威结论。
3. 不能对普通人进行羞辱、网暴或隐私挖掘。
4. 不能使用性别、地域、民族、疾病、残障等歧视性攻击。
5. 涉及刑事案件、死亡、未成年人、医疗等内容时，要降级情绪表达。
6. 涉及不完整信息时，要加入“目前公开信息有限”。
```

---

### 5.8 生成流水线模块：Generation Pipeline

文件：

```text
app/services/generation_pipeline.py
```

职责：

1. 串联所有模块。
2. 对外提供统一生成接口。
3. 处理异常。
4. 返回完整结果。

伪代码：

```python
def generate_comment(topic: str, persona: str, emotion_level: int):
    hot_topic = hot_search_service.get_topic(topic)
    context = context_collector.collect(topic)
    fact_summary = fact_summarizer.summarize(topic, context)
    retrieved = rag_retriever.retrieve(fact_summary)
    opinion = opinion_generator.generate(fact_summary, retrieved)
    draft = persona_rewriter.rewrite(opinion, persona, emotion_level)
    safety_result = safety_checker.check(draft, fact_summary)

    if safety_result.is_safe:
        return safety_result.revised_output or draft

    if safety_result.risk_level == "high":
        return safety_checker.rewrite_to_safe_version(draft, fact_summary)

    if safety_result.risk_level == "blocked":
        return {
            "error": "当前话题风险过高，无法生成情绪化锐评。",
            "safe_summary": fact_summary
        }
```

---

## 6. Prompt 设计

### 6.1 总系统 Prompt

文件：

```text
app/prompts/system_prompt.md
```

内容：

```md
你是一个中文互联网热点锐评写手，负责对微博热搜、品牌公关、社会争议、娱乐事件进行评论。

你的表达风格：
1. 有情绪，有立场，不要像新闻通稿。
2. 语言可以尖锐、讽刺、冷笑，但不要低级辱骂。
3. 优先攻击结构、话术、决策逻辑，不攻击无关个人。
4. 不追求绝对中立，但必须尊重事实。
5. 可以表现出人的认知偏差：厌蠢、对公关话术不信任、反感消费苦难、反感爹味说教。
6. 输出要像真实网友，而不是 AI 总结。

你的思维方式：
1. 先判断事件表层争议。
2. 再判断背后的利益结构、话语逻辑、情绪操控方式。
3. 再判断公众为什么愤怒。
4. 最后给出有冲击力的评论。

你的限制：
1. 不得编造未经确认的事实。
2. 不得把猜测写成事实。
3. 不得网暴普通人。
4. 不得泄露隐私。
5. 不得使用性别、地域、民族、疾病、残障等歧视性攻击。
6. 涉及刑事、法律、医疗、未成年人等内容时，必须降低情绪强度。
7. 公开信息不足时，必须明确标注“目前公开信息有限”。

输出格式：
- 一句话锐评
- 微博短评版
- 情绪拉满版
- 理性拆解版
- 阴阳怪气版
- 评论区短句
```

---

### 6.2 事实摘要 Prompt

文件：

```text
app/prompts/fact_summary_prompt.md
```

内容：

```md
请根据输入资料，对热点事件进行事实摘要。

要求：
1. 只总结可确认事实。
2. 不进行价值判断。
3. 不进行情绪化表达。
4. 区分事实、观点、猜测和未确认信息。
5. 如果信息不足，写入 uncertain_points。
6. 不要补充资料中不存在的信息。

请输出 JSON：

{
  "topic": "",
  "confirmed_facts": [],
  "controversy_points": [],
  "uncertain_points": [],
  "public_sentiment": "",
  "risk_level": "low|medium|high"
}
```

---

### 6.3 观点生成 Prompt

文件：

```text
app/prompts/opinion_prompt.md
```

内容：

```md
你需要根据事实摘要和知识库内容，生成热点评论的观点草稿。

要求：
1. 观点必须基于 confirmed_facts。
2. 可以结合 retrieved_knowledge 中的分析框架。
3. 不要编造新事实。
4. 不要进行最终文案化表达。
5. 重点找出事件的核心矛盾。
6. 输出应适合作为后续人格化改写的基础。

请输出 JSON：

{
  "core_conflict": "",
  "critique_angles": [],
  "usable_lines": []
}
```

---

### 6.4 风险审查 Prompt

文件：

```text
app/prompts/safety_prompt.md
```

内容：

```md
请对以下锐评草稿进行风险审查。

审查维度：
1. 是否包含未经证实的事实断言。
2. 是否包含人身攻击。
3. 是否攻击普通素人。
4. 是否包含隐私泄露。
5. 是否包含性别、地域、民族、疾病、残障等歧视性表达。
6. 是否存在煽动网暴。
7. 是否涉及刑事、法律、医疗、未成年人等高风险主题。
8. 是否把猜测写成确定事实。

处理规则：
1. 如果基本安全，is_safe 为 true。
2. 如果存在轻微问题，修改为更安全版本。
3. 如果高风险，降级情绪表达。
4. 如果无法安全输出，返回 blocked。

请输出 JSON：

{
  "is_safe": true,
  "risk_level": "low|medium|high|blocked",
  "issues": [],
  "revised_output": {}
}
```

---

## 7. 人格模板设计

### 7.1 暴躁网友型：angry_netizen

文件：

```text
app/prompts/personas/angry_netizen.md
```

```md
人格名称：暴躁但有逻辑的互联网网友

情绪底色：
- 厌蠢
- 不耐烦
- 反感糊弄
- 对品牌公关天然不信任

表达特征：
- 句子短。
- 节奏快。
- 喜欢反问。
- 喜欢一句话定性。
- 可以直接表达愤怒，但不低级辱骂。

常用表达：
- 不是，怎么还有人觉得……
- 这不是……这是……
- 最离谱的不是……而是……
- 说白了就是……
- 别装了……

限制：
- 不攻击普通人。
- 不造谣。
- 不使用歧视性表达。
```

---

### 7.2 阴阳怪气型：ironic_observer

文件：

```text
app/prompts/personas/ironic_observer.md
```

```md
人格名称：阴阳怪气的冷笑观察者

情绪底色：
- 冷笑
- 讽刺
- 表面克制
- 实际尖锐

表达特征：
- 不直接骂。
- 用夸张式赞美表达讽刺。
- 喜欢“挺会的”“确实”“不愧是”。
- 善于把荒谬逻辑反过来复述。

常用表达：
- 挺会的。
- 确实很懂……
- 不愧是……
- 这套话术真熟练。
- 感人，太感人了。

限制：
- 不进行身份攻击。
- 不泄露隐私。
- 不把猜测当事实。
```

---

### 7.3 理性拆解型：rational_critic

文件：

```text
app/prompts/personas/rational_critic.md
```

```md
人格名称：理性拆解型评论者

情绪底色：
- 克制
- 清醒
- 厌恶伪善
- 重视逻辑结构

表达特征：
- 先拆事实。
- 再拆话术。
- 最后给价值判断。
- 语言锋利但不失控。
- 适合长评和分析。

常用结构：
1. 这件事表面上是……
2. 但真正的问题是……
3. 它暴露的是……
4. 所以公众愤怒的点不是……而是……

限制：
- 必须保持事实准确。
- 不使用过度情绪化辱骂。
```

---

### 7.4 公关毒舌观察者：pr_critic

文件：

```text
app/prompts/personas/pr_critic.md
```

```md
人格名称：毒舌公关观察者

情绪底色：
- 对公关话术敏感
- 讨厌避重就轻
- 讨厌把用户当傻子
- 对品牌失误有强烈批判倾向

表达特征：
- 专注品牌、公关、营销逻辑。
- 擅长指出文案背后的决策问题。
- 喜欢批判“会议室自嗨”。
- 喜欢分析品牌如何消费情绪。

常用表达：
- 这不是文案问题，是审核链路问题。
- 这不是翻车，是价值观裸奔。
- 品牌最离谱的地方在于……
- 这套公关话术的核心就是……

限制：
- 不无证据指控违法。
- 不攻击具体员工。
- 不把内部流程猜测写成事实。
```

---

## 8. 知识库设计

### 8.1 知识库文件

建议第一版建立以下文件：

```text
app/knowledge/
├── brand_pr_cases.md
├── gender_discourse.md
├── rhetoric_templates.md
├── internet_slang.md
└── safety_rules.md
```

### 8.2 brand_pr_cases.md

内容方向：

```md
# 品牌公关案例库

## 母亲节文案争议类

常见问题：
1. 将母亲价值等同于牺牲。
2. 将女性身份绑定家庭角色。
3. 用亲情叙事完成商品销售。
4. 表面感恩，实际消费情绪。
5. 忽略真实母亲处境，只使用符号化母亲。

评论角度：
- 文案不是孤立问题，而是品牌价值观和审核机制的外显。
- 品牌常常把“爱”包装成消费场景。
- 公众反感的不是节日营销，而是廉价地挪用亲密关系。
```

### 8.3 gender_discourse.md

内容方向：

```md
# 性别议题与母职叙事

核心概念：
1. 母职神话。
2. 情感劳动。
3. 无偿照护劳动。
4. 牺牲叙事。
5. 女性工具化。

评论角度：
- 母亲不应该只被定义为奉献者。
- 感恩母亲不等于赞美牺牲。
- 如果一个文案只看见母亲的付出，而看不见母亲作为人的需求，那么它本质上仍然是工具化表达。
```

### 8.4 rhetoric_templates.md

内容方向：

```md
# 锐评话术模板

## 不是 A，是 B

- 这不是文案翻车，这是价值观裸奔。
- 这不是感恩母亲，是消费母职。
- 这不是公关失误，是把用户当傻子。

## 表面上 A，实际上 B

- 表面上是在歌颂母爱，实际上是在强化牺牲。
- 表面上是在道歉，实际上是在止损。
- 表面上是在共情用户，实际上是在糊弄舆论。

## 最离谱的不是 A，而是 B

- 最离谱的不是它写得烂，而是它好像真的觉得这很感人。
- 最恶心的不是它翻车，而是它翻车之后还在装无辜。
```

### 8.5 internet_slang.md

内容方向：

```md
# 互联网表达风格

可用表达：
- 不是……
- 怎么还有人……
- 这味太冲了。
- 熟悉的配方，熟悉的敷衍。
- 这套话术真不新鲜。
- 会议室自嗨。
- 把用户当 NPC。
- 把情绪当流量入口。

避免表达：
- 低级脏话。
- 身份攻击。
- 地域黑。
- 性别歧视。
- 针对普通人的羞辱。
```

### 8.6 safety_rules.md

内容方向：

```md
# 内容安全规则

禁止：
1. 未经证实指控违法犯罪。
2. 人肉搜索。
3. 煽动网暴。
4. 攻击普通素人。
5. 使用歧视性表达。
6. 对未成年人、死亡、刑事案件进行娱乐化锐评。

建议：
1. 使用“公开信息显示”。
2. 使用“目前无法确认”。
3. 使用“看起来像是”。
4. 使用“更像是一种……”。
5. 将批评对象指向结构、话术和行为，而不是身份属性。
```

---

## 9. API 设计

### 9.1 生成锐评接口

路径：

```http
POST /api/comment/generate
```

请求：

```json
{
  "topic": "某品牌母亲节文案翻车",
  "persona": "angry_netizen",
  "emotion_level": 8,
  "use_rag": true,
  "context_text": ""
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| topic | string | 是 | 热点话题 |
| persona | string | 否 | 人格模板 |
| emotion_level | int | 否 | 情绪强度，1-10 |
| use_rag | bool | 否 | 是否启用知识库 |
| context_text | string | 否 | 用户手动提供的背景资料 |

返回：

```json
{
  "topic": "某品牌母亲节文案翻车",
  "fact_summary": {},
  "retrieved_knowledge": [],
  "opinion": {},
  "output": {
    "one_liner": "",
    "short_comment": "",
    "emotional_version": "",
    "rational_version": "",
    "ironic_version": "",
    "comment_replies": []
  },
  "safety": {
    "is_safe": true,
    "risk_level": "low",
    "issues": []
  }
}
```

---

### 9.2 热搜列表接口

路径：

```http
GET /api/hot/weibo
```

参数：

```text
limit=20
```

返回：

```json
{
  "source": "weibo",
  "items": [
    {
      "rank": 1,
      "keyword": "",
      "hot_value": "",
      "url": "",
      "timestamp": ""
    }
  ]
}
```

---

### 9.3 知识库重建接口

路径：

```http
POST /api/knowledge/rebuild
```

请求：

```json
{
  "knowledge_dir": "app/knowledge"
}
```

返回：

```json
{
  "success": true,
  "document_count": 5,
  "chunk_count": 128
}
```

---

### 9.4 人格列表接口

路径：

```http
GET /api/comment/personas
```

返回：

```json
{
  "personas": [
    {
      "id": "angry_netizen",
      "name": "暴躁网友型"
    },
    {
      "id": "ironic_observer",
      "name": "阴阳怪气型"
    },
    {
      "id": "rational_critic",
      "name": "理性拆解型"
    },
    {
      "id": "pr_critic",
      "name": "公关毒舌观察者"
    }
  ]
}
```

---

## 10. 数据模型设计

### 10.1 HotTopic

```python
class HotTopic(BaseModel):
    rank: int | None = None
    keyword: str
    hot_value: str | None = None
    url: str | None = None
    source: str = "weibo"
    timestamp: datetime
```

### 10.2 FactSummary

```python
class FactSummary(BaseModel):
    topic: str
    confirmed_facts: list[str]
    controversy_points: list[str]
    uncertain_points: list[str]
    public_sentiment: str | None = None
    risk_level: Literal["low", "medium", "high"] = "low"
```

### 10.3 RetrievedKnowledge

```python
class RetrievedKnowledge(BaseModel):
    content: str
    source: str
    score: float | None = None
```

### 10.4 OpinionDraft

```python
class OpinionDraft(BaseModel):
    core_conflict: str
    critique_angles: list[str]
    usable_lines: list[str]
```

### 10.5 CommentOutput

```python
class CommentOutput(BaseModel):
    one_liner: str
    short_comment: str
    emotional_version: str
    rational_version: str
    ironic_version: str
    comment_replies: list[str]
```

### 10.6 SafetyResult

```python
class SafetyResult(BaseModel):
    is_safe: bool
    risk_level: Literal["low", "medium", "high", "blocked"]
    issues: list[str]
    revised_output: CommentOutput | None = None
```

---

## 11. Codex / AI Agent 开发指令

### 11.1 推荐创建 AGENTS.md

在项目根目录创建：

```text
AGENTS.md
```

内容如下：

```md
# AGENTS.md

## Project Goal

Build a Chinese hot-topic commentary generation system. The system should collect or accept Weibo hot topics, summarize facts, retrieve relevant local knowledge, generate opinion drafts, rewrite them with persona-based styles, and run a safety check before returning final outputs.

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic
- Chroma for vector database
- SQLite for local storage
- Markdown-based local knowledge base
- Optional Streamlit frontend
- LLM provider should be abstracted through a common interface

## Core Pipeline

Implement the generation pipeline in this order:

1. hot topic input or hot search retrieval
2. context collection
3. fact summarization
4. topic classification and risk strategy
5. RAG retrieval
6. opinion generation
7. persona rewriting
8. safety checking
9. final response

## Coding Rules

- Keep modules small and testable.
- Use Pydantic models for request and response schemas.
- Do not hard-code API keys.
- Read API keys from environment variables.
- All external HTTP requests must have timeouts.
- Handle failure gracefully.
- Keep prompts in Markdown files under app/prompts.
- Keep knowledge base files under app/knowledge.
- Do not mix business logic into route files.
- Route files should only parse requests and call services.
- Write tests for pipeline and safety checker.

## Content Rules

- Do not generate unverified factual claims.
- Do not attack private individuals.
- Do not reveal private information.
- Do not use discriminatory language.
- For uncertain facts, use cautious wording.
- The model may be sharp, sarcastic, and emotional, but must remain fact-grounded.

## Done When

The MVP is complete when:

1. The user can input a topic through API or Streamlit.
2. The system can load local Markdown knowledge.
3. The system can retrieve relevant knowledge chunks.
4. The system can generate multiple commentary styles.
5. The safety checker can return a risk result.
6. The final output includes fact summary, topic classification, opinion draft, generated comments, and safety metadata.
7. Generated content is saved as draft by default when called from MCP or automation.
8. The project does not implement automatic Weibo publishing in MVP.
```

---

## 12. 实现路径

### 12.1 第 0 步：初始化项目

Codex 任务：

```text
Create the initial project structure for a Python FastAPI project named hot-comment-ai. Include app, services, schemas, llm, rag, prompts, knowledge, tests, and frontend folders. Add README.md, AGENTS.md, .env.example, requirements.txt, Dockerfile, and docker-compose.yml.
```

验收标准：

```text
1. 项目目录完整。
2. 可以安装依赖。
3. 可以运行 FastAPI 服务。
4. /health 接口返回正常。
```

---

### 12.2 第 1 步：定义数据模型

Codex 任务：

```text
Implement Pydantic schemas for HotTopic, FactSummary, RetrievedKnowledge, OpinionDraft, CommentOutput, SafetyResult, and GenerateCommentRequest. Put them under app/schemas.
```

验收标准：

```text
1. 所有模型可以正常 import。
2. 字段类型明确。
3. 有基础单元测试。
```

---

### 12.3 第 2 步：实现 LLM 抽象层

Codex 任务：

```text
Create an LLM client abstraction. Define BaseLLMClient with a generate method. Implement at least one concrete client using environment variables for API key and base URL. The system should support provider switching through config.
```

验收标准：

```text
1. 不在代码中硬编码 API Key。
2. 支持环境变量配置。
3. LLM 调用失败时返回明确异常。
4. 可以用 MockLLMClient 做测试。
```

---

### 12.4 第 3 步：实现 Prompt Loader

Codex 任务：

```text
Implement a prompt loader utility that reads Markdown prompt files from app/prompts. It should support loading system prompts, task prompts, and persona prompts.
```

验收标准：

```text
1. 能读取 app/prompts/system_prompt.md。
2. 能读取 app/prompts/personas/angry_netizen.md。
3. 文件不存在时返回明确错误。
```

---

### 12.5 第 4 步：实现知识库加载与切分

Codex 任务：

```text
Implement Markdown knowledge loader and text splitter. Load all .md files under app/knowledge, split them into chunks with metadata including source filename.
```

验收标准：

```text
1. 能读取所有 Markdown 文件。
2. 每个 chunk 保留 source。
3. chunk 长度可配置。
4. 有测试覆盖。
```

---

### 12.6 第 5 步：实现 RAG 检索

Codex 任务：

```text
Implement a Chroma-based vector store service. It should build an index from app/knowledge and retrieve top_k relevant chunks for a query.
```

验收标准：

```text
1. 支持 rebuild index。
2. 支持 retrieve(query, top_k)。
3. 返回 content、source、score。
4. 没有知识库时系统不崩溃。
```

---

### 12.7 第 6 步：实现事实摘要模块

Codex 任务：

```text
Implement FactSummarizer service. It should accept topic and context text, call the LLM with fact_summary_prompt.md, and parse the result into FactSummary.
```

验收标准：

```text
1. 输出符合 FactSummary schema。
2. LLM 返回非 JSON 时有 fallback 处理。
3. 没有 context 时也能返回低信息量摘要。
```

---

### 12.8 第 7 步：实现观点生成模块

Codex 任务：

```text
Implement OpinionGenerator service. It should accept FactSummary and RetrievedKnowledge list, then call the LLM with opinion_prompt.md and return OpinionDraft.
```

验收标准：

```text
1. 输出符合 OpinionDraft schema。
2. 不应该添加 fact_summary 中不存在的事实。
3. 支持 MockLLM 测试。
```

---

### 12.9 第 8 步：实现人格化改写模块

Codex 任务：

```text
Implement PersonaRewriter service. It should load persona prompt according to persona id, accept OpinionDraft, FactSummary, emotion_level, and return CommentOutput.
```

验收标准：

```text
1. 支持 angry_netizen。
2. 支持 ironic_observer。
3. 支持 rational_critic。
4. 支持 pr_critic。
5. 输出符合 CommentOutput schema。
```

---

### 12.10 第 9 步：实现风险审查模块

Codex 任务：

```text
Implement SafetyChecker service. It should inspect CommentOutput and FactSummary. It can use rule-based checks first, then optional LLM-based safety review. Return SafetyResult.
```

验收标准：

```text
1. 能识别明显人身攻击词。
2. 能识别“肯定违法”“一定犯罪”等高风险断言。
3. 能识别隐私泄露风险词。
4. 能返回 revised_output 或 issues。
5. 有测试覆盖。
```

---

### 12.11 第 10 步：实现生成流水线

Codex 任务：

```text
Implement GenerationPipeline service that orchestrates fact summarization, RAG retrieval, opinion generation, persona rewriting, and safety checking. It should return a complete response object.
```

验收标准：

```text
1. 输入 topic 可以返回完整结果。
2. 支持 context_text。
3. 支持 persona。
4. 支持 emotion_level。
5. 任一模块失败时返回清晰错误。
```

---

### 12.12 第 11 步：实现 API 路由

Codex 任务：

```text
Implement FastAPI routes:
- GET /health
- POST /api/comment/generate
- GET /api/comment/personas
- POST /api/knowledge/rebuild
```

验收标准：

```text
1. OpenAPI 文档可访问。
2. 请求参数校验正常。
3. 返回结构稳定。
4. API 能调用 GenerationPipeline。
```

---

### 12.13 第 12 步：实现 Streamlit 前端

Codex 任务：

```text
Create a Streamlit frontend for the MVP. The user can input topic, paste context text, select persona, choose emotion level, and click generate. Display fact summary, retrieved knowledge, opinion draft, final outputs, and safety result.
```

验收标准：

```text
1. 能输入话题。
2. 能选择人格。
3. 能调节情绪强度。
4. 能显示多版本输出。
5. 能显示风险审查结果。
```

---

### 12.14 第 13 步：加入热点榜接口

Codex 任务：

```text
Implement HotSearchService with mock provider first. Add GET /api/hot/weibo. The service should be designed so that real providers can be added later.
```

验收标准：

```text
1. 能返回 mock 热搜列表。
2. 数据结构符合 HotTopic。
3. provider 可以扩展。
```

---

### 12.15 第 14 步：完善测试

Codex 任务：

```text
Add tests for schemas, prompt loader, knowledge loader, retriever, safety checker, and generation pipeline using MockLLMClient.
```

验收标准：

```text
1. pytest 可以正常运行。
2. 核心模块都有基础测试。
3. 测试不依赖真实 LLM API。
```

---

### 12.16 第 15 步：Docker 化

Codex 任务：

```text
Add Dockerfile and docker-compose.yml for running FastAPI and optional Streamlit frontend. Use environment variables for configuration.
```

验收标准：

```text
1. docker compose up 可以启动服务。
2. FastAPI 服务可访问。
3. Streamlit 服务可访问。
4. 数据目录可以挂载。
```

---

## 13. 环境变量设计

`.env.example`：

```env
APP_NAME=hot-comment-ai
APP_ENV=development
LOG_LEVEL=INFO

LLM_PROVIDER=openai
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

CHROMA_PERSIST_DIR=app/data/vector_db
KNOWLEDGE_DIR=app/knowledge

SQLITE_DB_PATH=app/data/sqlite/app.db

HOT_SEARCH_PROVIDER=mock
HOT_SEARCH_API_KEY=
```

---

## 14. 内容生成质量标准

### 14.1 好输出的标准

好的输出应该满足：

1. 事实没有乱编。
2. 能抓住事件核心矛盾。
3. 有明确立场。
4. 有情绪，但不是无意义辱骂。
5. 像真实网友，而不是 AI 总结。
6. 有适合微博传播的短句。
7. 不攻击普通人。
8. 不泄露隐私。
9. 不使用歧视性表达。

### 14.2 坏输出的表现

坏输出包括：

```text
这个品牌真恶心，公关全是废物，赶紧倒闭。
```

问题：

1. 只有辱骂，没有观点。
2. 没有事实依据。
3. 表达低级。
4. 容易引发风险。

较好版本：

```text
这类文案的问题不只是写得烂，而是它把“母亲”当成了一个可以随手调用的情绪符号。表面上是在感恩，实际上是在把牺牲包装成卖点。
```

优点：

1. 有批判对象。
2. 有结构分析。
3. 情绪明确。
4. 风险较低。

---

## 15. 安全边界

### 15.1 允许的内容

允许：

1. 批评品牌文案。
2. 批评公关策略。
3. 批评公开机构的公开行为。
4. 批评话术、叙事、营销逻辑。
5. 用讽刺方式表达观点。
6. 输出平台评论草稿。

### 15.2 不允许的内容

不允许：

1. 编造未确认事实。
2. 指控违法犯罪但没有证据。
3. 人肉搜索。
4. 煽动网暴。
5. 攻击普通素人。
6. 泄露隐私。
7. 对未成年人进行羞辱。
8. 对死亡、灾难、刑事案件进行娱乐化调侃。
9. 使用性别、地域、民族、疾病、残障等歧视性攻击。

### 15.3 高风险话题处理

高风险话题包括：

1. 刑事案件。
2. 自杀、自残。
3. 未成年人。
4. 医疗事故。
5. 真实个人隐私。
6. 民族、宗教、地域冲突。
7. 政治敏感事件。
8. 灾难死亡事件。

处理方式：

```text
1. 降低情绪强度。
2. 强化事实限定。
3. 不使用嘲讽语气。
4. 不进行动机推断。
5. 输出更接近理性分析。
```

---

## 16. 后续优化方向

### 16.1 内容质量评分

可以给每次输出打分：

| 指标 | 说明 |
|---|---|
| fact_grounding | 事实扎实程度 |
| sharpness | 锐利程度 |
| human_like | 真人感 |
| platform_fit | 微博适配度 |
| safety | 安全程度 |
| novelty | 新鲜感 |

### 16.2 爆款潜力评分

可根据以下因素评分：

1. 是否有强冲突。
2. 是否有一句话记忆点。
3. 是否适合转发。
4. 是否能引发共鸣。
5. 是否有足够短的评论区金句。
6. 是否踩中公众情绪点。

### 16.3 人格记忆

后续可加入人格记忆：

```json
{
  "persona_id": "angry_netizen",
  "favorite_phrases": [],
  "avoid_phrases": [],
  "tone_history": [],
  "user_preference": {
    "more_sharp": true,
    "less_ai_like": true
  }
}
```

### 16.4 自动热点筛选

不是所有热搜都适合锐评。

系统可以判断：

```text
1. 是否是娱乐八卦。
2. 是否是品牌公关。
3. 是否是社会事件。
4. 是否涉及高风险人群。
5. 是否信息不足。
6. 是否适合情绪化表达。
```

---

## 17. 推荐开发顺序总结

最终建议 Codex 按以下顺序开发：

```text
1. 初始化项目结构
2. 创建 AGENTS.md
3. 创建数据模型
4. 创建 LLM 抽象层
5. 创建 Prompt Loader
6. 创建知识库文件
7. 实现知识库加载与切分
8. 实现 Chroma 检索
9. 实现事实摘要模块
10. 实现观点生成模块
11. 实现人格化改写模块
12. 实现风险审查模块
13. 实现生成流水线
14. 实现 FastAPI 接口
15. 实现 Streamlit 前端
16. 加入 mock 热搜接口
17. 补充测试
18. Docker 化
19. 接入真实微博热榜 API
20. 新增 DraftService 草稿箱
21. 新增 MCP Server 工具层
22. 新增自动化草稿任务
23. 新增审核工作台
24. 后续扩展生命周期追踪和多平台舆情
```

---

## 18. 给 Codex 的第一条任务

可以直接把下面这段发给 Codex：

```text
请根据项目文档创建一个名为 hot-comment-ai 的 Python FastAPI 项目。

优先完成 MVP，不要一次性实现所有复杂功能。

要求：
1. 创建完整目录结构。
2. 添加 AGENTS.md、README.md、requirements.txt、.env.example。
3. 实现 /health 接口。
4. 定义 Pydantic 数据模型。
5. 创建 prompts 和 knowledge 目录，并写入基础 Markdown 文件。
6. 创建 LLM 抽象层和 MockLLMClient，先不接真实模型。
7. 创建 GenerationPipeline 的空实现或 mock 实现。
8. 添加基础 pytest 测试。
9. 确保项目可以本地启动。

完成后告诉我：
- 已创建哪些文件
- 如何安装依赖
- 如何启动服务
- 如何运行测试
```

---

## 19. 给 Codex 的第二条任务

第一步完成后，再发：

```text
请继续实现 HotComment-AI 的 MVP 生成链路。

要求：
1. 实现 PromptLoader。
2. 实现 KnowledgeLoader。
3. 实现 TextSplitter。
4. 实现一个简单的 KeywordRetriever，先不用真实向量库。
5. 实现 FactSummarizer，先使用 MockLLMClient。
6. 实现 OpinionGenerator，先使用 MockLLMClient。
7. 实现 PersonaRewriter，先使用 MockLLMClient。
8. 实现 SafetyChecker，先使用规则审查。
9. 实现 GenerationPipeline 串联所有模块。
10. 实现 POST /api/comment/generate 接口。
11. 添加测试。

完成后保证：
- 输入 topic 和 context_text 可以返回完整 JSON。
- 返回内容包含 fact_summary、retrieved_knowledge、opinion、output、safety。
```

---

## 20. 给 Codex 的第三条任务

MVP 跑通后，再发：

```text
请将 KeywordRetriever 替换或扩展为 Chroma 向量检索。

要求：
1. 添加 embedding 抽象层。
2. 支持 OpenAI embedding 或本地 fallback embedding。
3. 实现 ChromaVectorStore。
4. 实现 /api/knowledge/rebuild 接口。
5. 支持从 app/knowledge 读取 Markdown 文档并构建索引。
6. 支持 retrieve(query, top_k) 返回相关文本块。
7. 保留 KeywordRetriever 作为 fallback。
8. 添加相关测试。
```

---

## 21. 最终验收标准

项目 MVP 完成时，应满足：

```text
1. 能启动 FastAPI。
2. 能访问 /health。
3. 能通过 /api/comment/generate 生成锐评。
4. 能选择人格。
5. 能调节情绪强度。
6. 能读取本地知识库。
7. 能返回事实摘要。
8. 能返回话题分类结果。
9. 能返回观点草稿。
10. 能返回多风格文案。
11. 能返回风险审查结果。
11. 有基础测试。
12. 有 README 说明。
13. 有 AGENTS.md 给 Codex 使用。
14. 不依赖真实微博爬虫也能跑通。
```

---

## 22. 结论

这个项目最合理的实现方式不是直接让大模型生成评论，而是构建一条稳定的内容生成流水线：

```text
热点输入
↓
事实摘要
↓
知识库检索
↓
观点生成
↓
人格化表达
↓
风险审查
↓
最终输出
```

第一版重点不在“自动抓微博”，而在于把生成链路跑通。  
只要这条链路稳定，后续接微博热搜 API、接真实搜索、接更多人格、接自动发布系统都只是扩展问题。

项目的关键不是让 AI 更会骂，而是让 AI 具备：

```text
事实约束
观点判断
人格表达
安全边界
```

这四件事同时成立，才是一个真正可用的热点锐评 AI。

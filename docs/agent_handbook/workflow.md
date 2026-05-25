# 工作流

## 总原则

项目工作流是“人机协同”，不是自动化发布流水线。

内容生成的长期宗旨是：让模型继承账号的判断习惯，而不是只模仿语气。

有“人味”的文本应稳定具备五类特征：

- 稳定的价值排序：知道账号更关心普通人的规则成本、品牌话术、公关自救、平台机制还是具体处境。
- 稳定的反应方式：同类事件反复出现时，账号有可预期的观察顺序、让步方式、转折方式和收束方式。
- 稳定的词库和句法习惯：保留常用判断词、短句节奏、转折方式和禁用表达，但避免把“口语化”做成油腻模板。
- 具体经验感：文本不只是资料摘要，要能体现“见过这种场面”的判断，例如从规则、成本、注意力和用户处境切入。
- 保留边界和余地：不把话说满；先承认可能合理的部分，再指出未公开、未核验或不透明之处。

因此生成链路不应只追求“更犀利、更像真人”，而应同时提供：

```text
事实背景
+ 价值排序
+ 常见反应模式
+ 句法/词库习惯
+ 禁用表达
+ 历史好稿/坏稿复盘
```

后续风格记忆库、人格判断框架、人味评估器和 RAG 分路都应围绕这条宗旨设计。

功能设计默认采用“双入口”：

```text
真人工作台入口
+ Hermes/MCP 自动化入口
-> 共同调用 app/services
-> 结果进入候选、资料、草稿、摘要或待审核状态
```

也就是说，新增能力时要同时想清楚：

- 真人在哪里看、选、改、确认。
- Hermes 通过哪个 MCP/FastAPI 工具调用。
- 自动化结果如何回到工作台或 Telegram 供人过目。
- 哪些动作必须等待人工确认，哪些动作可以在明确授权后自动执行。

AI 可以做：

- 抓取公开热榜。
- 初筛选题。
- 解释推荐理由。
- 整理人工提供或公开来源的背景资料。
- 检索知识库。
- 生成待审核草稿。
- 给出风险提示。

人必须做：

- 最终选题。
- 背景资料确认。
- 草稿编辑。
- 发布决定。
- 发布后的链接和数据记录。

## 当前微博选题流程

```text
抓取微博热搜前 50
-> TopicSelectionService 评分
-> 生成微博候选池
-> 人工多选并标记 selected/skipped/researched
-> 对 selected/researched 话题补充背景资料
-> 入库 RAG
-> 生成微博短评草稿
-> 草稿箱人工编辑
-> 人工发布
-> 记录 published_url / published_at / performance_note
```

候选池字段重点：

- `score`
- `reason`
- `risk_level`
- `recommended_angle`
- `avoid_points`
- `hot_value`
- `category_label`
- `label`
- `target_platform_scores`
- `recommended_targets`

## 综合池流程

综合池用于保存通用选题资产，而不是保存某个平台的完整创作方案。

```text
微博候选池 selected
-> 人工点击加入综合池
-> TopicAsset 保存通用标题、摘要、来源、热度信号、标签、风险、资料状态
-> 后续由规则/LLM 给出平台分发建议
-> 人工确认进入微博池、知乎问题池或视频创意池
```

综合池不直接保存：

- 微博锐评角度。
- 知乎回答结构。
- 视频分镜稿。

这些属于平台池或草稿产物。

## 草稿箱流程

```text
候选题 selected
-> 选择账号和表达风格
-> 生成微博短评或知乎回答
-> 保存为 DraftRecord
-> 人工编辑 edited_text
-> 更新状态 reviewed/rejected/published_manually
-> 人工记录发布链接和复盘备注
```

状态：

- `draft`
- `reviewed`
- `rejected`
- `published_manually`

草稿箱永远不负责自动发布。

## 背景资料入库流程

当前支持两种入库入口。

人工粘贴入库：

```text
人工选择 selected/researched 候选题
-> 粘贴背景资料、来源 URL、标题、可信度、备注
-> KnowledgeIngestionService 保存到 app/knowledge/inbox/
-> 可选自动 rebuild RAG
-> 后续生成草稿时检索使用
```

工作台本轮资料入库：

```text
人工选择 selected/researched 候选题
-> 点击“检索本轮资料”
-> Exa 返回公开来源摘要、高亮和可信度
-> 人工勾选值得沉淀的来源
-> 点击“把选中资料入库 RAG”
-> KnowledgeIngestionService 保存并在最后一条后 rebuild RAG
```

自动网页抓取暂未实现。后续实现时仍需要人工审查入口，避免低质搬运内容污染知识库。

## 风格记忆库流程

风格记忆库用于沉淀写法规则，不保存大段原文，不复刻单个博主。

真人工作台入口：

```text
粘贴公开或授权文本
-> 提炼风格观察卡
-> 人工查看 hook、节奏、结构、修辞、禁用点
-> 确认入库 app/knowledge/style_memory/
-> rebuild RAG
```

Hermes 入口：

```text
extract_style_memory
-> 用户确认或 auto_ingest
-> ingest_style_memory
-> retrieve_knowledge 验证
```

外部公开博主默认只作为 `public_reference`，入库卡片必须 `needs_review=true`。自有或授权账号可以自动沉淀，但仍只保存风格摘要、短例句和禁用点。

## 多平台方向

平台之间不应长期共用同一个候选池。

推荐结构：

```text
TopicAsset 综合池
-> 微博候选池
-> 知乎问题池
-> 视频创意池
```

LLM 可以参与分发建议，但不能自动拍板。系统只提供推荐去向、理由、阻碍、建议角度和需要补充的资料。

当前已接入 `LLMPlatformRouter`：

- 规则层先给基础分和硬约束。
- LLM 再做编辑判断和平台适配解释。
- 高风险话题仍由规则层限制，不能由 LLM 单独推荐情绪化微博或误导性视频。
- Streamlit 综合池详情页可以生成并查看微博、知乎、视频三类分发建议。

## Exa 背景检索与 RAG 入库时机

背景资料不应等到生成前才第一次出现。当前 Streamlit/API 已支持候选池生成时可选“微博智搜 + Exa”背景检索重排：

```text
热搜列表
-> TopicSelectionService 硬规则粗筛 3-10 条
-> 勾选“启用背景检索重排”
-> 微博智搜为前 N 条候选补站内热搜语境
-> Exa 为前 N 条候选检索 1-5 条公开背景摘要
-> TopicRerankService 基于标题、热度、智搜/Exa 摘要、风险提示重新评分
-> 候选池保存 rerank_score、rerank_decision、needed_context、source_urls
-> 人工审核 selected/researched
-> 后续生成时继续使用 RAG 编辑记忆，必要时再补本轮智搜/Exa 背景
-> 文本给用户过目
```

这里的微博智搜和 Exa 结果是临时上下文，用于当次评分和生成；不默认写入长期 RAG。

RAG 入库放在生成之后，由人确认资料或角度有长期复用价值时再触发：

```text
用户确认资料值得沉淀
-> Hermes 或工作台整理 Markdown 资料卡
-> KnowledgeIngestionService 写入 app/knowledge/inbox/
-> rebuild RAG
```

当前 RAG 更偏人格化、写作公式和安全边界；Exa 更适合补当前热点事实。不要把低质量转载、未核实爆料和只服务当天的小八卦自动写入 RAG。

# 工作流

## 总原则

项目工作流是“人机协同”，不是自动化发布流水线。

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

当前只做人工粘贴入库：

```text
人工选择 selected/researched 候选题
-> 粘贴背景资料、来源 URL、标题、可信度、备注
-> KnowledgeIngestionService 保存到 app/knowledge/inbox/
-> 可选自动 rebuild RAG
-> 后续生成草稿时检索使用
```

自动搜索和自动网页抓取暂未实现。后续实现时需要人工审查入口，避免低质搬运内容污染知识库。

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

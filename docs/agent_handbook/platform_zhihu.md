# 知乎产线

## 定位

知乎产线用于解释型、论证型、长回答内容，不是微博热搜短评的简单变体。

边界：

- 不自动发布知乎回答。
- 不自动评论、点赞、关注、私信。
- 不批量运营账号。
- 不绕过平台限制。

## 当前能力

已实现：

- 知乎回答生成器 `ZhihuAnswerGenerator`。
- 知乎垂直领域配置 `configs/zhihu_domains.json`。
- 知乎适配评分 `ZhihuTopicFitService`。
- API：`POST /api/zhihu/answer/generate`。
- API：`POST /api/drafts/zhihu`。
- 草稿箱展示知乎回答结构。

当前领域：

- 品牌公关。
- 消费维权。
- 职场。
- 年轻人生活。
- 文娱传播。

## 重要架构决策

微博候选池和知乎候选池必须拆开。

现有 `CandidatePool` 先视为微博候选池。里面的知乎分、知乎领域字段是过渡方案，后续不要继续往 `CandidatePoolItem` 塞更多知乎字段。

应新增：

- `ZhihuQuestionPool`
- `ZhihuQuestionCandidate`
- `ZhihuQuestionPoolService`

## 候选来源

建议来源：

- 手动添加问题标题/URL。
- 从 TopicAsset 生成问题候选。
- 知乎热榜。
- 知乎搜索。
- 知乎首页 feed。

如果后续使用 Cookie，只读问题候选和可见数据，不做互动。

## 评分重点

知乎评分不应以微博热度为核心。

重点应该是：

- 垂直领域适配。
- 问题质量。
- 关注/浏览与回答供给差。
- 搜索长尾价值。
- 资料支撑。
- 回答空间。
- 风险边界。

## 回答结构

推荐结构：

- `question_title`
- `answer_title`
- `opening_judgement`
- `background_summary`
- `core_argument`
- `supporting_points`
- `counter_arguments`
- `risk_notes`
- `answer_body`
- `references`

## 下一步

新增 Streamlit “知乎问题池”页面：

- 手动添加问题标题/URL。
- 从 TopicAsset 派生问题候选。
- 查看知乎评分。
- 标记 selected。
- 生成知乎回答。

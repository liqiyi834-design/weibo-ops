# 微博产线

## 定位

微博产线负责热点锐评短内容的选题、资料准备和草稿生成。

边界：

- 不自动发微博。
- 不自动评论、转发、点赞、关注。
- 不刷量。
- 不规避平台限制。

## 当前能力

热搜来源：

- 统一入口：`HotSearchService.get_hot_topics(platform="weibo")`
- 实时热搜：`HotSearchService.get_weibo_hot_topics()`
- 文娱榜：`HotSearchService.get_weibo_ent_topics()`

API：

- `GET /api/hot?platform=weibo`
- `GET /api/hot/weibo`
- `POST /api/topics/select`
- `POST /api/topic-candidates/pools`
- `POST /api/research/weibo-aisearch`

MCP：

- `get_hot_topics`
- `get_ent_topics`
- `select_comment_topics`
- `research_weibo_aisearch`

## 评分信号

当前选题推荐考虑：

- 热搜排名。
- 热度数字 `hot_value`。
- 榜单标记 `label`，例如热、新、沸。
- 热搜分类 `category_label`，例如电影、综艺、剧集。
- 二次采样指标：阅读量、讨论量、采样内容数、争议度。
- 微博智搜站内背景摘要和关键点。
- Exa 外部背景检索重排结果。
- 关键词冲突空间。
- 账号适配度。
- 低评论空间惩罚。
- 风险提示。

注意：风险等级不参与评分，只作为提示和表达边界。

## 候选池状态

- `candidate`
- `selected`
- `skipped`
- `researched`

人工选择后才能进入资料补充和草稿生成。

## 后续优化

- 优化微博智搜和 Exa 的来源融合、摘要截断与可信度展示。
- 加强热度字段解析测试。
- 根据运营策略决定是否过滤置顶、政务、低评论空间话题。
- 引入 LLM 二次评审，让推荐理由更像编辑判断。
- 支持从综合池分发回微博候选池。
- 多平台同题聚合后，把百度等公开热榜的跨平台讨论广度作为参考因素。

# 当前进度

## 项目状态

HotComment-AI 已经从单纯微博锐评草稿工具，推进到“少数账号的人机协同内容运营工作台”雏形。

当前可用主链路：

```text
微博热搜
-> 选题评分
-> 候选池
-> 人工多选与状态流转
-> 背景资料人工入库
-> RAG 检索
-> 微博短评/知乎回答草稿
-> 草稿箱人工编辑与发布记录
```

## 已完成能力

### FastAPI

已实现：

- `GET /`
- `GET /health`
- `GET /api/hot/weibo`
- `POST /api/comment/generate`
- `GET /api/comment/personas`
- `GET /api/comment/styles`
- `GET /api/accounts`
- `POST /api/topics/select`
- `POST /api/topic-candidates/pools`
- `GET /api/topic-candidates/pools`
- `GET /api/topic-candidates/pools/{pool_id}`
- `PATCH /api/topic-candidates/pools/{pool_id}/items/{item_id}`
- `POST /api/topic-assets`
- `GET /api/topic-assets`
- `GET /api/topic-assets/{asset_id}`
- `PATCH /api/topic-assets/{asset_id}`
- `POST /api/topic-assets/{asset_id}/routing`
- `POST /api/knowledge/rebuild`
- `POST /api/knowledge/search`
- `POST /api/knowledge/ingest`
- `GET /api/knowledge/inbox`
- `GET /api/knowledge/inbox/{record_id}`
- `POST /api/drafts`
- `GET /api/drafts`
- `GET /api/drafts/{draft_id}`
- `PATCH /api/drafts/{draft_id}`
- `POST /api/zhihu/answer/generate`
- `POST /api/drafts/zhihu`

### 微博热搜

已实现：

- Cookie 抓取微博实时热搜。
- Cookie 失效或登录跳转识别。
- fallback 到可见采样或 mock。
- 文娱榜 `get_weibo_ent_topics()`。
- `category_label` 字段，保存 `电影`、`综艺`、`剧集` 等分类。
- `hot_value` 只保留纯数字热度，避免 `综艺 126022` 混入评分和展示。

### 候选池与选题推荐

已实现：

- 热搜前 50 评分。
- 推荐 3-10 个候选。
- 输出 `score`、`reason`、`risk_level`、`recommended_angle`、`avoid_points`。
- 风险等级不参与评分，只作为提示和表达边界。
- 可选二次采样补充 `read_count`、`discussion_count`、`sampled_posts_count`、`controversy_score`。
- 可选 Exa 背景检索重排：先按硬规则粗筛，再用 Exa 来源和 `TopicRerankService` 重新计算 `rerank_score`、`rerank_decision`、待核验点和来源链接。
- 候选状态：`candidate`、`selected`、`skipped`、`researched`。
- 人工备注 `operator_note`。

### 综合池 TopicAsset

已实现：

- `app/services/topic_asset_service.py`
- 手动创建选题资产。
- 从微博候选池 selected 项加入综合池。
- 查看、更新状态、风险等级、资料状态和摘要。
- LLM 平台分发建议，输出微博、知乎、视频三类去向的分数、建议、理由、阻碍、建议角度和需补资料。
- 高风险话题仍由规则层施加硬约束，不能让 LLM 单独决定发布方向。

当前原则：

- 综合池只保存通用选题资产。
- 微博角度、知乎回答角度、视频分镜不放综合池。
- 由综合池给出平台分发建议，再由人工确认是否进入各平台池。

### Streamlit 工作台

已实现：

- 生成今日热搜候选池。
- 生成候选池时可勾选“启用 Exa 背景检索重排”，重排分、决策、来源数、待核验点会落到候选池详情表。
- 候选池列表与详情。
- 候选题多选与批量状态更新。
- 人工背景资料入库与 RAG 重建。
- Exa 本轮检索结果可在工作台人工勾选后批量入库 RAG。
- 风格记忆库 tab：可粘贴公开或授权文本，提炼风格观察卡，人工确认后入库 RAG。
- 查看入库背景资料。
- 从候选题生成微博草稿或知乎回答草稿。
- 草稿箱查看、编辑、审核状态更新。
- 发布链接、发布时间、复盘备注记录。
- 账号配置与表达风格查看。
- 综合池 tab。
- 综合池详情页可生成并查看 LLM 平台分发建议。

### RAG 与知识库

已实现：

- 本地 hash embedding。
- 可选 OpenAI-compatible embedding。
- `.rag_index/` 本地索引。
- 无向量索引时 fallback 到 `KeywordRetriever`。
- 人工背景资料入库到 `app/knowledge/inbox/`。
- 工作台支持把 Exa 检索到的本轮公开资料转成资料卡，人工选择后入库。
- 风格记忆库写入 `app/knowledge/style_memory/`，用于长期表达风格召回。
- RAG 递归索引 `app/knowledge/**/*.md`。

### MCP

已实现：

- `get_hot_topics`
- `get_ent_topics`
- `select_comment_topics`
- `generate_comment`
- `save_draft`
- `list_drafts`
- `update_draft`
- `rebuild_knowledge`
- `search_knowledge`
- `retrieve_knowledge`
- `extract_style_memory`
- `ingest_style_memory`
- `ingest_knowledge`
- `ingest_current_research`
- `classify_topic`
- `safety_check`
- `research_topic_sources`
- `rerank_topics_with_research`
- `build_generation_context`

启动：

```powershell
python -m mcp_server.server
```

### 多账号与表达风格

已实现：

- `accounts/today_direct.json`
- `app/services/style_service.py`
- `GET /api/accounts`
- `GET /api/comment/styles`
- 生成接口支持 `account_id`、`style`，旧字段 `persona` 暂时兼容。
- 高风险话题自动禁用不合适的高情绪/嘲讽风格。

项目内统一称为“表达风格”，不是“人格”。

### 知乎 MVP

已实现：

- `ZhihuAnswerGenerator`
- `configs/zhihu_domains.json`
- `app/services/zhihu_domain_service.py`
- `app/services/zhihu_topic_fit_service.py`
- 知乎回答生成 API。
- 知乎草稿保存到草稿箱。
- 草稿箱按 `platform`、`draft_type`、`status` 筛选。

## 测试

当前测试：

```text
tests/test_api.py
tests/test_hot_sources.py
tests/test_pipeline.py
tests/test_rag.py
tests/test_safety_checker.py
tests/test_mcp_tools.py
tests/test_candidate_pool.py
tests/test_topic_selection.py
tests/test_topic_research.py
tests/test_style_service.py
tests/test_draft_service.py
tests/test_knowledge_ingestion.py
tests/test_zhihu_domain_service.py
tests/test_topic_asset_service.py
```

最新验证：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

结果：

```text
78 passed
```

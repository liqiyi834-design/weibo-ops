# 项目文档索引

本目录用于承接 HotComment-AI 的产品、技术和 Agent 交接文档。

## 核心方案

- `../AGENTS.md`：当前 Agent 入口、硬规则、项目摘要和常用命令。
- `agent_handbook/README.md`：当前交接分卷入口和阅读顺序。
- `HotComment-AI技术方案.md`：历史完整方案 / 同步整理版，保留产品和技术背景。

如果历史方案与当前实现冲突，以 `AGENTS.md` 和 `agent_handbook/` 当前分卷为准。

## Agent 交接文档

- `agent_handbook/README.md`：分卷说明和阅读顺序。
- `agent_handbook/current_status.md`：当前进度、已完成能力、测试结果。
- `agent_handbook/workflow.md`：候选池、综合池、草稿箱、知识库的实际工作流。
- `agent_handbook/architecture.md`：FastAPI、Streamlit、MCP、RAG 和服务层结构。
- `agent_handbook/backlog.md`：P0-P7 待办和优先级。
- `agent_handbook/hermes_agents.md`：Hermes agents / MCP 自动化编排接入方式和边界。
- `agent_handbook/pitfalls.md`：DeepSeek、代理、Cookie、pytest、Streamlit Cloud 等踩坑记录。
- `agent_handbook/deployment.md`：本地和 Streamlit Community Cloud 部署说明。
- `agent_handbook/platform_weibo.md`：微博产线。
- `agent_handbook/platform_zhihu.md`：知乎产线。
- `agent_handbook/platform_video.md`：视频创意产线。
- `agent_handbook/platform_wechat.md`：微信公众号中长文产线。
- `../deployment/linux/README.md`：Ubuntu 云服务器部署、systemd、Nginx 和 Hermes gateway/cron。

## 可复用资料

以下文件可作为生成、RAG 和规则模块的知识来源：

| 文件 | 用途 |
| --- | --- |
| `legacy_ops/04_人设与风格规则.md` | 表达风格模板和风格化改写规则 |
| `legacy_ops/06_草稿生成提示词.md` | 草稿生成 Prompt 来源 |
| `legacy_ops/08_高热博文公开样本研究.md` | 高互动样本研究 |
| `legacy_ops/10_爆款博文写作公式.md` | 写作结构和选题判断 |
| `legacy_ops/12_事实核查与风险分级.md` | 事实核查和风险表达规则 |
| `legacy_ops/24_高互动正文分析标准.md` | 内容质量评分维度 |
| `../data/weibo_post_samples.csv` | 高互动正文样本 |
| `../data/weibo_samples.csv` | 可见微博样本 |

早期人工运营模板和增长资料已归档到 `legacy_ops/`。这些资料可作知识源参考，不是当前开发入口。

## 边界提醒

项目只做少数账号的人机协同内容运营工作台。AI 辅助选题、资料整理、草稿生成和风险提示；最终选题、审核、修改和发布由人完成。

不做自动发布、自动评论、自动转发点赞、批量互动、刷量、养号矩阵、绕过平台限制或自动引战能力。

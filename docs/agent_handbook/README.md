# Agent Handbook

这是 `AGENTS.md` 的分卷交接区。根目录 `AGENTS.md` 只保留入口、硬规则和当前摘要；细节写在本目录。

阅读顺序建议：

1. `current_status.md`：当前做到哪里、最近验证结果。
2. `workflow.md`：实际运营和产品工作流。
3. `architecture.md`：代码结构、服务边界、API/MCP/RAG/Streamlit。
4. `backlog.md`：下一步优先级。
5. `hermes_agents.md`：Hermes agents / MCP 自动化编排接入方式和边界。
6. `pitfalls.md`：已踩坑和注意事项。
7. `deployment.md`：本地与 Streamlit Community Cloud 部署。
8. 平台分卷：`platform_weibo.md`、`platform_zhihu.md`、`platform_video.md`、`platform_wechat.md`。

维护原则：

- `AGENTS.md` 和本目录分卷是当前 Agent 交接入口。
- `docs/HotComment-AI技术方案.md` 是历史完整方案参考，不作为当前实现的唯一权威。
- 本目录用于让新线程快速接手，不写密钥、Cookie、token 或真实账号隐私。
- 完成核心能力、调整架构、改变部署方式或发现关键坑点时，同步更新对应分卷。

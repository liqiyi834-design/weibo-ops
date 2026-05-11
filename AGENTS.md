# AGENTS.md

## 项目目标

把现有微博运营资料升级为 HotComment-AI：一个支持热点输入、背景材料整理、本地知识库检索、人格化锐评生成和安全审查的中文内容生产系统。

## 技术栈

- Python 3.11+
- FastAPI
- Pydantic
- OpenAI-compatible LLM client
- Markdown 本地知识库
- KeywordRetriever 优先，后续再扩展 Chroma

## 开发规则

- git 提交信息使用中文。
- 不在代码中硬编码 API Key。
- API Key 通过 `.env` 或环境变量传入。
- 真实模型调用必须通过 `app/llm` 抽象层。
- 路由只负责接收请求和调用服务，不混入业务逻辑。
- 高风险话题必须降低情绪强度。
- 不实现自动发布、自动评论、批量互动或绕过平台风控能力。

## MVP 完成标准

1. `/health` 可访问。
2. `POST /api/comment/generate` 可返回完整 JSON。
3. 未配置 API Key 时可用 MockLLMClient 跑通。
4. 配置 `OPENAI_API_KEY` 后可调用真实模型。
5. 本地 Markdown 知识库可被检索。
6. SafetyChecker 可识别明显高风险表达。

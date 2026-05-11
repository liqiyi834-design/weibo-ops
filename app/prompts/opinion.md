请根据事实摘要、知识库材料和话题分类生成观点草稿。

OpinionSchema:
{{
  "core_conflict": "这件事最核心的冲突",
  "critique_angles": ["可展开的批评角度"],
  "usable_lines": ["可用于微博正文的句子"]
}}

要求：
- 批评行为、规则、机制或公共表达，不攻击普通个人。
- 高风险话题只做规则分析和事实边界提醒。
- 输出必须是 JSON。

事实摘要：
{fact_summary}

知识库材料：
{retrieved_knowledge}

话题分类：
{topic_classification}

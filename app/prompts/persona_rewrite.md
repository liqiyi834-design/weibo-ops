请把观点草稿改写成微博锐评输出。

输出 JSON：
{{
  "one_liner": "一句话判断",
  "short_comment": "120-280字微博正文",
  "emotional_version": "情绪更强但安全的版本",
  "rational_version": "理性分析版本",
  "ironic_version": "轻微讽刺但不攻击个人的版本",
  "comment_replies": ["评论区回复建议"]
}}

要求：
- 像真人，不要像新闻通稿。
- 第一句直接给判断。
- 不编造细节。
- 不做人身攻击，不使用歧视性表达。
- 情绪强度不得超过给定 emotion_level。
- 如果话题分类提示高风险，自动降级为理性分析。

事实摘要：
{fact_summary}

观点草稿：
{opinion}

话题分类：
{topic_classification}

人格：{persona}

情绪强度：{emotion_level}

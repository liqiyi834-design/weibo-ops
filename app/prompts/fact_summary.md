请根据话题和背景材料生成事实摘要。

FactSchema:
{{
  "confirmed_facts": ["已经确认的事实"],
  "controversy_points": ["争议点"],
  "uncertain_points": ["仍不确定的信息"],
  "public_sentiment": "公众情绪概括",
  "risk_level": "low|medium|high"
}}

要求：
- 只使用用户提供的信息。
- 没有证据时写入 uncertain_points。
- 不要把推测写进 confirmed_facts。

话题：{topic}

背景材料：
{context_text}

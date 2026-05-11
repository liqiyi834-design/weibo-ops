from app.schemas.comment import FactSummary, TopicClassification


class TopicClassifier:
    def classify(self, topic: str, context_text: str, fact_summary: FactSummary) -> TopicClassification:
        text = f"{topic} {context_text}".lower()
        rules = [
            ("minor_related", ["未成年", "儿童", "学生", "孩子"], "rational_critic", 4),
            ("crime_case", ["警方", "刑事", "犯罪", "判决", "法院"], "rational_critic", 4),
            ("disaster", ["死亡", "灾难", "事故", "地震", "火灾"], "rational_critic", 4),
            ("political_sensitive", ["政治", "外交", "选举"], "rational_critic", 3),
            ("gender_issue", ["性别", "女性", "男性", "母职", "婚育"], "ironic_observer", 6),
            ("brand_pr", ["品牌", "公关", "广告", "文案", "客服"], "pr_critic", 7),
            ("entertainment", ["明星", "粉丝", "综艺", "电影"], "ironic_observer", 8),
            ("social_issue", ["平台", "消费", "职场", "外卖", "教育"], "rational_critic", 7),
        ]
        for category, keywords, persona, max_emotion in rules:
            if any(keyword in text for keyword in keywords):
                notes = []
                if max_emotion <= 4:
                    notes.append("高风险话题，建议降低情绪强度并避免嘲讽。")
                return TopicClassification(
                    category=category,
                    recommended_persona=persona,
                    max_emotion_level=max_emotion,
                    risk_notes=notes,
                )
        return TopicClassification()

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.comment import AccountConfig, StyleInfo, TopicClassification


STYLE_CATALOG = [
    StyleInfo(
        id="rational_critic",
        name="理性拆解型",
        description="先稳住事实，再拆责任边界和规则漏洞。",
        best_for=["social_issue", "crime_case", "disaster", "minor_related", "political_sensitive"],
    ),
    StyleInfo(
        id="ironic_observer",
        name="阴阳怪气型",
        description="用轻讽刺和反差表达观点，适合中低风险文娱和生活议题。",
        best_for=["entertainment", "social_issue"],
    ),
    StyleInfo(
        id="pr_critic",
        name="公关毒舌观察者",
        description="从品牌、公关、舆论危机和用户感受切入。",
        best_for=["brand_pr", "social_issue"],
    ),
    StyleInfo(
        id="angry_netizen",
        name="暴躁网友型",
        description="强情绪吐槽风格，只适合低风险生活和消费类话题。",
        best_for=["social_issue", "brand_pr"],
    ),
]


class StyleService:
    def __init__(self, accounts_dir: Path | str = Path("accounts")):
        self.accounts_dir = Path(accounts_dir)

    def list_styles(self) -> list[StyleInfo]:
        return STYLE_CATALOG

    def list_accounts(self) -> list[AccountConfig]:
        if not self.accounts_dir.exists():
            return [self.default_account()]
        accounts = [
            AccountConfig(**json.loads(path.read_text(encoding="utf-8")))
            for path in self.accounts_dir.glob("*.json")
        ]
        return accounts or [self.default_account()]

    def get_account(self, account_id: str) -> AccountConfig:
        for account in self.list_accounts():
            if account.id == account_id:
                return account
        raise FileNotFoundError(f"Account config not found: {account_id}")

    def resolve_style(
        self,
        account_id: str,
        requested_style: str | None,
        classification: TopicClassification,
    ) -> tuple[str, list[str]]:
        account = self.get_account(account_id)
        notes: list[str] = []
        style = requested_style or classification.recommended_persona or account.default_style

        if style not in account.allowed_styles:
            notes.append(f"风格 {style} 不在账号允许列表中，已改用默认风格 {account.default_style}。")
            style = account.default_style

        is_high_risk = classification.max_emotion_level <= 4
        if is_high_risk and style in account.blocked_styles_for_high_risk:
            notes.append(f"高风险话题不使用 {style}，已改用理性拆解型。")
            style = "rational_critic"

        return style, notes

    def default_account(self) -> AccountConfig:
        return AccountConfig(
            id="today_direct",
            name="今日有话直说",
            positioning="社会热点与公共话题锐评账号。",
            default_style="rational_critic",
            allowed_styles=["rational_critic", "ironic_observer", "pr_critic", "angry_netizen"],
            blocked_styles_for_high_risk=["angry_netizen", "ironic_observer"],
            preferred_topics=["social_issue", "brand_pr", "entertainment"],
        )

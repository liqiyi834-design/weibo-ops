from app.schemas.comment import TopicClassification
from app.services.style_service import StyleService


def test_style_service_lists_default_account_and_styles():
    service = StyleService()

    styles = service.list_styles()
    account = service.get_account("today_direct")

    assert any(style.id == "rational_critic" for style in styles)
    assert account.default_style == "rational_critic"
    assert "angry_netizen" in account.allowed_styles


def test_style_service_blocks_high_risk_style():
    service = StyleService()
    classification = TopicClassification(
        category="crime_case",
        recommended_persona="rational_critic",
        max_emotion_level=4,
    )

    style, notes = service.resolve_style(
        account_id="today_direct",
        requested_style="angry_netizen",
        classification=classification,
    )

    assert style == "rational_critic"
    assert notes

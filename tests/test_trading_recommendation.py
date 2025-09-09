from pogorarity import get_trading_recommendation


def test_trading_recommendation_special_cases():
    assert get_trading_recommendation(5.0, "legendary") == "Never Transfer (Legendary)"
    assert get_trading_recommendation(5.0, "event-only") == "Never Transfer (Event Only)"
    assert get_trading_recommendation(5.0, "evolution-only") == "Evaluate for Evolution"


def test_trading_recommendation_ranges():
    assert get_trading_recommendation(1.0, "wild") == "Should Always Trade"
    assert get_trading_recommendation(3.5, "wild") == "Should Always Trade"
    assert get_trading_recommendation(4.0, "wild") == "Depends on Circumstances"
    assert get_trading_recommendation(6.5, "wild") == "Depends on Circumstances"
    assert get_trading_recommendation(7.0, "wild") == "Safe to Transfer"
    assert get_trading_recommendation(9.5, "wild") == "Safe to Transfer"

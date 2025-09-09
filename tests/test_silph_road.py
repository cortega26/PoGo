import pytest

from pogorarity.sources import silph_road


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


def test_silph_road_mapping(monkeypatch):
    sample_data = [{"name": "Bulbasaur", "tier": 5}]
    monkeypatch.setattr(
        silph_road,
        "safe_request",
        lambda url, session=None, metrics=None: DummyResponse(sample_data),
    )
    data, report = silph_road.scrape_spawn_tiers()
    assert report.success
    assert data["Bulbasaur"] == pytest.approx(
        silph_road.SILPH_ROAD_TIER_MAPPING[5]
    )

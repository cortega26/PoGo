import logging
import pytest

from pogorarity.scaling import scale_records


def test_structured_spawn_out_of_range(caplog):
    records = [("Pikachu", 5), ("Mewtwo", 25)]
    with caplog.at_level(logging.WARNING):
        result = scale_records(records, 0, 20, False)
    assert "outside expected range" in caplog.text
    assert result["Pikachu"] == pytest.approx(2.5)
    assert result["Mewtwo"] == 10.0


def test_structured_spawn_auto_scale(caplog):
    records = [("Pikachu", 5), ("Mewtwo", 25)]
    with caplog.at_level(logging.WARNING):
        result = scale_records(records, 0, 20, True)
    assert "outside expected range" in caplog.text
    assert result["Pikachu"] == pytest.approx(2.0)
    assert result["Mewtwo"] == pytest.approx(10.0)


def test_pokemondb_out_of_range(caplog):
    records = [("Pidgey", 300)]
    with caplog.at_level(logging.WARNING):
        result = scale_records(records, 0, 255, False)
    assert "outside expected range" in caplog.text
    assert result["Pidgey"] == 10.0


def test_structured_spawn_discard_out_of_range(caplog):
    records = [("Pikachu", 5), ("Mewtwo", 25)]
    with caplog.at_level(logging.WARNING):
        result = scale_records(
            records, 0, 20, False, on_out_of_range="discard"
        )
    assert "outside expected range" in caplog.text
    assert "Discarding" in caplog.text
    assert result == {"Pikachu": pytest.approx(2.5)}

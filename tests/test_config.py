import json
from pathlib import Path

from pogorarity import thresholds, aggregator
from pogorarity.config import apply_config, load_config


def test_apply_config_overrides(tmp_path):
    cfg_path = tmp_path / "cfg.json"
    spawn_path = tmp_path / "spawn.json"
    spawn_path.write_text("{}", encoding="utf-8")
    cfg = {
        "thresholds": {"common": 8.0, "uncommon": 5.0, "rare": 3.0},
        "weights": {"PokemonDB Catch Rate": 5.0},
        "spawn_types_path": str(spawn_path),
    }
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    orig_thresholds = thresholds.get_thresholds()
    orig_weights = aggregator.SOURCE_WEIGHTS.copy()
    orig_spawn_path = aggregator.SPAWN_TYPES_PATH

    apply_config(load_config(cfg_path))

    assert thresholds.COMMON == 8.0
    assert thresholds.UNCOMMON == 5.0
    assert thresholds.RARE == 3.0
    assert aggregator.SOURCE_WEIGHTS["PokemonDB Catch Rate"] == 5.0
    assert aggregator.SPAWN_TYPES_PATH == spawn_path

    # restore
    aggregator.SOURCE_WEIGHTS = orig_weights
    aggregator.SPAWN_TYPES_PATH = orig_spawn_path
    thresholds.apply_thresholds(orig_thresholds)

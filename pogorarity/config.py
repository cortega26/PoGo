"""Configuration helpers for adjusting rarity parameters."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Dict, Optional

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from *path* if it exists.

    Parameters
    ----------
    path:
        Optional path to a JSON configuration file. When omitted the function
        looks for ``config.json`` in the repository root.  Any errors while
        reading the file result in an empty config dictionary.
    """

    cfg_path = path or DEFAULT_CONFIG_PATH
    try:
        with open(cfg_path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def apply_config(config: Dict[str, Any]) -> None:
    """Apply configuration values to global modules.

    Supported keys in *config*:

    ``thresholds``: mapping passed to :func:`pogorarity.thresholds.apply_thresholds`.
    ``weights``: mapping merged into :mod:`pogorarity.aggregator` SOURCE_WEIGHTS.
    ``spawn_types_path``: path to a JSON file describing spawn type categories.
    """

    from . import aggregator, thresholds

    thresholds_cfg = config.get("thresholds")
    if isinstance(thresholds_cfg, dict):
        thresholds.apply_thresholds(thresholds_cfg)

    weights_cfg = config.get("weights")
    if isinstance(weights_cfg, dict):
        aggregator.SOURCE_WEIGHTS.update({str(k): float(v) for k, v in weights_cfg.items()})

    spawn_path = config.get("spawn_types_path")
    if spawn_path:
        aggregator.SPAWN_TYPES_PATH = Path(spawn_path)
        aggregator._SPAWN_TYPES = None  # reload mapping on next access

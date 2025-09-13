from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Set, Tuple

DEFAULT_LOG_PATH = Path.home() / ".pogorarity" / "caught.log"
COMPACT_EVERY = 100


def append_event(
    pid: int,
    op: str,
    path: Path = DEFAULT_LOG_PATH,
    *,
    compact_every: int = COMPACT_EVERY,
    timestamp: float | None = None,
) -> None:
    """Append a toggle event to ``path``.

    Parameters
    ----------
    pid:
        Pokémon ID to toggle.
    op:
        Either ``"add"`` or ``"remove"``.
    path:
        Log file to append to.
    compact_every:
        Compact the log after this many events.
    timestamp:
        Optional event timestamp; defaults to ``time.time()``.
    """

    if timestamp is None:
        timestamp = time.time()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"op": op, "id": pid, "ts": timestamp}) + "\n")
    try:
        if compact_every and sum(1 for _ in path.open("r", encoding="utf-8")) > compact_every:
            compact(path)
    except FileNotFoundError:
        pass


def append_toggle(
    pid: int,
    checked: bool,
    path: Path = DEFAULT_LOG_PATH,
    *,
    compact_every: int = COMPACT_EVERY,
) -> None:
    """Append an add/remove event based on ``checked``."""

    op = "add" if checked else "remove"
    append_event(pid, op, path=path, compact_every=compact_every)


def load(path: Path = DEFAULT_LOG_PATH) -> Tuple[Set[int], int]:
    """Fold all events in ``path`` and return the resulting set and version."""

    ids: Set[int] = set()
    count = 0
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                count += 1
                evt = json.loads(line)
                if evt.get("op") == "add":
                    ids.add(int(evt["id"]))
                elif evt.get("op") == "remove":
                    ids.discard(int(evt["id"]))
    except FileNotFoundError:
        pass
    return ids, count


def compact(path: Path = DEFAULT_LOG_PATH) -> None:
    """Rewrite ``path`` with a minimal set of add events."""

    ids, _ = load(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = time.time()
    with path.open("w", encoding="utf-8") as f:
        for pid in sorted(ids):
            f.write(json.dumps({"op": "add", "id": pid, "ts": ts}) + "\n")

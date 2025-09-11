from __future__ import annotations

import threading
from typing import Iterable, Set, Tuple

from app.diag.latency import maybe_sleep
from app.diag.tracer import trace

_store_ids: Set[int] = set()
_store_ver: int = 0


def reset() -> None:
    global _store_ids, _store_ver
    _store_ids = set()
    _store_ver = 0


def persist(ids: Iterable[int], ver: int, delay: bool = True) -> threading.Thread:
    ids = set(ids)

    def _commit() -> None:
        trace("persist_start", ver=ver, size=len(ids))
        if delay:
            maybe_sleep()
        global _store_ids, _store_ver
        _store_ids = set(ids)
        _store_ver = ver
        trace("persist_ok", ver=ver, size=len(ids))

    t = threading.Thread(target=_commit)
    t.start()
    return t


def load() -> Tuple[Set[int], int]:
    trace("load", ver=_store_ver, size=len(_store_ids))
    return set(_store_ids), _store_ver

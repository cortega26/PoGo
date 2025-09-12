from __future__ import annotations

import threading
from typing import Iterable, Set

from app.diag.latency import maybe_sleep
from app.diag.tracer import trace

_store_ids: Set[int] = set()


def reset() -> None:
    global _store_ids
    _store_ids = set()


def persist(ids: Iterable[int], delay: bool = True) -> threading.Thread:
    ids = set(ids)

    def _commit() -> None:
        trace("persist_start", size=len(ids))
        if delay:
            maybe_sleep()
        global _store_ids
        _store_ids = set(ids)
        trace("persist_ok", size=len(ids))

    t = threading.Thread(target=_commit)
    t.start()
    return t


def load() -> Set[int]:
    trace("load", size=len(_store_ids))
    return set(_store_ids)

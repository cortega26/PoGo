from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Iterable, Set, Tuple

from app.diag.latency import maybe_sleep
from app.diag.tracer import trace

_LOCK = threading.Lock()


def _ensure_conn(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    with conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS meta (ver INTEGER)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS caught (id INTEGER PRIMARY KEY)")
        cur = conn.execute("SELECT COUNT(*) FROM meta")
        if cur.fetchone()[0] == 0:
            conn.execute("INSERT INTO meta (ver) VALUES (0)")
    return conn


def reset(path: Path) -> None:
    if path.exists():
        path.unlink()


def persist(ids: Iterable[int], ver: int, path: Path, delay: bool = True) -> threading.Thread:
    ids = set(ids)

    def _commit() -> None:
        trace("persist_start", ver=ver, size=len(ids))
        if delay:
            maybe_sleep()
        conn = _ensure_conn(path)
        try:
            with _LOCK:
                cur_ver = conn.execute("SELECT ver FROM meta").fetchone()[0]
                if ver > cur_ver:
                    conn.execute("DELETE FROM caught")
                    conn.executemany(
                        "INSERT INTO caught(id) VALUES (?)",
                        [(i,) for i in ids],
                    )
                    conn.execute("UPDATE meta SET ver=?", (ver,))
                    conn.commit()
        finally:
            conn.close()
        trace("persist_ok", ver=ver, size=len(ids))

    t = threading.Thread(target=_commit)
    t.start()
    return t


def load(path: Path) -> Tuple[Set[int], int]:
    conn = _ensure_conn(path)
    try:
        rows = conn.execute("SELECT id FROM caught").fetchall()
        ids = {row[0] for row in rows}
        ver = conn.execute("SELECT ver FROM meta").fetchone()[0]
        trace("load", ver=ver, size=len(ids))
        return ids, ver
    finally:
        conn.close()

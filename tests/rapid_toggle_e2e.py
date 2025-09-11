from types import SimpleNamespace
import pathlib
import sys


class Session(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.backend import mock_store  # noqa: E402
from app.state.selection import ensure_session_state, toggle_and_bump  # noqa: E402


def main() -> None:
    st = SimpleNamespace(session_state=Session())
    ensure_session_state(st)
    mock_store.reset()
    threads = []
    for pid in range(1, 21):
        st.session_state[f"caught_{pid}"] = True
        ver, ids = toggle_and_bump(st, pid, True)
        threads.append(mock_store.persist(ids, ver, delay=(pid % 2 == 0)))
    for t in threads:
        t.join()
    ids, ver = mock_store.load()
    assert ids == st.session_state.caught_ids, "backend lost some selections"


if __name__ == "__main__":
    main()

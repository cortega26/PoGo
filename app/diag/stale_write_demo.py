import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from app.backend import mock_store  # noqa: E402
from app.diag.tracer import trace  # noqa: E402


def main() -> None:
    mock_store.reset()
    t1 = mock_store.persist({1}, 1, delay=True)
    t2 = mock_store.persist({1, 2}, 2, delay=False)
    t1.join()
    t2.join()
    ids, ver = mock_store.load()
    trace("diag_complete", ver=ver, ids=sorted(ids))
    assert ver == 2, "stale write overwrote newer state"


if __name__ == "__main__":
    main()

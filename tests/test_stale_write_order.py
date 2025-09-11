from app.backend import mock_store


def test_stale_write_order():
    mock_store.reset()
    t1 = mock_store.persist({1}, 1, delay=True)
    t2 = mock_store.persist({1, 2}, 2, delay=False)
    t1.join()
    t2.join()
    ids, ver = mock_store.load()
    assert ver == 2, "older write overwrote newer state"

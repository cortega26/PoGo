from app.backend import sql_store


def test_stale_write_order_sql(tmp_path):
    db = tmp_path / "caught.db"
    sql_store.reset(db)
    t1 = sql_store.persist({1}, 1, db, delay=True)
    t2 = sql_store.persist({1, 2}, 2, db, delay=False)
    t1.join()
    t2.join()
    ids, ver = sql_store.load(db)
    assert ver == 2, "older write overwrote newer state"

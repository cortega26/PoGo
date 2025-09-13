import threading
import time

import streamlit as st

import app
from app.backend import sql_store


def test_stale_write_order_save_caught(tmp_path, monkeypatch):
    st.session_state.clear()
    db = tmp_path / "caught.db"
    monkeypatch.setattr(app, "CAUGHT_DIR", tmp_path)
    monkeypatch.setattr(app.app_module, "CAUGHT_DIR", tmp_path)
    monkeypatch.setattr(app, "CAUGHT_DB", db)
    monkeypatch.setattr(app.app_module, "CAUGHT_DB", db)
    sql_store.reset(db)
    st.session_state.caught_set = set()
    st.session_state.selection_version = 0
    st.session_state.caught_saved_version = 0

    original_persist = app.sql_store.persist
    call = {"count": 0}

    def slow_persist(ids, ver, path, delay=False):
        if call["count"] == 0:
            time.sleep(0.1)
        call["count"] += 1
        return original_persist(ids, ver, path, delay=False)

    monkeypatch.setattr(app.sql_store, "persist", slow_persist)

    def persist(caught, version):
        def run():
            st.session_state.caught_set = caught
            st.session_state.selection_version = version
            app.save_caught(caught)
        t = threading.Thread(target=run)
        t.start()
        return t

    t1 = persist({"Bulbasaur"}, 1)
    time.sleep(0.01)
    t2 = persist({"Bulbasaur", "Chikorita"}, 2)
    t1.join()
    t2.join()

    ids, ver = sql_store.load(db)
    assert ids == {"Bulbasaur", "Chikorita"}
    assert st.session_state.caught_saved_version == 2

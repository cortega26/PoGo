from multiprocessing import Process

import streamlit as st

import app
from app.backend import sql_store


def _save(tmp_dir, names, version):
    import app
    import streamlit as st
    from app.backend import sql_store

    db = tmp_dir / "caught.db"
    app.CAUGHT_DIR = tmp_dir
    app.app_module.CAUGHT_DIR = tmp_dir
    app.CAUGHT_DB = db
    app.app_module.CAUGHT_DB = db
    st.session_state.clear()
    st.session_state.caught_set = set(names)
    st.session_state.selection_version = version
    app.save_caught(set(names))


def test_save_caught_across_processes(tmp_path):
    db = tmp_path / "caught.db"
    sql_store.reset(db)

    p1 = Process(target=_save, args=(tmp_path, {"Bulbasaur"}, 1))
    p2 = Process(target=_save, args=(tmp_path, {"Bulbasaur", "Chikorita"}, 2))
    p1.start()
    p2.start()
    p1.join()
    p2.join()

    ids, ver = sql_store.load(db)
    assert ids == {"Bulbasaur", "Chikorita"}
    assert ver == 2

import json
import threading
import time
from pathlib import Path

import streamlit as st

import app


def test_stale_write_order_save_caught(tmp_path, monkeypatch):
    st.session_state.clear()
    monkeypatch.setattr(app, "CAUGHT_DIR", tmp_path)
    monkeypatch.setattr(app.app_module, "CAUGHT_DIR", tmp_path)
    monkeypatch.setattr(app, "CAUGHT_FILE", tmp_path / "caught.json")
    monkeypatch.setattr(app.app_module, "CAUGHT_FILE", tmp_path / "caught.json")
    st.session_state.caught_set = set()
    st.session_state.selection_version = 0
    st.session_state.caught_saved_version = 0

    original_write = Path.write_text

    def slow_write(self, *args, **kwargs):
        time.sleep(0.1)
        return original_write(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", slow_write)

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

    data = json.loads(app.CAUGHT_FILE.read_text())
    assert data == ["Bulbasaur", "Chikorita"]
    assert st.session_state.caught_saved_version == 2

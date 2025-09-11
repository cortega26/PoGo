from pathlib import Path

import pandas as pd
import streamlit as st
import threading
import time

import app


def test_apply_caught_edits_merges_changes(monkeypatch):
    st.session_state.clear()
    st.session_state.caught_set = set()

    saved = {}

    def fake_save(caught: set[str]) -> None:
        saved["caught"] = set(caught)

    monkeypatch.setattr(app, "save_caught", fake_save)

    df = pd.DataFrame({"Name": ["Bulbasaur", "Chikorita"], "Caught": [False, False]})

    edited = df.copy()
    edited.loc[0, "Caught"] = True
    app.apply_caught_edits(df, edited)
    assert st.session_state.caught_set == {"Bulbasaur"}

    # Simulate a rapid second edit where only the second row changes
    df2 = edited.copy()
    edited2 = df2.copy()
    edited2.loc[1, "Caught"] = True
    app.apply_caught_edits(df2, edited2)
    assert st.session_state.caught_set == {"Bulbasaur", "Chikorita"}

    # Unmark the first Pokémon
    df3 = edited2.copy()
    edited3 = df3.copy()
    edited3.loc[0, "Caught"] = False
    app.apply_caught_edits(df3, edited3)
    assert st.session_state.caught_set == {"Chikorita"}

    # Ensure save_caught was invoked with the latest state
    assert saved["caught"] == {"Chikorita"}


def test_caught_file_path():
    expected = Path.home() / ".pogorarity" / "caught_pokemon.json"
    assert app.CAUGHT_FILE == expected


def test_apply_caught_edits_many_rows():
    st.session_state.clear()
    st.session_state.caught_set = set()

    names = [f"Poke{i}" for i in range(12)]
    base = pd.DataFrame({"Name": names, "Caught": [False] * 12})

    original = base.copy()
    for i in range(10):
        edited = original.copy()
        edited.loc[i, "Caught"] = True
        app.apply_caught_edits(original, edited)
        original = edited

    assert st.session_state.caught_set == set(names[:10])


def test_apply_caught_edits_race_condition(monkeypatch):
    st.session_state.clear()
    st.session_state.caught_set = set()

    saved = {}

    def slow_save(caught: set[str]) -> None:
        time.sleep(0.1)
        saved["caught"] = set(caught)

    monkeypatch.setattr(app, "save_caught", slow_save)

    df = pd.DataFrame({"Name": ["Bulbasaur", "Chikorita"], "Caught": [False, False]})
    edited1 = df.copy()
    edited1.loc[0, "Caught"] = True

    thread = threading.Thread(target=app.apply_caught_edits, args=(df, edited1))
    thread.start()
    time.sleep(0.01)

    edited2 = df.copy()
    edited2.loc[1, "Caught"] = True
    app.apply_caught_edits(df, edited2)
    thread.join()

    assert st.session_state.caught_set == {"Bulbasaur", "Chikorita"}
    assert saved["caught"] == {"Bulbasaur", "Chikorita"}


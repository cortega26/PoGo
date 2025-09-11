import pandas as pd
import streamlit as st

import app


def test_apply_caught_edits_merges_changes(monkeypatch):
    st.session_state.clear()
    st.session_state.caught_set = set()

    saved = {}

    def fake_save(caught: set[str]) -> None:
        saved["caught"] = set(caught)

    monkeypatch.setattr(app, "save_caught", fake_save)

    df = pd.DataFrame({"Name": ["Bulbasaur", "Chikorita"]})

    app.apply_caught_edits(df, {"edited_rows": {"0": {"Caught": True}}})
    assert st.session_state.caught_set == {"Bulbasaur"}

    # Simulate a rapid second edit where the frontend only sends the second row
    app.apply_caught_edits(df, {"edited_rows": {"1": {"Caught": True}}})
    assert st.session_state.caught_set == {"Bulbasaur", "Chikorita"}

    # Unmark the first Pokémon
    app.apply_caught_edits(df, {"edited_rows": {"0": {"Caught": False}}})
    assert st.session_state.caught_set == {"Chikorita"}

    # Ensure save_caught was invoked with the latest state
    assert saved["caught"] == {"Chikorita"}


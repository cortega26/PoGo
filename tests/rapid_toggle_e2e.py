import time
import pandas as pd
import streamlit as st
import app

def main() -> None:
    st.write("Rapid toggle demo")
    st.session_state.clear()
    st.session_state.caught_set = set()
    st.session_state.selection_version = 0

    base = pd.DataFrame({"Name": [f"Poke{i}" for i in range(20)], "Caught": [False] * 20})
    edited = base.copy()
    for i in range(20):
        edited.loc[i, "Caught"] = True
        app.apply_caught_edits(base, edited)
        time.sleep(0.05)

    st.write("Final caught set:", sorted(st.session_state.caught_set))
    st.write("Selection version:", st.session_state.selection_version)

if __name__ == "__main__":
    main()

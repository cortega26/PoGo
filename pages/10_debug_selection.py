import streamlit as st

from app.backend.mock_store import load, persist
from app.diag.tracer import trace
from app.state.selection import ensure_session_state, toggle_and_bump


def load_pokemon():
    return [{"id": i, "name": f"Pokemon {i}"} for i in range(1, 31)]


ensure_session_state(st)
pokemon_list = load_pokemon()

simulate_latency = st.sidebar.checkbox("simulate backend latency", value=False)


def on_change(pid: int):
    checked = st.session_state[f"caught_{pid}"]
    ver, ids = toggle_and_bump(st, pid, checked)
    trace("toggle", pid=pid, checked=checked, ver=ver, size=len(ids))
    if simulate_latency:
        persist(ids, ver)


st.title("Debug: Selection State")
st.caption("Instrumented page. No fixes here—only observation.")

for p in sorted(pokemon_list, key=lambda x: x["id"]):
    st.checkbox(
        label=p["name"],
        key=f"caught_{p['id']}",
        value=(p["id"] in st.session_state.caught_ids),
        on_change=on_change,
        args=(p["id"],),
    )

server_ids, server_ver = load()
trace("render", ver=st.session_state.sel_ver, size=len(st.session_state.caught_ids))
trace("backend_state", server_ver=server_ver, server_size=len(server_ids))

st.json(
    {
        "sel_ver": st.session_state.sel_ver,
        "caught_ids": sorted(st.session_state.caught_ids),
        "server_ver": server_ver,
        "server_ids": sorted(server_ids),
    }
)

from typing import Iterable, Set, Tuple


def ensure_session_state(st) -> None:
    if "caught_ids" not in st.session_state:
        st.session_state.caught_ids = set()  # type: Set[int]
    if "sel_ver" not in st.session_state:
        st.session_state.sel_ver = 0
    if "last_committed_ver" not in st.session_state:
        st.session_state.last_committed_ver = 0


def toggle_and_bump(st, pid: int, checked: bool) -> Tuple[int, Set[int]]:
    ids = set(st.session_state.caught_ids)
    if checked:
        ids.add(pid)
    else:
        ids.discard(pid)
    st.session_state.caught_ids = ids
    st.session_state.sel_ver += 1
    return st.session_state.sel_ver, ids

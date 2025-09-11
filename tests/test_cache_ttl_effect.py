import time
import streamlit as st


@st.cache_data(ttl=0.1)
def cached() -> float:
    return time.time()


def test_cache_ttl_effect():
    first = cached()
    time.sleep(0.2)
    second = cached()
    assert first == second, "cache refreshed and flipped state"

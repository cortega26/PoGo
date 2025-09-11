import json
import time
import sys
from typing import Any, Dict


def jdump(obj: Any):
    try:
        return json.dumps(obj, default=str, sort_keys=True)
    except Exception as e:
        return f"<nonjson:{type(obj).__name__}:{e}>"


def trace(tag: str, **kvs: Dict[str, Any]):
    ts = time.time()
    line = f"{ts:.3f} [{tag}] {jdump(kvs)}"
    print(line, file=sys.stdout, flush=True)
    try:
        import streamlit as st

        st.markdown(
            f"**🧭 {ts:.3f} [{tag}]**\n\n```json\n{jdump(kvs)}\n```"
        )
    except Exception:
        pass

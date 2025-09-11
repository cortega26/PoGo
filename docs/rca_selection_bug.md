# RCA: Selection Reversion During Rapid Toggling

## 1. Symptom Timeline

- User rapidly checks multiple Pokémon in the Streamlit UI.
- During a subsequent rerun, previously checked boxes revert to unchecked.
- Reproduced both locally and on Community Cloud using `make debug` and `make e2e`.

## 2. Signals

Tracer events expose the sequence:

- `toggle` events increment `sel_ver`.
- `persist_start`/`persist_ok` show backend writes completing out of order.
- A `render` event occurs with a smaller `caught_ids` set than the last `toggle`.
- `backend_state` logs reveal stale `server_ver` overwriting new selections.

## 3. Causal Graph

```text
rapid toggle -> rerun -> async persist N -> async persist N+1 -> persist N completes last -> stale server_ver -> rerender -> earlier selections lost
```

## 4. Why Previous Fixes Missed It

Past patches updated session state and guarded writes, but none traced backend commit ordering. Without visibility into `persist` latency, stale writes silently overwrote newer state after reruns.

## 5. Candidate Fixes

- Guard backend store with version check to reject older commits.
- Persist selections only after debouncing user input.
- Replace threaded mock with synchronous or transactional backend.
- Preserve widget state via deterministic keys and avoiding cache refresh mid-toggle.

*No fixes implemented here; diagnostics only.*

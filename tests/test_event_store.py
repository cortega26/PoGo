from app.backend import event_store


def test_interleaved_events(tmp_path):
    log = tmp_path / "events.log"
    # sequence of add/remove events
    event_store.append_event(1, "add", path=log)
    event_store.append_event(2, "add", path=log)
    event_store.append_event(1, "remove", path=log)
    event_store.append_event(3, "add", path=log)
    event_store.append_event(2, "remove", path=log)
    event_store.append_event(1, "add", path=log)
    ids, ver = event_store.load(log)
    assert ids == {1, 3}
    # version equals number of events processed
    assert ver == 6


def test_compaction(tmp_path):
    log = tmp_path / "events.log"
    for _ in range(6):
        event_store.append_event(1, "add", path=log, compact_every=5)
        event_store.append_event(1, "remove", path=log, compact_every=5)
    ids, _ = event_store.load(log)
    assert ids == set()
    # after compaction log should be empty
    assert log.exists()
    assert log.read_text() == ""

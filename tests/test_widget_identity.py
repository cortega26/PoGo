import pytest


def rebuild(keys):
    return [f"caught_{k}" for k in sorted(keys)]


def test_widget_identity():
    first = rebuild([1, 2, 3])
    second = rebuild([3, 2, 1])
    assert first == second, "widget keys changed with reordering"

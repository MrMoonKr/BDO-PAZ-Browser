from __future__ import annotations

import pytest

import _common.node as node
from _common.lookup_index import IndexKind, clear_indexes, init_index

_SUB_NODE = 2070
_PARENT = 1328
_NAMES = {_SUB_NODE: "Mining", _PARENT: "Bambu Valley"}


@pytest.fixture(autouse=True)
def _loc_names(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(node, "node_name", lambda key: _NAMES.get(key, ""))
    clear_indexes()
    yield
    clear_indexes()


def test_sub_node_name_starts_with_its_parent() -> None:
    init_index(IndexKind.NODE_PARENT, {_SUB_NODE: _PARENT})
    assert node.full_node_name(_SUB_NODE) == "Bambu Valley - Mining"


def test_main_node_keeps_its_own_name() -> None:
    init_index(IndexKind.NODE_PARENT, {_SUB_NODE: _PARENT})
    assert node.full_node_name(_PARENT) == "Bambu Valley"


def test_sub_node_without_the_index_keeps_its_own_name() -> None:
    assert node.full_node_name(_SUB_NODE) == "Mining"


def test_parent_without_a_name_is_left_out() -> None:
    init_index(IndexKind.NODE_PARENT, {_SUB_NODE: 9999})
    assert node.full_node_name(_SUB_NODE) == "Mining"


def test_node_without_a_name_has_none() -> None:
    init_index(IndexKind.NODE_PARENT, {4242: _PARENT})
    assert node.full_node_name(4242) == ""


def test_node_with_parent_name_joins_both_names() -> None:
    init_index(IndexKind.NODE_PARENT, {_SUB_NODE: _PARENT})
    assert node.node_with_parent_name(_SUB_NODE) == "Bambu Valley - Mining"


def test_node_with_parent_name_needs_a_named_parent() -> None:
    assert node.node_with_parent_name(_SUB_NODE) == ""
    assert node.node_with_parent_name(_PARENT) == ""
    init_index(IndexKind.NODE_PARENT, {_SUB_NODE: 9999})
    assert node.node_with_parent_name(_SUB_NODE) == ""

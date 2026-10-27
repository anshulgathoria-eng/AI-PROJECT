from graph_algorithms import bfs_nearest_source, dfs_reachable
from grid_simulation import ROUTING, analyze_failure


def test_bfs_shortest_path():
    graph = {"a": ["b", "c"], "b": ["a", "d"], "c": ["a", "e"], "d": ["e"], "e": []}
    result = bfs_nearest_source(graph, "a", {"e"})
    assert result["path"] == ["a", "c", "e"]
    assert result["connections"] == 2
    assert len(result["traversal"]) == len(set(result["traversal"]))


def test_disconnected_unavailable_and_blocked():
    graph = {"a": ["b"], "b": ["a"], "z": []}
    assert bfs_nearest_source(graph, "a", {"z"})["path"] == []
    assert bfs_nearest_source(graph, "a", set())["source"] is None
    assert bfs_nearest_source(graph, "a", {"b"}, {"b"})["source"] is None
    assert bfs_nearest_source(graph, "missing", {"b"})["path"] == []
    assert bfs_nearest_source(graph, "b", {"b"})["connections"] == 0
    assert bfs_nearest_source(ROUTING, "H1", {"Battery A"}, {"T1"})["path"] == []


def test_dfs_cycles_disconnected_and_blocked():
    graph = {"a": ["b", "c"], "b": ["a", "c"], "c": ["b"], "z": []}
    assert dfs_reachable(graph, "a") == ["a", "b", "c"]
    assert dfs_reachable(graph, "a", {"c"}) == ["a", "b"]
    assert dfs_reachable(graph, "missing") == []
    assert dfs_reachable(graph, "z") == ["z"]


def test_transformer_failure_is_downstream_only():
    result = analyze_failure("T1")
    assert result["consumers"] == ["H1", "H2"]
    assert "T2" not in result["traversal"]
    assert ("Grid", "T1") in result["unavailable_edges"]

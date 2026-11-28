from __future__ import annotations

from typing import Any, Hashable
import pytest

from src import gps_snapping

class _DummyGraph:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def copy(self):
        return self

    def degree(self):
        return [(node, 2) for node in self.nodes]

    def remove_nodes_from(self, nodes):
        nodes_to_remove = set(nodes)
        self.nodes = [node for node in self.nodes if node not in nodes_to_remove]

    def __contains__(self, node):
        return node in self.nodes

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _DummyGraph):
            return NotImplemented
        return self.nodes == other.nodes and self.edges == other.edges

@pytest.mark.parametrize(
    "raw_node_id",
    [
        1234,
        "node1",
        ("node2", 123, "abc")
    ]
)
def test_snap_gps_to_nearest_node_return_node_id(monkeypatch: pytest.MonkeyPatch, raw_node_id: Hashable) -> None:
    graph = _DummyGraph(nodes = [1234, raw_node_id], edges = [])
    captured: dict[str, Any] = {}
    
    def fake_nearest_nodes(
        G: Any,
        *,
        X: float,
        Y: float,
        return_dist: bool
    ) -> Any:
        captured["G"] = G
        captured["X"] = X
        captured["Y"] = Y
        captured["return_dist"] = return_dist
        return raw_node_id

    monkeypatch.setattr(
        gps_snapping.ox.distance,
        "nearest_nodes",
        fake_nearest_nodes
    )

    node_id = gps_snapping.snap_gps_to_nearest_node(
        graph = graph,
        lat = 12.34,
        lon = 56.78
    )

    assert node_id == raw_node_id
    assert isinstance(node_id, Hashable)
    assert captured == {
        "G": graph,
        "X": 56.78,
        "Y": 12.34,
        "return_dist": False
    }

def test_gps_snap_to_nearest_node_without_and_with_distance(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = _DummyGraph(nodes = ["node1", "node2"], edges = [])

    monkeypatch.setattr(
        gps_snapping.ox.distance,
        "nearest_nodes",
        lambda G, *, X, Y, return_dist: ("node2", 300) if return_dist else "node2"
    )

    node_id, distance_m = gps_snapping.snap_gps_to_nearest_node(
        graph = graph,
        lat = 12.34,
        lon = 56.78,
        return_distance = True
    )

    assert node_id == "node2"
    assert distance_m == 300.0
    assert isinstance(distance_m, float)

    with pytest.raises(ValueError):
        node_id, distance_m = gps_snapping.snap_gps_to_nearest_node(
            graph = graph,
            lat = 12.34,
            lon = 56.78,
            return_distance = False
        )

@pytest.mark.parametrize(
    ("lat", "lon"),
    [
        (-90.0001, 19.0),
        (90.0001, 19.0),
        (50.0, -180.0001),
        (50.0, 180.0001),
    ]
)
def test_snap_gps_to_nearest_node_invalid_coordinates(lat: float, lon: float) -> None:
    graph = _DummyGraph(nodes = ["node1"], edges = [])

    with pytest.raises(ValueError):
        gps_snapping.snap_gps_to_nearest_node(graph = graph, lat = lat, lon = lon)

def test_snap_gps_to_nearest_node_empty_graph() -> None:
    graph = _DummyGraph(nodes = [], edges = [])

    with pytest.raises(ValueError, match = "Graph doesn't contain any nodes."):
        gps_snapping.snap_gps_to_nearest_node(graph = graph, lat = 12.34, lon = 56.78)
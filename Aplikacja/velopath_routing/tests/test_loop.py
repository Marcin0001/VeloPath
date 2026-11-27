import pytest

from src import loop
from src.astar import PathNotFoundError
from typing import Hashable, Any

class _NodesView(dict):
    def __call__(self, data: bool = False):
        if data:
            return self.items()
        return self.keys()

class FakeGraph:
    def __init__(
        self,
        nodes: dict[str, dict[str, float]],
        edges: dict[tuple[str, str], float]
    ):
        self.nodes = _NodesView(nodes)
        self._edges = edges

    def __contains__(
            self,
            node_id: Hashable
    ) -> bool:
        return node_id in self.nodes

@pytest.fixture
def sample_graph() -> FakeGraph:
    nodes = {
        "node1": {"x": 0.0, "y": 0.0},
        "node2": {"x": 0.001, "y": 0.0},
        "node3": {"x": -0.002, "y": 0.002},
        "node4": {"x": 0.003, "y": -0.002},
    }
    edges = {
        ("node1", "node2"): 300.0,
        ("node2", "node3"): 300.0,
        ("node3", "node4"): 300.0,
        ("node4", "node1"): 300.0,
    }
    return FakeGraph(nodes, edges)

def test_generate_loop_waypoints_success(monkeypatch: pytest.MonkeyPatch, sample_graph: FakeGraph) -> None:
    monkeypatch.setattr(
        loop,
        "haversine_distance_m",
        lambda y1, x1, y2, x2: 300.0
    )

    def fake_astar(
        graph: Any,
        source_node_id: Hashable,
        target_node_id: Hashable,
        weight: str = "length"
    ) -> tuple[list[Hashable], float]:
        cost = graph._edges.get((source_node_id, target_node_id))
        if cost is None:
            raise PathNotFoundError(f"Path from {source_node_id} to {target_node_id} not found.")
        return [source_node_id, target_node_id], cost

    monkeypatch.setattr(
        loop,
        "astar",
        fake_astar
    )

    waypoints = loop.generate_loop_waypoints(
        graph = sample_graph,
        start_node_id = "node1",
        target_distance_m = 1200.0,
        n_waypoints = 3,
        min_ratio = 0.1,
        max_ratio = 0.5,
        max_nodes_per_sector = 2
    )

    assert len(waypoints) == 3
    assert len(set(waypoints)) == 3
    assert "node1" not in waypoints

def test_missing_start_node(sample_graph: FakeGraph) -> None:
    with pytest.raises(loop.LoopNotFoundError):
        loop.generate_loop_waypoints(
            graph = sample_graph,
            start_node_id = "node0",
            target_distance_m = 1200.0
        )

def test_invalid_n_waypoints(sample_graph: FakeGraph) -> None:
    with pytest.raises(ValueError):
        loop.generate_loop_waypoints(
            graph = sample_graph,
            start_node_id = "node1",
            target_distance_m = 1200.0,
            n_waypoints = 0
        )

def test_empty_sector(monkeypatch: pytest.MonkeyPatch, sample_graph: FakeGraph) -> None:
    monkeypatch.setattr(
        loop,
        "haversine_distance_m",
        lambda y1, x1, y2, x2: 3000.0
    )

    with pytest.raises(loop.LoopNotFoundError):
        loop.generate_loop_waypoints(
            graph = sample_graph,
            start_node_id = "node1",
            target_distance_m = 1200.0,
            n_waypoints = 3
        )

def test_penalty_choose_path_without_repeats(monkeypatch: pytest.MonkeyPatch) -> None:
    nodes = {
        "node1": {"x": 0.0, "y": 0.0},
        "node2": {"x": 0.003, "y": 0.0},
        "node3": {"x": 0.0031, "y": 0.0},
        "node4": {"x": -0.003, "y": 0.003},
        "node5": {"x": -0.003, "y": -0.003},
        "node6": {"x": 0.0, "y": 0.003},
        "node7": {"x": 0.003, "y": -0.003}
    }
    graph = FakeGraph(nodes, edges={})

    monkeypatch.setattr(
        loop,
        "haversine_distance_m",
        lambda y1, x1, y2, x2: 300.0
    )

    def fake_astar(
            graph: Any,
            source_node_id: Hashable,
            target_node_id: Hashable,
            weight: str = "length"
        ) -> tuple[list[Hashable], float]:
        if (source_node_id, target_node_id) == ("node3", "node4"):
            return ["node3", "node6", "node4"], 300.0
        elif (source_node_id, target_node_id) == ("node4", "node5"):
            return ["node4", "node6", "node5"], 300.0
        return [source_node_id, target_node_id], 300.0

    monkeypatch.setattr(
        loop,
        "astar",
        fake_astar
    )

    waypoints = loop.generate_loop_waypoints(
        graph = graph,
        start_node_id = "node1",
        target_distance_m = 1200.0,
        n_waypoints = 3,
        max_nodes_per_sector = 2
    )

    assert waypoints[0] == "node2"

@pytest.mark.parametrize("wrong_x, wrong_y", [
    (float("nan"), 0.0),
    (0.0, float("nan")),
    (float("inf"), 0.0),
    (0.0, float("inf")),
    (float("-inf"), 0.0),
    (0.0, float("-inf")),
    (300.0, 0.0),
    (-300.0, 0.0),
    (0.0, 300.0),
    (0.0, -300.0),
    (-300.0, -300.0),
    (300.0, 300.0),
    (-300.0, 300.0),
    (300.0, -300.0),
    (180.0001, 0.0),
    (180.0001, 90.0001),
    (180.0001, -90.0001),
    (-180.0001, 0.0),
    (-180.0001, 90.0001),
    (-180.0001, -90.0001),
])
def test_generate_loop_waypoints_with_out_of_range_start_and_candidate_coordinates(monkeypatch: pytest.MonkeyPatch, wrong_x: float, wrong_y: float) -> None:
    nodes =  {
        "node1": {"x": wrong_x, "y": wrong_y},
        "node2": {"x": 0, "y": 0}
    }
    
    graph = FakeGraph(
        nodes = nodes,
        edges = {}
    )

    monkeypatch.setattr(
        loop,
        "haversine_distance_m",
        lambda y1, x1, y2, x2: 300.0
    )

    monkeypatch.setattr(
        loop,
        "astar",
        lambda graph, source_node_id, target_node_id, weight = "length": ([source_node_id, target_node_id], 300.0)
    )

    with pytest.raises(ValueError):
        loop.generate_loop_waypoints(
            graph = graph,
            start_node_id = "node1",
            target_distance_m = 1200.0,
            n_waypoints = 1,
            max_nodes_per_sector = 1
        )

    with pytest.raises(loop.LoopNotFoundError):
        loop.generate_loop_waypoints(
            graph = graph,
            start_node_id = "node2",
            target_distance_m = 1200.0,
            n_waypoints = 1,
            max_nodes_per_sector = 1
        )

def test_generate_loop_waypoints_with_extreme_coordinates(monkeypatch: pytest.MonkeyPatch) -> None:
    nodes = {
        "node1": {"x": 179.9999, "y": 89.9999},
        "node2": {"x": -179.9999, "y": 89.9999},
        "node3": {"x": -179.9999, "y": -89.9999},
        "node4": {"x": 179.9999, "y": -89.9999},
        "node5": {"x": 179.9999, "y": 89.9999}
    }

    graph = FakeGraph(
        nodes = nodes,
        edges = {}
    )

    monkeypatch.setattr(
        loop,
        "haversine_distance_m",
        lambda y1, x1, y2, x2: 300.0
    )

    monkeypatch.setattr(
        loop,
        "astar",
        lambda graph, source_node_id, target_node_id, weight = "length": ([source_node_id, target_node_id], 300.0)
    )

    waypoints = loop.generate_loop_waypoints(
        graph = graph,
        start_node_id = "node1",
        target_distance_m = 1200.0,
        n_waypoints = 3,
        max_nodes_per_sector = 2
    )

    assert len(waypoints) == 3
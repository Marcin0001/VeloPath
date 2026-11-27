import pytest
import osmnx as ox
import networkx as nx
from pathlib import Path

from src import graph_loader, graph_part_cache

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

def test_compute_bbox_symmetry_and_order():
    lat, lon = 30.1234, 20.5432
    west, south, east, north = graph_loader.compute_bbox(lat, lon, target_distance_km = 30.0)

    assert west < lon < east
    assert south < lat < north
    assert pytest.approx(lon - west, rel = 1e-6) == east - lon
    assert pytest.approx(lat - south, rel = 1e-6) == north - lat

def test_compute_bbox_invalid_distance():
    with pytest.raises(ValueError):
        graph_loader.compute_bbox(30.1234, 20.5432, target_distance_km = 0.0)

def test_fetch_bike_graph_calls_with_computed_bbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_graph_part_cache = graph_part_cache.GraphPartCache
    monkeypatch.setattr(
        graph_loader,
        "GraphPartCache",
        lambda *args, **kwargs: real_graph_part_cache(cache_dir = tmp_path),
    )
    
    lat, lon = 30.1234, 20.5432
    distance_km = 20.0
    expected_bbox = graph_loader.compute_bbox(lat, lon, distance_km)
    captured = {}
    expected_graph = _DummyGraph(
        nodes = [1,2],
        edges = [(1, 2, 0)]
    )

    def fake_graph_from_bbox(
        bbox,
        *,
        network_type,
        custom_filter = None,
        simplify
    ):
        captured["bbox"] = bbox
        captured["custom_filter"] = custom_filter
        captured["network_type"] = network_type
        captured["simplify"] = simplify
        return expected_graph

    monkeypatch.setattr(
        graph_loader.ox,
        "graph_from_bbox", 
        fake_graph_from_bbox
    )

    graph = graph_loader.fetch_bike_graph(lat, lon, distance_km, network_type = "bike")

    assert graph == expected_graph
    assert captured["bbox"] == expected_bbox
    assert captured["network_type"] == "bike"
    assert captured["simplify"] == True

def test_fetch_bike_graph_pass_custom_filter_and_useful_tags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_graph_part_cache = graph_part_cache.GraphPartCache
    monkeypatch.setattr(
        graph_loader,
        "GraphPartCache",
        lambda *args, **kwargs: real_graph_part_cache(cache_dir = tmp_path),
    )
    
    captured = {}
    expected_graph = _DummyGraph(
        nodes = [1,2],
        edges = [(1, 2, 0)]
    )

    monkeypatch.setattr(
        ox.settings,
        "useful_tags_way",
        ["highway"]
    )

    monkeypatch.setattr(
        graph_loader,
        "compute_bbox",
        lambda lat, lon, target_distance_km: (12.34, 53.21, 23.12, 54.12)
    )

    def fake_graph_from_bbox(
        bbox,
        *,
        network_type,
        custom_filter,
        simplify
    ):
        captured["bbox"] = bbox
        captured["network_type"] = network_type
        captured["custom_filter"] = custom_filter
        captured["simplify"] = simplify
        captured["useful_tags_way"] = list(ox.settings.useful_tags_way)
        return expected_graph

    monkeypatch.setattr(
        ox,
        "graph_from_bbox",
        fake_graph_from_bbox
    )

    graph = graph_loader.fetch_bike_graph(
        30.1234,
        20.5432,
        target_distance_km = 2.0,
        network_type = "bike"
    )

    assert graph == expected_graph
    assert captured["custom_filter"] == graph_loader.BIKE_CUSTOM_FILTER
    assert captured["network_type"] == "bike"
    assert captured["simplify"] is True
    for tag in graph_loader.BIKE_USEFUL_TAGS:
        assert tag in captured["useful_tags_way"]

def test_fetch_graph_with_retry_errors_then_success(monkeypatch: pytest.MonkeyPatch):
    attempts = {
        "count": 0
    }
    delays = []
    expected_graph = _DummyGraph(
        nodes = [1, 2],
        edges = [(1, 2, )]
    )

    def fake_graph_from_bbox(
        bbox,
        *,
        network_type,
        custom_filter,
        simplify
    ):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("429 Overpass Too Many Requests")
        return expected_graph

    monkeypatch.setattr(
        graph_loader.ox,
        "graph_from_bbox",
        fake_graph_from_bbox
    )

    monkeypatch.setattr(
        graph_loader.time,
        "sleep",
        lambda delay_s: delays.append(delay_s)
    )

    result = graph_loader._fetch_graph_with_retry(
        (12.34, 54.32, 21.92, 31.44),
        network_type = "bike",
        custom_filter = graph_loader.BIKE_CUSTOM_FILTER,
        simplify = True,
        max_retries = 3,
        base_delay_s = 1.0
    )

    assert result is expected_graph
    assert attempts["count"] == 3
    assert delays == [1.0, 2.0]

def test_fetch_graph_with_retry_error_exhaust_raise(monkeypatch: pytest.MonkeyPatch):
    attempts = {
        "count": 0
    }
    delays = []

    def fake_graph_from_bbox(
        bbox,
        *,
        network_type,
        custom_filter,
        simplify
    ):
        attempts["count"] += 1
        raise ConnectionError("Network unreachable")

    monkeypatch.setattr(
        graph_loader.ox,
        "graph_from_bbox",
        fake_graph_from_bbox
    )

    monkeypatch.setattr(
        graph_loader.time,
        "sleep",
        lambda delay: delays.append(delay)
    )

    with pytest.raises(graph_loader.GraphLoadError):
        graph_loader._fetch_graph_with_retry(
            (12.34, 54.32, 21.92, 31.44),
            network_type = "bike",
            custom_filter = graph_loader.BIKE_CUSTOM_FILTER,
            simplify = True,
            max_retries = 3,
            base_delay_s = 2.0
        )

    assert attempts["count"] == 4
    assert delays == [2.0, 4.0, 8.0]

def test_fetch_graph_with_retry_error_empty_graph_with_no_retries(monkeypatch: pytest.MonkeyPatch):
    attempts = {
        "count": 0
    }
    delays = []

    def fake_graph_from_bbox(
        bbox,
        *,
        network_type,
        custom_filter,
        simplify
    ):
        attempts["count"] += 1
        return _DummyGraph(
            nodes = [],
            edges = []
        )

    monkeypatch.setattr(
        graph_loader.ox,
        "graph_from_bbox",
        fake_graph_from_bbox
    )

    monkeypatch.setattr(
        graph_loader.time,
        "sleep",
        lambda delay: delays.append(delay)
    )

    with pytest.raises(graph_loader.GraphLoadError):
        graph_loader._fetch_graph_with_retry(
            (12.34, 54.32, 21.92, 31.44),
            network_type = "bike",
            custom_filter = graph_loader.BIKE_CUSTOM_FILTER,
            simplify = True,
            max_retries = 2,
            base_delay_s = 3.0
        )

    assert attempts["count"] == 1
    assert delays == []

def test_fetch_bike_graph_graph_load_error(monkeypatch: pytest.MonkeyPatch):
    def fake_graph_from_bbox(
            bbox,
            *,
            network_type,
            custom_filter,
            simplify
        ):
        raise ValueError("Invalid Overpass response")
    
    monkeypatch.setattr(
        graph_loader.ox,
        "graph_from_bbox",
        fake_graph_from_bbox
    )

    with pytest.raises(graph_loader.GraphLoadError):
        graph_loader.fetch_bike_graph(
            12.34,
            56.78,
            target_distance_km = 5.0,
            max_retries = 1
        )

def test_clean_osm_graph_remove_isolated_and_dead_ends_and_unreachable() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("node0")
    graph.add_node("node1")
    graph.add_node("node2")
    graph.add_node("node3")
    graph.add_node("node4")
    graph.add_node("node5")
    graph.add_node("node6")
    graph.add_node("node7")
    graph.add_node("node8")
    graph.add_node("node9")
    graph.add_node("node10")
    graph.add_edge("node1","node2")
    graph.add_edge("node2","node3")
    graph.add_edge("node3","node4")
    graph.add_edge("node2","node4")
    graph.add_edge("node2","node5")
    graph.add_edge("node5","node6")
    graph.add_edge("node6","node7")
    graph.add_edge("node8","node9")
    graph.add_edge("node9","node10")
    graph.add_edge("node8","node10")

    cleaned_graph = graph_loader.clean_osm_graph(
        graph = graph,
        start_node = "node1"
    )

    assert "node0" not in cleaned_graph
    assert "node1" in cleaned_graph
    assert "node2" in cleaned_graph
    assert "node3" in cleaned_graph
    assert "node4" in cleaned_graph
    assert "node5" not in cleaned_graph
    assert "node6" not in cleaned_graph
    assert "node7" not in cleaned_graph
    assert "node8" not in cleaned_graph
    assert "node9" not in cleaned_graph
    assert "node10" not in cleaned_graph

def test_clean_osm_graph_keeps_protected_nodes() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("node0")
    graph.add_node("node1")
    graph.add_node("node2")
    graph.add_node("node3")
    graph.add_node("node4")
    graph.add_node("node5")
    graph.add_node("node6")
    graph.add_node("node7")
    graph.add_node("node8")
    graph.add_node("node9")
    graph.add_node("node10")
    graph.add_edge("node1","node2")
    graph.add_edge("node2","node3")
    graph.add_edge("node3","node4")
    graph.add_edge("node2","node4")
    graph.add_edge("node2","node5")
    graph.add_edge("node5","node6")
    graph.add_edge("node6","node7")
    graph.add_edge("node8","node9")
    graph.add_edge("node9","node10")
    graph.add_edge("node8","node10")

    cleaned_graph = graph_loader.clean_osm_graph(
        graph = graph,
        protected_nodes = {"node0","node9","node6"},
        start_node = "node1"
    )

    assert "node0" in cleaned_graph
    assert "node1" in cleaned_graph
    assert "node2" in cleaned_graph
    assert "node3" in cleaned_graph
    assert "node4" in cleaned_graph
    assert "node5" in cleaned_graph
    assert "node6" in cleaned_graph
    assert "node7" not in cleaned_graph
    assert "node8" not in cleaned_graph
    assert "node9" in cleaned_graph
    assert "node10" not in cleaned_graph

def test_fetch_bike_graph_default_clean(monkeypatch) -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("node1")
    graph.add_node("node2")
    graph.add_node("node3")
    graph.add_node("node4")
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", "node3")
    graph.add_edge("node1", "node3")
    graph.add_edge("node3", "node4")

    monkeypatch.setattr(
        graph_loader,
        "configure_bike_tags",
        lambda tags: []
    )

    monkeypatch.setattr(
        graph_loader,
        "_fetch_graph_with_retry",
        lambda bbox, *, network_type, custom_filter, simplify, max_retries, base_delay_s: graph
    )

    result = graph_loader.fetch_bike_graph(12.34, 56.78, 10.0, start_node = "node1")

    assert "node4" not in result
    assert set(result) == {"node1","node2","node3"}

def test_fetch_bike_graph_skip_clean(monkeypatch) -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("node1")
    graph.add_node("node2")
    graph.add_node("node3")
    graph.add_node("node4")
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", "node3")
    graph.add_edge("node1", "node3")
    graph.add_edge("node3", "node4")

    monkeypatch.setattr(
        graph_loader,
        "configure_bike_tags",
        lambda tags: []
    )

    monkeypatch.setattr(
        graph_loader,
        "_fetch_graph_with_retry",
        lambda bbox, *, network_type, custom_filter, simplify, max_retries, base_delay_s: graph
    )

    result = graph_loader.fetch_bike_graph(12.34, 56.78, 10.0, start_node = "node1", clean_graph = False)

    assert "node4" in result
    assert set(result) == {"node1","node2","node3","node4"}
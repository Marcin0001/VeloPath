import pytest
import math
import networkx as nx

from src import astar

def test_haversine_distance_value():
    distance_m = astar.haversine_distance_m(0.0, 0.0, 0.0, 1.0)
    assert math.isclose(distance_m, 111194.93, rel_tol = 1e-3)

def test_haversine_distance_same_point():
    distance_m = astar.haversine_distance_m(12.34, 56.78, 12.34, 56.78)
    assert distance_m == 0.0

def test_haversine_distance_symmetry():
    distance_m_1 = astar.haversine_distance_m(12.34, 56.78, 33.33, 33.33)
    distance_m_2 = astar.haversine_distance_m(33.33, 33.33, 12.34, 56.78)
    assert math.isclose(distance_m_1, distance_m_2, rel_tol = 1e-12)

def test_heuristic_use_node_coordinates():
    graph = nx.DiGraph()
    graph.add_node("A", x = 0.0, y = 0.0)
    graph.add_node("B", x = 1.0, y = 0.0)
    heuristic_result = astar._heuristic(graph, "A", "B")
    assert math.isclose(heuristic_result, 111194.93, rel_tol = 1e-3)

def test_astar_same_source_and_target():
    graph = nx.MultiDiGraph()
    graph.add_node("A", x = 56.78, y = 12.34)
    path, cost = astar.astar(graph, "A", "A")
    assert path == ["A"]
    assert cost == 0.0

def test_astar_shortest_path_and_parallel_edges():
    graph = nx.MultiDiGraph()
    graph.add_node("A", x = 10.0, y = 10.0)
    graph.add_node("B", x = 10.1, y = 10.1)
    graph.add_node("C", x = 10.2, y = 10.2)

    graph.add_edge("A", "B", length = 20000.0)
    graph.add_edge("A", "B", length = 10000.0)
    graph.add_edge("B", "C", length = 30000.0)
    graph.add_edge("A", "C", length = 50000.0)

    path, cost = astar.astar(graph, "A", "C")
    assert path == ["A", "B", "C"]
    assert cost == 40000.0

def test_astar_missing_weight_using_default():
    graph = nx.DiGraph()
    graph.add_node("A", x = 10.0, y = 10.0)
    graph.add_node("B", x = 10.1, y = 10.1)

    graph.add_edge("A", "B")

    path, cost = astar.astar(graph, "A", "B")
    assert path == ["A", "B"]
    assert cost == 1.0

def test_astar_ignore_negative_weight():
    graph = nx.DiGraph()
    graph.add_node("A", x = 10.0, y = 10.0)
    graph.add_node("B", x = 10.1, y = 10.1)

    graph.add_edge("A", "B", length = -10.0)

    with pytest.raises(astar.PathNotFoundError):
        astar.astar(graph, "A", "B")

def test_astar_no_path_or_missing_node():
    graph = nx.MultiDiGraph()
    graph.add_node("A", x = 10.0, y = 10.0)
    graph.add_node("B", x = 10.1, y = 10.1)

    with pytest.raises(astar.PathNotFoundError):
        astar.astar(graph, "A", "B")

    with pytest.raises(astar.PathNotFoundError):
        astar.astar(graph, "A", "C")

@pytest.mark.parametrize(
    ("edge_data", "base_weight", "expected"),
    [
        ({"surface": " asPhaLt  "}, 100.0, 100.0),
        ({"surface": ["  pAvEd", "^$@#&%85782"]}, 100.0, 100.0),
        ({"surface": [" ConCRete  "]}, 100.0, 105.0),
        ({"surface": "gravel"}, 100.0, 140.0),
        ({"surface": "unpaved"}, 100.0, 150.0),
        ({"surface": "dirt"}, 100.0, 160.0),
        ({"surface": "wrong"}, 100.0, 120.0),
        ({"surface": None}, 100.0, 110.0),
    ]
)
def test_astar_single_edge_cost_osm_tags(edge_data, base_weight, expected) -> None:
    attributes = {"length": base_weight, "surface": edge_data["surface"]}
    assert astar._single_edge_cost(
        attributes = attributes,
        weight = "osm_tags"
    ) == pytest.approx(expected)

def test_min_edge_weight_multiedge_osm_tags() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("Node1", x = 30.0, y = 30.0)
    graph.add_node("Node2", x = 30.001, y = 30.0)
    graph.add_edge("Node1", "Node2", key = 0, length = 300.0, surface="dirt")
    graph.add_edge("Node1", "Node2", key = 1, length = 300.0, surface="concrete")

    assert astar._min_edge_weight(graph, "Node1", "Node2", weight = "osm_tags") == pytest.approx(315.0)

def test_astar_surface_cost_preference() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node("Node1", x = 30.0, y = 30.0)
    graph.add_node("Node2", x = 30.001, y = 30.0)
    graph.add_node("Node3", x = 30.001, y = 30.001)

    graph.add_edge("Node1", "Node2", length = 100.0, surface = "dirt")
    graph.add_edge("Node2", "Node3", length = 100.0, surface = "dirt")
    graph.add_edge("Node1", "Node3", length = 300.0, surface = "concrete")

    path, cost = astar.astar(graph, "Node1", "Node3", weight = "osm_tags")

    assert path == ["Node1", "Node3"]
    assert cost == pytest.approx(315.00)
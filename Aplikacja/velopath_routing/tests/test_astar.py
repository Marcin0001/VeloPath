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
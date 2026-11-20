import pytest
import osmnx as ox

from src import graph_loader

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

def test_fetch_bike_graph_calls_with_computed_bbox(monkeypatch):
    lat, lon = 30.1234, 20.5432
    distance_km = 20.0
    expected_bbox = graph_loader.compute_bbox(lat, lon, distance_km)
    captured = {}

    def fake_graph_from_bbox(*, bbox, network_type, custom_filter = None, simplify):
        captured["bbox"] = bbox
        captured["network_type"] = network_type
        captured["simplify"] = simplify
        return "FAKE_GRAPH"

    monkeypatch.setattr(
        graph_loader.ox,
        "graph_from_bbox", 
        fake_graph_from_bbox)

    graph = graph_loader.fetch_bike_graph(lat, lon, distance_km, network_type = "bike")

    assert graph == "FAKE_GRAPH"
    assert captured["bbox"] == expected_bbox
    assert captured["network_type"] == "bike"
    assert captured["simplify"] == True

def test_fetch_bike_graph_pass_custom_filter_and_useful_tags(monkeypatch):
    captured = {}

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

    def fake_graph_from_bbox(*, bbox, network_type, custom_filter, simplify):
        captured["bbox"] = bbox
        captured["network_type"] = network_type
        captured["custom_filter"] = custom_filter
        captured["simplify"] = simplify
        captured["useful_tags_way"] = list(ox.settings.useful_tags_way)
        return "FAKE_GRAPH"

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

    assert graph == "FAKE_GRAPH"
    assert captured["custom_filter"] == graph_loader.BIKE_CUSTOM_FILTER
    assert captured["network_type"] == "bike"
    assert captured["simplify"] is True
    for tag in graph_loader.BIKE_USEFUL_TAGS:
        assert tag in captured["useful_tags_way"]
import pytest

from src import osm_tags

@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("    ConCrEte         ", "concrete"),
        ("GRAVEL", "gravel"),
        (["  Dirt ", "asphalt"], "dirt"),
        ([], None),
        ([""], None),
        ("", None),
        ("     ", None),
        (["           "], None),
        ([["         "], None]),
        (None, None),
    ],
)
def test_normalize_tag(raw_value, expected) -> None:
    assert osm_tags._normalize_tag(raw_value) == expected

def test_normalize_edge_tags_ignores_extra_keys() -> None:
    edge_data = {
        "osmid": 1234,
        "length": 300.0,
        "name": "Oxford street",
        "highway": ["    CyClEwAy   ", " additional one for test_!@#"],
        "surface": "   cOnCrEte  ",
        "smoothness": None
    }

    assert osm_tags.normalize_edge_tags(edge_data) == {
        "highway": "cycleway",
        "surface": "concrete",
        "smoothness": None
    }

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
def test_compute_edge_weight_default_multipliers(edge_data, base_weight, expected) -> None:
    assert osm_tags.compute_edge_weight(edge_data, base_weight = base_weight) == pytest.approx(expected)

def test_compute_edge_weight_custom_multipliers() -> None:
    edge_data = {"surface": "gravel"}
    custom_surface_multipliers = {"gravel": 2.0}

    assert osm_tags.compute_edge_weight(
        data = edge_data,
        base_weight = 100.0,
        surface_multipliers = custom_surface_multipliers
    ) == pytest.approx(200.0)
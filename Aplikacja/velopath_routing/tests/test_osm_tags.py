import pytest
import math

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

def test_city_and_mountain_bike_edge_weight_wrong_length_return_inf():
    assert math.isinf(osm_tags.city_bike_edge_weight({"length": 0.0}))
    assert math.isinf(osm_tags.city_bike_edge_weight({"length": -5.0}))
    assert math.isinf(osm_tags.mountain_bike_edge_weight({"length": 0.0}))
    assert math.isinf(osm_tags.mountain_bike_edge_weight({"length": -5.0}))

def test_city_and_mountain_bike_highway_preference():
    better_way = {
        "length": 300.0,
        "highway": "cycleway",
        "surface": "asphalt"
    }

    worse_way = {
        "length": 300.0,
        "highway": "primary",
        "surface": "asphalt"
    }

    assert osm_tags.city_bike_edge_weight(worse_way) > osm_tags.city_bike_edge_weight(better_way)
    assert osm_tags.mountain_bike_edge_weight(worse_way) > osm_tags.mountain_bike_edge_weight(better_way)

def test_city_and_mountain_bike_surface_preference():
    dirt_way = {
        "length": 300.0,
        "highway": "cycleway",
        "surface": "dirt"
    }

    asphalt_way = {
        "length": 300.0,
        "highway": "cycleway",
        "surface": "asphalt"
    }

    assert osm_tags.city_bike_edge_weight(dirt_way) > osm_tags.city_bike_edge_weight(asphalt_way)
    assert osm_tags.mountain_bike_edge_weight(dirt_way) < osm_tags.mountain_bike_edge_weight(asphalt_way)

@pytest.mark.parametrize("grade", [-10, -0.3, 0.0])
def test_city_and_mountain_bike_non_positive_grade_influence(grade):
    base_way = {
        "length": 300.0,
        "highway": "cycleway",
        "surface": "asphalt",
        "grade": 0.0
    }

    non_positive_grade_way = {
        "length": 300.0,
        "highway": "cycleway",
        "surface": "asphalt",
        "grade": grade
    }

    assert osm_tags.city_bike_edge_weight(base_way) == pytest.approx(osm_tags.city_bike_edge_weight(non_positive_grade_way))
    assert osm_tags.mountain_bike_edge_weight(base_way) == pytest.approx(osm_tags.mountain_bike_edge_weight(non_positive_grade_way))

def test_city_and_mountain_bike_positive_grade_influence_and_cap():
    flat_way = {
        "length": 300.0,
        "highway": "cycleway",
        "surface": "asphalt",
        "grade": 0.0
    }

    small_grade_way = {
        "length": 300.0,
        "highway": "cycleway",
        "surface": "asphalt",
        "grade": 0.2
    }

    extreme_grade_way = {
        "length": 300.0,
        "highway": "cycleway",
        "surface": "asphalt",
        "grade": 50.0
    }

    assert osm_tags.city_bike_edge_weight(small_grade_way) > osm_tags.city_bike_edge_weight(flat_way)
    assert osm_tags.city_bike_edge_weight(small_grade_way) < osm_tags.city_bike_edge_weight(extreme_grade_way)
    assert osm_tags.mountain_bike_edge_weight(small_grade_way) > osm_tags.mountain_bike_edge_weight(flat_way)
    assert osm_tags.mountain_bike_edge_weight(small_grade_way) < osm_tags.mountain_bike_edge_weight(extreme_grade_way)
    assert osm_tags.mountain_bike_edge_weight(small_grade_way) > osm_tags.city_bike_edge_weight(small_grade_way)
    assert osm_tags.city_bike_edge_weight(extreme_grade_way) == pytest.approx(
        osm_tags.city_bike_edge_weight(
            {
                "length": 300.0,
                "highway": "cycleway",
                "surface": "asphalt",
                "grade": 1.0
            }
        )
    )
    assert osm_tags.mountain_bike_edge_weight(extreme_grade_way) == pytest.approx(
        osm_tags.mountain_bike_edge_weight(
            {
                "length": 300.0,
                "highway": "cycleway",
                "surface": "asphalt",
                "grade": 1.0
            }
        )
    )
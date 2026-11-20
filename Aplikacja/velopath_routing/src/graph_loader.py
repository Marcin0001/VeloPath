import math
import osmnx as ox

BIKE_CUSTOM_FILTER = (
    '["highway"~"cycleway|path|footway|residential|living_street|tertiary|secondary|unclassified|track"]'
    '["bicycle"!~"no"]'
    '["access"!~"private"]'
)

BIKE_USEFUL_TAGS = [
    "highway",
    "bicycle",
    "cycleway",
    "cycleway:left",
    "cycleway:right",
    "cycleway:both",
    "oneway",
    "oneway:bicycle",
    "surface"
]

def configure_bike_tags() -> None:
    for tag in BIKE_USEFUL_TAGS:
        if tag not in ox.settings.useful_tags_way:
            ox.settings.useful_tags_way.append(tag)

def compute_bbox(lat: float, lon: float, target_distance_km: float) -> tuple[float, float, float, float]:
    if target_distance_km <= 0:
        raise ValueError("Target distance has to be higher than 0")

    max_range_km = max(1.0, target_distance_km * 0.45)

    lat_delta = max_range_km / 111.32
    cos_lat = max(math.cos(math.radians(lat)), 0.01)
    lon_delta = max_range_km / (111.32 * cos_lat)

    north = lat + lat_delta
    south = lat - lat_delta
    east = lon + lon_delta
    west = lon - lon_delta

    return (west, south, east, north)

def fetch_bike_graph(
        lat: float,
        lon: float,
        target_distance_km: float,
        network_type: str = "bike",
        custom_filter: str | None = BIKE_CUSTOM_FILTER
    ):
    configure_bike_tags()
    bbox = compute_bbox(lat, lon, target_distance_km)

    return ox.graph_from_bbox(
        bbox = bbox,
        network_type = network_type,
        custom_filter = custom_filter,
        simplify = True
    )
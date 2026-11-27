from typing import Any

CITY_BIKE_SURFACE_MULTIPLIERS = {
    "asphalt": 1.0,
    "paved": 1.0,
    "concrete": 1.1,
    "paving_stones": 1.3,
    "cobblestone": 1.7,
    "gravel": 1.8,
    "unpaved": 2.0,
    "dirt": 2.2
}

MOUNTAIN_BIKE_SURFACE_MULTIPLIERS = {
    "dirt": 0.8,
    "gravel": 0.9,
    "unpaved": 0.9,
    "ground": 0.9,
    "asphalt": 1.15,
    "paved": 1.1,
    "concrete": 1.15,
    "cobblestone": 1.05  
}

def _normalize_tag(value: Any) -> str | None:
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    normalized_tag = str(value).strip().lower()

    return normalized_tag or None

def normalize_edge_tags(data: dict[str, Any]) -> dict[str, str | None]:
    return {
        "highway": _normalize_tag(data.get("highway")),
        "surface": _normalize_tag(data.get("surface")),
        "smoothness": _normalize_tag(data.get("smoothness"))
    }

def city_bike_edge_weight(
    data: dict[str, Any]
) -> float:
    base_weight = float(data.get("length", 0.0) or 0.0)
    if base_weight <= 0:
        return float("inf")

    bike_weight = compute_edge_weight(
        data = data,
        base_weight = base_weight,
        surface_multipliers = CITY_BIKE_SURFACE_MULTIPLIERS
    )

    tags = normalize_edge_tags(data)
    highway = tags.get("highway")
    multiplier = 1.0

    if highway in {"cycleway", "living_street", "residential"}:
        multiplier *= 0.85
    elif highway in {"primary", "secondary", "trunk", "primary_link", "secondary_link"}:
        multiplier *= 1.4

    edge_grade = float(data.get("grade", 0.0) or 0.0)
    if edge_grade > 0:
        multiplier += min(edge_grade * 4.0, 1.5)

    return bike_weight * multiplier

def mountain_bike_edge_weight(
    data: dict[str, Any]
) -> float:
    base_weight = float(data.get("length", 0.0) or 0.0)
    if base_weight <= 0:
        return float("inf")

    bike_weight = compute_edge_weight(
        data = data,
        base_weight = base_weight,
        surface_multipliers = MOUNTAIN_BIKE_SURFACE_MULTIPLIERS
    )

    tags = normalize_edge_tags(data)
    highway = tags.get("highway")
    multiplier = 1.0

    if highway in {"path", "track", "bridleway", "footway", "cycleway"}:
        multiplier *= 0.85
    elif highway in {"primary", "secondary", "trunk", "primary_link", "secondary_link"}:
        multiplier *= 1.4

    edge_grade = float(data.get("grade", 0.0) or 0.0)
    if edge_grade > 0:
        multiplier += min(edge_grade * 6.0, 1.5)

    return bike_weight * multiplier

def compute_edge_weight(
    data: dict[str, Any],
    base_weight: float = 1.0,
    surface_multipliers: dict[str, float] | None = None
) -> float:
    multipliers = surface_multipliers or {
        "asphalt": 1.0,
        "paved": 1.0,
        "concrete": 1.05,
        "gravel": 1.4,
        "unpaved": 1.5,
        "dirt": 1.6
    }

    tags = normalize_edge_tags(data)
    surface = tags["surface"]
    factor = multipliers.get(surface, 1.2) if surface else 1.1

    return float(base_weight) * factor
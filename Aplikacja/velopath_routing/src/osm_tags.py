from typing import Any

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
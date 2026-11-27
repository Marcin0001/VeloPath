import math
import osmnx as ox
import time
from typing import Hashable
import networkx as nx

from src.graph_part_cache import GraphPartCache

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

class GraphLoadError(RuntimeError):
    """Data loading or OSMnx graph building error"""

def clean_osm_graph(
    graph: nx.MultiDiGraph,
    protected_nodes: set[Hashable] | None = None,
    start_node: Hashable | None = None
) -> nx.MultiDiGraph:
    cleaned_graph = graph.copy()
    prot_nodes = protected_nodes or set()
    if start_node is not None:
        prot_nodes.add(start_node)

    isolated = [
        node for node, deg in cleaned_graph.degree()
        if deg == 0 and node not in prot_nodes
    ]
    cleaned_graph.remove_nodes_from(isolated)

    while True:
        dead_ends = [
            node for node, deg in cleaned_graph.degree()
            if deg <= 1 and node not in prot_nodes
        ]
        if not dead_ends:
            break
        cleaned_graph.remove_nodes_from(dead_ends)

    cleaned_graph.remove_nodes_from(
        node for node, deg in cleaned_graph.degree()
        if deg == 0 and node not in prot_nodes
    )

    if start_node is not None and start_node in cleaned_graph:
        reachable = nx.descendants(cleaned_graph, start_node) | {start_node}
        unreachable = [
            node for node in cleaned_graph.nodes
            if node not in reachable
            and node not in prot_nodes
        ]
        cleaned_graph.remove_nodes_from(unreachable)

    return cleaned_graph

def configure_bike_tags(
        useful_tags: list[str] | None = None
) -> list[str]:
    tags_to_add = useful_tags if useful_tags is not None else BIKE_USEFUL_TAGS
    current_tags = list(ox.settings.useful_tags_way)

    for tag in tags_to_add:
        if tag not in current_tags:
            current_tags.append(tag)

    ox.settings.useful_tags_way = current_tags

    return current_tags

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

def _is_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True

    message = str(exc).lower()
    retry_markers = (
        "429",
        "502",
        "503",
        "504",
        "too many requests",
        "timed out",
        "timeout",
        "temporarily unavailable",
        "overpass"
    )

    return any(marker in message for marker in retry_markers)

def _fetch_graph_with_retry(
    bbox: tuple[float, float, float, float],
    *,
    network_type: str,
    custom_filter: str | None,
    simplify: bool = True,
    max_retries: int = 3,
    base_delay_s: float = 1.0
):
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            graph = ox.graph_from_bbox (
                bbox,
                network_type = network_type,
                custom_filter = custom_filter,
                simplify = simplify
            )

            if graph is None or len(graph.nodes) == 0 or len(graph.edges) == 0:
                raise GraphLoadError("Loaded graph is empty (no nodes or edges)")
            return graph
        except GraphLoadError:
            raise
        except Exception as exc:
            last_exc = exc
            if not _is_retryable_error(exc) or attempt == max_retries:
                raise GraphLoadError(
                    f"Graph loading failed after {attempt + 1} tries: {exc}"
                ) from exc
            time.sleep(base_delay_s * (2 ** attempt))

    raise GraphLoadError("Graph loading process failed.") from last_exc

def fetch_bike_graph(
        lat: float,
        lon: float,
        target_distance_km: float,
        network_type: str = "bike",
        custom_filter: str | None = BIKE_CUSTOM_FILTER,
        simplify: bool = True,
        useful_tags: list[str] | None = None,
        max_retries: int = 3,
        base_delay_s: float = 1.0,
        clean_graph: bool = True,
        protected_nodes: set[Hashable] | None = None,
        start_node: Hashable | None = None
    ):
    configure_bike_tags(useful_tags)
    bbox = compute_bbox(lat, lon, target_distance_km)
    actual_custom_filter = custom_filter if custom_filter is not None else BIKE_CUSTOM_FILTER

    query_params = {
        "bbox": bbox,
        "network_type": network_type,
        "custom_filter": actual_custom_filter,
        "simplify": simplify,
    }

    cache = GraphPartCache()

    graph = cache.get_or_fetch(
        query_params = query_params,
        fetcher = lambda: _fetch_graph_with_retry(
            bbox = bbox,
            network_type = network_type,
            custom_filter = actual_custom_filter,
            simplify = simplify,
            max_retries = max_retries,
            base_delay_s = base_delay_s
        )
    )

    if clean_graph:
        return clean_osm_graph(
            graph = graph,
            protected_nodes = protected_nodes,
            start_node = start_node
        )
    return graph
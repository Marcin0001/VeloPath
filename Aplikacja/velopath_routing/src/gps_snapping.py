from __future__ import annotations

from typing import Any, Hashable
import osmnx as ox

def snap_gps_to_nearest_node(
    graph: Any,
    lat: float,
    lon: float,
    *,
    return_distance: bool = False
) -> Hashable | tuple[Hashable, float]:
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Given latitude ({lat}) is invalid.")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Given longitude ({lon}) is invalid.")
    if len(graph.nodes) == 0:
        raise ValueError("Graph doesn't contain any nodes.")

    nearest_node = ox.distance.nearest_nodes(
        G = graph,
        X = lon,
        Y = lat,
        return_dist = return_distance
    )
    if return_distance:
        node_id, distance_m = nearest_node
        return node_id, float(distance_m)
    return nearest_node
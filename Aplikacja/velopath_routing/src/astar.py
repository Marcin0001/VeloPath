import heapq
import math
from typing import Any, Hashable
from src.osm_tags import compute_edge_weight

class PathNotFoundError(ValueError):
    """No path between given nodes"""

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_m = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    phi_delta = math.radians(lat2 - lat1)
    lambda_delta = math.radians(lon2 - lon1)

    a = math.sin(phi_delta / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(lambda_delta / 2.0) ** 2)

    return 2.0 * earth_radius_m * math.asin(math.sqrt(max(min(a, 1.0), 0.0)))

def _heuristic(graph: Any, u_node_id: Hashable, target_node_id: Hashable) -> float:
    u_node = graph.nodes[u_node_id]
    target_node = graph.nodes[target_node_id]
    return haversine_distance_m(u_node["y"], u_node["x"], target_node["y"], target_node["x"])

def _single_edge_cost(attributes: dict[str, Any], weight: str) -> float:
    if weight in {"osm_tags", "surface_weight"}:
        base_length = float(attributes.get("length", 1.0))
        return float(compute_edge_weight(data = attributes, base_weight = base_length))
    return float(attributes.get(weight, 1.0))

def _min_edge_weight(graph: Any, u_node_id: Hashable, v_node_id: Hashable, weight: str = "length") -> float | None:
    edge_data = graph.get_edge_data(u_node_id, v_node_id)
    if edge_data is None:
        return None
    if not edge_data:
        return 1.0

    first_val = next(iter(edge_data.values()))
    if isinstance(first_val, dict):
        weights = [
            _single_edge_cost(attributes = attributes, weight = weight) for attributes in edge_data.values()
        ]
    else:
        weights = [
            _single_edge_cost(attributes = edge_data, weight = weight)
        ]

    return min(weights) if weights else None

def astar(graph: Any, source_node_id: Hashable, target_node_id: Hashable, weight: str = "length") -> tuple[list[Hashable], float]:
    if source_node_id not in graph or target_node_id not in graph:
        raise PathNotFoundError("Source or target node doesn't exist in the graph.")

    if source_node_id == target_node_id:
        return [source_node_id], 0.0

    counter = 0
    open_heap: list[tuple[float, int, Hashable]] = [(0.0, counter, source_node_id)]
    previous_node_id: dict[Hashable, Hashable] = {}
    node_score: dict[Hashable, float] = {source_node_id: 0.0}
    closed_node_ids: set[Hashable] = set()

    while open_heap:
        _, _, current_node_id = heapq.heappop(open_heap)

        if current_node_id in closed_node_ids:
            continue

        if current_node_id == target_node_id:
            path = [current_node_id]
            while current_node_id in previous_node_id:
                current_node_id = previous_node_id[current_node_id]
                path.append(current_node_id)
            path.reverse()
            return path, node_score[target_node_id]

        closed_node_ids.add(current_node_id)

        for neighbor_node_id in graph.successors(current_node_id):
            if neighbor_node_id in closed_node_ids:
                continue

            step_cost = _min_edge_weight(graph, current_node_id, neighbor_node_id, weight = weight)
            if step_cost is None or step_cost < 0:
                continue

            new_score = node_score[current_node_id] + step_cost
            if new_score < node_score.get(neighbor_node_id, float("inf")):
                previous_node_id[neighbor_node_id] = current_node_id
                node_score[neighbor_node_id] = new_score
                counter += 1
                heapq.heappush(open_heap, (new_score + _heuristic(graph, neighbor_node_id, target_node_id), counter, neighbor_node_id))

    raise PathNotFoundError(f"Path from {source_node_id} to {target_node_id} not found.")
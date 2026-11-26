import math
from typing import Hashable, Any
from src.astar import PathNotFoundError, astar, haversine_distance_m

class LoopNotFoundError(PathNotFoundError):
    """Loop generation error"""

def _direction_angle_deg(
    start_x: float,
    start_y: float,
    target_x: float,
    target_y: float
) -> float:
    delta_x = target_x - start_x
    delta_y = target_y - start_y
    return (math.degrees(math.atan2(delta_y, delta_x)) + 360.0) % 360.0

def _chain_cost(
    graph: Any,
    nodes: list[Hashable],
    weight: str = "length"
) -> tuple[float, list[Hashable]]:
    total_cost = 0.0
    full_path: list[Hashable] = []

    for i in range(len(nodes) - 1):
        part_path, part_cost = astar(graph, nodes[i], nodes[i + 1], weight = weight)
        total_cost += part_cost
        if i == 0:
            full_path.extend(part_path)
        else:
            full_path.extend(part_path[1:])

    return total_cost, full_path

def generate_loop_waypoints(
    graph: Any,
    start_node_id: Hashable,
    target_distance_m: float,
    n_waypoints: int = 3,
    weight: str = "length",
    min_ratio: float = 0.1,
    max_ratio: float = 0.5,
    max_nodes_per_sector: int = 5
) -> list[Hashable]:
    if start_node_id not in graph:
        raise LoopNotFoundError("Start node doesn't exist in given graph.")
    if n_waypoints not in (1, 2, 3, 4, 5):
        raise ValueError("Number of waypoints must be an integer in range 1-5")

    start_node = graph.nodes[start_node_id]
    start_x = float(start_node["x"])
    start_y = float(start_node["y"])

    min_r_m = target_distance_m * min_ratio
    max_r_m = target_distance_m * max_ratio
    expected_part_len_m = target_distance_m / (n_waypoints + 1)

    sectors: list[list[tuple[float, Hashable]]] = [[] for _ in range(n_waypoints)]
    sectors_angle_width = 360.0 / n_waypoints

    for node_id, node in graph.nodes(data = True):
        if node_id == start_node_id or "x" not in node or "y" not in node:
            continue

        x = float(node["x"])
        y = float(node["y"])

        approx_dist_m = haversine_distance_m(start_y, start_x, y, x)
        if not (min_r_m <= approx_dist_m and approx_dist_m <= max_r_m):
            continue

        angle_deg = _direction_angle_deg(start_x, start_y, x, y)
        sector_idx = min(int(angle_deg // sectors_angle_width), n_waypoints - 1)
        score_m = abs(approx_dist_m - expected_part_len_m)

        sectors[sector_idx].append((score_m, node_id))

    cut_sectors: list[list[Hashable]] = []
    for sector in sectors:
        sector.sort(key = lambda item: item[0])
        chosen_node_ids = [node_id for _, node_id in sector[:max_nodes_per_sector]]
        if not chosen_node_ids:
            raise LoopNotFoundError("There is not enough candidates across directions to build a loop.")
        cut_sectors.append(chosen_node_ids)

    best_waypoints: list[Hashable] = []
    best_score_m: float = float("inf")

    combos: list[list[Hashable]] = [[]]
    for sector in cut_sectors:
        combos = [prev + [candidate] for prev in combos for candidate in sector]

    for waypoints in combos:
        if(len(set(waypoints)) != len(waypoints)):
            continue

        try:
            total_cost_m, full_path = _chain_cost(
                graph,
                [start_node_id, *waypoints, start_node_id],
                weight = weight
            )
        except PathNotFoundError:
            continue

        repeated_nodes = len(full_path) - len(set(full_path)) - 1
        penalty_m = max(0, repeated_nodes) * (0.1 * target_distance_m)
        diff_m = abs(total_cost_m - target_distance_m) + penalty_m

        if diff_m < best_score_m:
            best_score_m = diff_m
            best_waypoints = waypoints

    if not best_waypoints:
        raise LoopNotFoundError(f"Loop from {start_node_id} containing {n_waypoints} waypoints not found.")

    return best_waypoints
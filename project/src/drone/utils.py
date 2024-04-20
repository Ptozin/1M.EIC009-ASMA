# ----------------------------------------------------------------------------------------------

from itertools import combinations

from order import DeliveryOrder
from misc.distance import haversine_distance

# ---------------------------------------------------------------------------------------------

def arrived_to_target(position, target_lat : float, target_lon : float) -> bool:
    return position['latitude'] == target_lat and position['longitude'] == target_lon

# ---------------------------------------------------------------------------------------------

def closest_order(latitude, longitude, orders : list[DeliveryOrder]) -> DeliveryOrder:
    min_dist = float('inf')
    closest = None
    for order in orders:
        dist = haversine_distance(
            latitude,
            longitude,
            order.destination_position['latitude'],
            order.destination_position['longitude']
        )
        if dist < min_dist:
            min_dist = dist
            closest = order
    return closest

# ---------------------------------------------------------------------------------------------

def closest_warehouse(latitude, longitude, warehouse_positions : dict) -> dict:
    min_dist = float('inf')
    closest = None
    for warehouse_id, position in warehouse_positions.items():
        dist = haversine_distance(
            latitude,
            longitude,
            position['latitude'],
            position['longitude']
        )
        if dist < min_dist:
            min_dist = dist
            closest = warehouse_id
    return closest

# ---------------------------------------------------------------------------------------------

def generate_path(orders: list[DeliveryOrder], first_order: DeliveryOrder) -> list[DeliveryOrder]:
    if not orders:
        return []
    start_order = first_order
    if start_order not in orders:
        return []
    path = [start_order]
    visited = {start_order.id}
    current_order = start_order
    while len(path) < len(orders):
        next_order = None
        min_distance = float('inf')
        for order in orders:
            if order.id not in visited:  
                distance = haversine_distance(
                    current_order.destination_position['latitude'], 
                    current_order.destination_position['longitude'], 
                    order.destination_position['latitude'], 
                    order.destination_position['longitude']
                )
                if distance < min_distance:
                    min_distance = distance
                    next_order = order
        if next_order:
            visited.add(next_order.id)  
            path.append(next_order)
            current_order = next_order
        else:
            break 
    return path

# ---------------------------------------------------------------------------------------------

def calculate_travel_distance(path : list[DeliveryOrder]) -> float:
    if len(path) < 2:
        return 0.0
    total_distance = 0.0
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]
        total_distance += haversine_distance(
            start.destination_position['latitude'], 
            start.destination_position['longitude'], 
            end.destination_position['latitude'], 
            end.destination_position['longitude']
        )
    return total_distance

# ---------------------------------------------------------------------------------------------

def calculate_capacity_level(orders: list[DeliveryOrder], max_capacity: int) -> float:
    total_weight = sum(order.weight for order in orders)
    capacity_level = total_weight / max_capacity
    return min(capacity_level, 1.0)

# ---------------------------------------------------------------------------------------------

def utility(num_orders: int, travel_distance: float, autonomy: float, capacity_level: float) -> float:
    if num_orders == 0:
        return float('-inf')
    capacity_utility = capacity_level
    if travel_distance > autonomy:
        travel_utility = float('-inf')
    else:
        travel_utility = 1 - (travel_distance / autonomy)
    final_utility = capacity_utility + travel_utility
    return final_utility

# ---------------------------------------------------------------------------------------------

def combine_orders(orders: list[DeliveryOrder], capacity: int) -> list[list[DeliveryOrder]]:
    valid_combinations = []
    for r in range(1, len(orders) + 1):
        valid_combinations.extend(
            list(combo) for combo in combinations(orders, r) if sum(order.weight for order in combo) <= capacity
        )
    return valid_combinations

# ---------------------------------------------------------------------------------------------

def best_available_orders(orders: list[DeliveryOrder], latitude: float, longitude: float, capacity: int, autonomy: float) -> list[DeliveryOrder]:
    order_sets = combine_orders(orders, capacity)
    best_set = None
    best_utility = float('-inf')
    for order_set in order_sets:
        closest = closest_order(latitude, longitude, order_set)
        distance_closest_order = haversine_distance(
            latitude, 
            longitude, 
            closest.destination_position['latitude'], 
            closest.destination_position['longitude']
        )
        path = generate_path(order_set, closest)
        travel_distance = distance_closest_order + calculate_travel_distance(path)
        capacity_level = calculate_capacity_level(order_set, capacity)
        set_utility = utility(len(order_set), travel_distance, autonomy, capacity_level)
        if set_utility >= best_utility:
            best_set = order_set
            best_utility = set_utility
    return best_set

# ----------------------------------------------------------------------------------------------
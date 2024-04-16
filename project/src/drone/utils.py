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

def generate_path(orders: list[DeliveryOrder], first_order: DeliveryOrder) -> list[DeliveryOrder]:
    if not orders:
        return []
    start_order = first_order
    if start_order not in orders:
        return []
    path = [start_order]
    visited = set(path)
    current_order = start_order
    while len(path) < len(orders):
        next_order = None
        min_distance = float('inf')
        for order in orders:
            if order not in visited:
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
            visited.add(next_order)
            path.append(next_order)
            current_order = next_order
        else:
            break 
    return path

# ---------------------------------------------------------------------------------------------

def calculate_travel_time(path : list[DeliveryOrder], velocity : float) -> float:
    if len(path) < 2:
        return 0.0
    total_time = 0.0
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]
        distance = haversine_distance(
            start.destination_position['latitude'], 
            start.destination_position['longitude'], 
            end.destination_position['latitude'], 
            end.destination_position['longitude']
        )
        travel_time = distance / velocity
        total_time += travel_time
    return total_time

# ---------------------------------------------------------------------------------------------

def calculate_capacity_level(orders: list[DeliveryOrder], max_capacity: int) -> float:
    total_weight = sum(order.weight for order in orders)
    capacity_level = total_weight / max_capacity
    return min(capacity_level, 1.0)

# ---------------------------------------------------------------------------------------------

def utility(travel_time : float, capacity_level : float) -> float:
    time_k = 0.1
    capacity_k = 2.0
    if travel_time <= 0:
        return float('-inf')
    # decreases with increasing travel time, sharply penalizes near-zero travel time
    travel_utility = - time_k * (1 / travel_time + travel_time)
    # maximize at capacity_level == 1, penalize deviation from 1
    capacity_utility = - capacity_k * (1 - capacity_level)**2
    # TODO: penalizes solutions that do not have enough autonomy to recharge in X warehouses
    autonomy_utility = 0.0
    return travel_utility + capacity_utility + autonomy_utility

# ---------------------------------------------------------------------------------------------

def combine_orders(orders : list[DeliveryOrder], capacity : int) -> list[list[DeliveryOrder]]:
    all_combinations = []
    for r in range(1, len(orders) + 1):
        all_combinations.extend(combinations(orders, r))
    valid_combinations = []
    for combo in all_combinations:
        if sum(order.weight for order in combo) <= capacity:
            valid_combinations.append(list(combo))
    return valid_combinations

# ---------------------------------------------------------------------------------------------

def best_available_orders(orders: list[DeliveryOrder], latitude: float, longitude: float, capacity: int, velocity: float) -> list[DeliveryOrder]:
    best_set = None
    best_utility = float('-inf')
    order_sets = combine_orders(orders, capacity)
    for order_set in order_sets:
        first_order = closest_order(latitude, longitude, order_set)
        path = generate_path(order_set, first_order)
        travel_time = calculate_travel_time(path, velocity)
        capacity_level = calculate_capacity_level(order_set, capacity)
        set_utility = utility(travel_time, capacity_level)
        if set_utility > best_utility:
            best_set = order_set
            best_utility = set_utility
    return best_set

# ----------------------------------------------------------------------------------------------
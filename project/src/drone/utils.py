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

def utility(travel_distance : float, velocity : float, capacity_level : float) -> float:
    travel_time = travel_distance / velocity
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
    order_sets = combine_orders(orders, capacity)
    best_set = None
    best_utility = float('-inf')
    for order_set in order_sets:
        first_order = closest_order(latitude, longitude, order_set)
        path = generate_path(order_set, first_order)
        travel_distance = calculate_travel_distance(path)
        capacity_level = calculate_capacity_level(order_set, capacity)
        set_utility = utility(travel_distance, velocity, capacity_level)
        if set_utility > best_utility:
            best_set = order_set
            best_utility = set_utility
    return best_set

# ----------------------------------------------------------------------------------------------

def best_order_decision(agent) -> str:
    winner = None
    
    orders = agent.next_orders
    closest = closest_order(agent.position["latitude"], agent.position["longitude"], orders)
    distance_closest_order = haversine_distance(
        agent.position["latitude"], 
        agent.position["longitude"], 
        closest.destination_position['latitude'], 
        closest.destination_position['longitude']
    )
    path = generate_path(orders, closest)
    travel_distance = distance_closest_order + calculate_travel_distance(path)
        
    capacity_level = calculate_capacity_level(orders, agent.params.max_capacity)
    drone_utility = utility(travel_distance, agent.params.velocity, capacity_level)
        
    for warehouse, orders in agent.available_order_sets.items():
        orders = agent.next_orders + orders    
        distance_warehouse = haversine_distance(
            agent.position["latitude"], 
            agent.position["longitude"], 
            agent.warehouse_positions[warehouse]['latitude'], 
            agent.warehouse_positions[warehouse]['longitude']
        )
        closest_to_warehouse = closest_order(
            agent.warehouse_positions[warehouse]['latitude'], 
            agent.warehouse_positions[warehouse]['longitude'], 
            orders
        )
        distance_warehouse_to_closest_order = haversine_distance(
            agent.warehouse_positions[warehouse]['latitude'], 
            agent.warehouse_positions[warehouse]['longitude'], 
            closest_to_warehouse.destination_position['latitude'], 
            closest_to_warehouse.destination_position['longitude']
        )
        path = generate_path(orders, closest_to_warehouse)
        travel_distance = distance_warehouse + distance_warehouse_to_closest_order + calculate_travel_distance(path)
            
        orders += agent.next_orders
        capacity_level = calculate_capacity_level(orders, agent.params.max_capacity)
        new_utility = utility(travel_distance, agent.params.velocity, capacity_level)
            
        if new_utility > drone_utility:
            winner = warehouse
            drone_utility = new_utility  
    
    return winner

# ----------------------------------------------------------------------------------------------
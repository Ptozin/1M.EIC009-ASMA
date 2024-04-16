# ----------------------------------------------------------------------------------------------

from order import DeliveryOrder
from misc.distance import haversine_distance

# ----------------------------------------------------------------------------------------------

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

def generate_path(orders : list[DeliveryOrder]) -> list[str]:
    # TODO: implement best path algorithm
    return []

def calculate_travel_time(path : list[str], velocity) -> float:
    # TODO: calculate travel time based on path and velocity
    return 0.0

def calculate_capacity_level(orders : list[DeliveryOrder], max_capacity : int) -> float:
    # TODO: calculate capacity level based on orders and max capacity
    return 0.0

def utility(travel_time : float, capacity_level : float) -> float:
    # TODO: implement utility function
    return 0.0

def combine_orders(orders : list[DeliveryOrder], capacity : int) -> list[list[DeliveryOrder]]:
    # TODO: generate sets of orders that can be delivered together taking autonomy and capacity into account
    pass

def best_available_orders(order_sets : list[list[DeliveryOrder]], capacity : int) -> list[DeliveryOrder]:
    # TODO: calculate utility for each set and return the best one
    return []

# ----------------------------------------------------------------------------------------------

def arrived_to_target(position, target_lat : float, target_lon : float) -> bool:
    return position['latitude'] == target_lat and position['longitude'] == target_lon

# ----------------------------------------------------------------------------------------------
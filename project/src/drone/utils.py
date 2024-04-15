# ----------------------------------------------------------------------------------------------

from src.order import DeliveryOrder

# ----------------------------------------------------------------------------------------------

def generate_path(orders : list[DeliveryOrder]) -> list[str]:
    # TODO: implement best path algorithm
    pass

def utility(self, orders : list[DeliveryOrder]) -> float:
    # TODO: utility formula (optimized path distance + capacity)
    return 0.0

def combine_orders(orders : list[DeliveryOrder]) -> list[list[DeliveryOrder]]:
    # TODO: generate sets of orders that can be delivered together taking autonomy and capacity into account
    pass

def best_order_set(order_sets : list[list[DeliveryOrder]]) -> list[str]:
    # TODO: calculate utility for each set and return the best one
    return []

# ----------------------------------------------------------------------------------------------

def arrived_to_target(position, target_lat : float, target_lon : float) -> bool:
    return position['latitude'] == target_lat and position['longitude'] == target_lon

# ----------------------------------------------------------------------------------------------
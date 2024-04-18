# ----------------------------------------------------------------------------------------------

import json
from spade.agent import Agent

from order import DeliveryOrder
from drone.parameters import DroneParameters
from misc.log import Logger
from drone.behaviours import *
from drone.utils import *
from flask_socketio import SocketIO

# ----------------------------------------------------------------------------------------------

STATE_AVAILABLE = "available"
STATE_SUGGEST = "suggest"
STATE_PICKUP = "pickup"
STATE_RECHARGE = "recharge"
STATE_DELIVER = "deliver"


# ----------------------------------------------------------------------------------------------

class DroneAgent(Agent):
    def __init__(self, id, jid, password, initialPos, capacity = 0, autonomy = 0, velocity = 0, warehouse_positions = {}, socketio : SocketIO = None) -> None:
        super().__init__(jid, password)
        self.total_orders : list[DeliveryOrder] = [] 
        self.next_orders : list[DeliveryOrder] = []
        self.next_order : DeliveryOrder = None
        self.next_warehouse : str = None
        
        self.required_autonomy : float = 0.0
        
        self.warehouse_positions : dict = warehouse_positions    
        self.distance_to_next_warehouse = 0.0
        self.available_order_sets : dict = {}
        self.orders_to_be_picked : dict[str, list[DeliveryOrder]] = {}
    
        self.position = {
            "latitude": warehouse_positions[initialPos]["latitude"],
            "longitude": warehouse_positions[initialPos]["longitude"]
        } 
        
        self.params = DroneParameters(id, capacity, autonomy, velocity)
        self.logger = Logger(filename = id)
        self.socketio = socketio
        self.orders_to_visualize : list[DeliveryOrder] = []
        
        
        self.warehouses_responses = []
        
    async def setup(self) -> None:
        """
        Agent's setup method. It adds the IdleBehav behaviour.
        """
        self.logger.log(f"{self.params.id} - [SETUP]")
        self.add_behaviour(EmitPositionBehaviour(period=1.0))
        fsm = FSMBehaviour()
        fsm.add_state(name=STATE_AVAILABLE, state=AvailableBehaviour(), initial=True)
        fsm.add_state(name=STATE_SUGGEST, state=OrderSuggestionsBehaviour())
        fsm.add_state(name=STATE_PICKUP, state=PickupOrdersBehaviour())
        fsm.add_transition(source=STATE_AVAILABLE, dest=STATE_SUGGEST)
        fsm.add_transition(source=STATE_SUGGEST, dest=STATE_PICKUP)
        self.add_behaviour(fsm)
        
        

    def __str__(self) -> str:
        return str(self.params)

    def __repr__(self) -> str:
        return json.dumps({
            "id": self.params.id,
            "capacity": self.params.max_capacity,
            "autonomy": self.params.max_autonomy,
            "velocity": self.params.velocity,
        })     
        
    # ----------------------------------------------------------------------------------------------

    def arrived_at_next_order(self):
        """
        Method to verify if the drone has arrived at the next order's destination.
        
        Returns:
            bool: True if the drone has arrived at the next order's destination, False otherwise.
        """
        return self.position["latitude"] == self.next_order.destination_position["latitude"] \
           and self.position["longitude"] == self.next_order.destination_position["longitude"]
           
    def arrived_at_next_warehouse(self):
        """
        Method to verify if the drone has arrived at the next warehouse.
        
        Returns:
            bool: True if the drone has arrived at the next warehouse, False otherwise.
        """
        return self.position["latitude"] == self.warehouse_positions[self.next_warehouse]["latitude"] \
           and self.position["longitude"] == self.warehouse_positions[self.next_warehouse]["longitude"]
        

    def any_warehouse_available(self) -> bool:
        """
        Method to check if there are any warehouses available.

        Returns:
            bool: True if there are available warehouses, False otherwise.
        """
        return len(self.warehouse_positions) > 0
    
    def remove_warehouse(self, warehouse_id : str) -> None:
        """
        Method to remove a warehouse from the available list.

        Args:
            warehouse_id (str): The id of the warehouse to remove.
        """
        self.warehouse_positions.pop(warehouse_id)
        
    def get_next_warehouse_position(self) -> tuple:
        """
        Method to get the next warehouse position.

        Returns:
            tuple: The latitude and longitude of the next warehouse.
        """
        return self.warehouse_positions[self.next_warehouse]['latitude'], self.warehouse_positions[self.next_warehouse]['longitude']
        
    # ----------------------------------------------------------------------------------------------

    def add_order(self, order : DeliveryOrder) -> None:
        """
        Method to add an order to the drone's current orders.
        Updates the current capacity and the current orders list.

        Args:
            order (DeliveryOrder): The order to add.
        """
        self.next_orders.append(order)
        self.total_orders.append(order)
        self.params.add_order(order.weight, order.get_order_destination_position())
        
    def drop_order(self, order : DeliveryOrder) -> None:
        """
        Method to remove an order from the drone's current orders.
        Updates the current capacity and empties the current order field

        Args:
            order (DeliveryOrder): The order to add.
        """
        self.params.drop_order(order.weight)
        self.next_orders.remove(order)
        self.next_order = None

        order.mark_as_delivered()
        self.orders_to_visualize.append(order)

# ----------------------------------------------------------------------------------------------

    def best_orders(self) -> tuple[str, list[DeliveryOrder]]:
        """
        Method to select the best orders for the drone from the available warehouses.

        Returns:
            tuple[str, list[DeliveryOrder]]: The warehouse id and the list of orders to pick up.
        """
        # For now, choose a random warehouse and the first N orders to fill the drone's capacity
        warehouse : str = list(self.available_order_sets.keys())[0]
        orders : list[DeliveryOrder] = []
        curr_capacity = 0
        for order in self.available_order_sets[warehouse]:
            if curr_capacity + order.weight <= self.params.max_capacity:
                orders.append(order)
                curr_capacity += order.weight
        
        return warehouse, orders
        
        

    def best_order_decision(self) -> str:
        # if winner is None, that means that it didn't receive any orders
        winner = None
        drone_utility = float('-inf')
        
        if self.next_orders:
            orders = self.next_orders
            closest = closest_order(self.position["latitude"], self.position["longitude"], orders)
            distance_closest_order = haversine_distance(
                self.position["latitude"], 
                self.position["longitude"], 
                closest.destination_position['latitude'], 
                closest.destination_position['longitude']
            )
            path = generate_path(orders, closest)
            travel_distance = distance_closest_order + calculate_travel_distance(path)
                
            capacity_level = calculate_capacity_level(orders, self.params.max_capacity)
            drone_utility = utility(travel_distance, self.params.velocity, capacity_level)
            
        print(f"{self.params.id} - [BEST ORDER DECISION] - {self.available_order_sets}")
        
        for warehouse, orders in self.available_order_sets.items():
            if self.next_orders:
                orders += self.next_orders
            distance_warehouse = haversine_distance(
                self.position["latitude"], 
                self.position["longitude"], 
                self.warehouse_positions[warehouse]['latitude'], 
                self.warehouse_positions[warehouse]['longitude']
            )
            closest_to_warehouse = closest_order(
                self.warehouse_positions[warehouse]['latitude'], 
                self.warehouse_positions[warehouse]['longitude'], 
                orders
            )
            distance_warehouse_to_closest_order = haversine_distance(
                self.warehouse_positions[warehouse]['latitude'], 
                self.warehouse_positions[warehouse]['longitude'], 
                closest_to_warehouse.destination_position['latitude'], 
                closest_to_warehouse.destination_position['longitude']
            )
            path = generate_path(orders, closest_to_warehouse)
            travel_distance = distance_warehouse + distance_warehouse_to_closest_order + calculate_travel_distance(path)
                
            orders += self.next_orders
            capacity_level = calculate_capacity_level(orders, self.params.max_capacity)
            new_utility = utility(travel_distance, self.params.velocity, capacity_level)
                
            if new_utility > drone_utility:
                winner = warehouse
                drone_utility = new_utility  
        
        return winner

# ----------------------------------------------------------------------------------------------

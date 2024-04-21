# ----------------------------------------------------------------------------------------------

import json
from spade.agent import Agent

from order import DeliveryOrder
from drone.parameters import DroneParameters
from misc.log import Logger
from drone.behaviours import *
from drone.utils import *
from flask_socketio import SocketIO
from misc.distance import haversine_distance, next_position

# ----------------------------------------------------------------------------------------------

STATE_AVAILABLE = "available"
STATE_SUGGEST = "suggest"
STATE_PICKUP = "pickup"
STATE_DELIVER = "deliver"
STATE_DEAD = "dead"

TIME_MULTIPLIER = 50000.0
INTERVAL_BETWEEN_TICKS = 0.030

# ----------------------------------------------------------------------------------------------

class DroneAgent(Agent):
    def __init__(self, id, jid, password, initialPos, capacity = 0, autonomy = 0, velocity = 0, warehouse_positions = {}, socketio : SocketIO = None) -> None:
        super().__init__(jid, password)
        self.total_orders : list[DeliveryOrder] = [] 
        self.next_orders : list[DeliveryOrder] = []
        self.next_order : DeliveryOrder = None
        self.next_warehouse : str = None
        
        self.required_warehouse : str = None # warehouse drone needs to go when autonomy runs out
        self.max_deliverable_order : DeliveryOrder = None # furthest order drone can deliver with autonomy leaving a warehouse
        
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
        
        self.need_to_stop = False
        
        self.warehouses_responses = []
        
        self.__distance_since_last_drop : float = 0.0
        self.tick_rate = INTERVAL_BETWEEN_TICKS
        
        # Helper
        self.died_sucessfully : bool | None = None
        
    async def setup(self) -> None:
        """
        Agent's setup method. It adds the IdleBehav behaviour.
        """
        self.logger.log(f"{self.params.id} - [SETUP]")
        self.add_behaviour(EmitPositionBehaviour(period=INTERVAL_BETWEEN_TICKS))
        fsm = FSMBehaviour()
        fsm.add_state(name=STATE_AVAILABLE, state=AvailableBehaviour(), initial=True)
        fsm.add_state(name=STATE_SUGGEST, state=OrderSuggestionsBehaviour())
        fsm.add_state(name=STATE_PICKUP, state=PickupOrdersBehaviour())
        fsm.add_state(name=STATE_DELIVER, state=DeliverOrdersBehaviour())
        fsm.add_state(name=STATE_DEAD, state=DeadBehaviour())
        fsm.add_transition(source=STATE_AVAILABLE, dest=STATE_SUGGEST)
        fsm.add_transition(source=STATE_SUGGEST, dest=STATE_PICKUP)
        fsm.add_transition(source=STATE_SUGGEST, dest=STATE_DELIVER)
        fsm.add_transition(source=STATE_PICKUP, dest=STATE_DELIVER)
        fsm.add_transition(source=STATE_DELIVER, dest=STATE_AVAILABLE)
        
        fsm.add_transition(source=STATE_AVAILABLE, dest=STATE_DEAD)
        fsm.add_transition(source=STATE_SUGGEST, dest=STATE_DEAD)
        fsm.add_transition(source=STATE_PICKUP, dest=STATE_DEAD)
        fsm.add_transition(source=STATE_DELIVER, dest=STATE_DEAD)
        
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

    def get_current_metrics(self):
        return {
            'id': self.params.id,
            'latitude': self.position['latitude'],
            'longitude': self.position['longitude'],
            'distance': self.params.metrics_total_distance,
            'capacity': round(self.params.curr_capacity * 100.0/self.params.max_capacity,2),
            'autonomy': round(self.params.curr_autonomy * 100.0/self.params.max_autonomy,2),
            'orders_delivered': self.params.orders_delivered,
            'type': 'drone'
        }

    def recharge(self) -> None:
        """
        Method to recharge the drone.
        """
        warehouse = self.warehouse_positions[self.next_warehouse]
        self.params.refill_autonomy(warehouse)

    def update_position(self, target_latitude : float, target_longitude : float) -> None:
        self.logger.log("[TRAVELLING] - Distance to target: {} meters"\
            .format(round(haversine_distance(
                        self.position['latitude'], self.position['longitude'], 
                        target_latitude, target_longitude), 2)))
                
        position, distance = next_position(
            self.position['latitude'], self.position['longitude'],
            target_latitude, target_longitude,
            self.params.velocity * TIME_MULTIPLIER * self.tick_rate
        )
        
        self.__distance_since_last_drop += distance
        self.params.update_distance(distance)
        
        self.position = position
        
        if self.params.is_out_of_autonomy():
            self.logger.log(f"[ERROR] Drone out of battery")

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

    def has_inventory(self) -> bool:
        """
        Method to check if the drone has any orders in its inventory.

        Returns:
            bool: True if the drone has orders in its inventory, False otherwise.
        """
        return len(self.next_orders) > 0        

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
        
    def get_next_order_position(self) -> tuple:
        """
        Method to get the next order position.

        Returns:
            tuple: The latitude and longitude of the next order.
        """
        return self.next_order.destination_position['latitude'], self.next_order.destination_position['longitude']    
    
    # ----------------------------------------------------------------------------------------------

    def add_order(self, order : DeliveryOrder) -> None:
        """
        Method to add an order to the drone's current orders.
        Updates the current capacity and the current orders list.

        Args:
            order (DeliveryOrder): The order to add.
        """
        #TODO: verify if this doesn't f the frontend
        order.mark_as_taken()
        
        self.next_orders.append(order)
        self.next_order = order
        self.params.add_order(order.weight)
        
    def drop_order(self) -> None:
        """
        Method to remove an order from the drone's current orders.
        Updates the current capacity and empties the current order field

        """
        
        order = self.next_orders.pop(0) 
        self.logger.log("[DELIVERING] - Order {} delivered".format(order.id))
        self.params.drop_order(order.weight, self.__distance_since_last_drop,  order.get_order_destination_position())
        # Only append the order to the total orders list if it has been delivered
        self.total_orders.append(order)
        
        order.mark_as_delivered()
        self.orders_to_visualize.append(order)
        
        self.next_order = order
        
        self.__distance_since_last_drop = 0.0

    # ----------------------------------------------------------------------------------------------
    
    def tasks_in_range(self) -> None:
        '''
        Method that checks the furthest order that can be delivered with autonomy, 
        after having next orders defined in a warehouse.
        '''
        
        self.required_warehouse = None
        self.max_deliverable_order = None
        distance_max_order = 0.0
        current_position = self.position
        
        for order in self.next_orders:
            distance_max_order += haversine_distance(
                current_position['latitude'], 
                current_position['longitude'],
                order.destination_position['latitude'],
                order.destination_position['longitude']
            )
            current_position = order.destination_position
            closest_warehouse_to_order = closest_warehouse(
                order.destination_position['latitude'],
                order.destination_position['longitude'],
                self.warehouse_positions
            )
            distance_order_to_warehouse = haversine_distance(
                order.destination_position['latitude'],
                order.destination_position['longitude'],
                self.warehouse_positions[closest_warehouse_to_order]['latitude'],
                self.warehouse_positions[closest_warehouse_to_order]['longitude']
            )
            total_required_distance = distance_max_order + distance_order_to_warehouse
            if total_required_distance <= self.params.curr_autonomy:
                self.max_deliverable_order = order
                break
        
        if self.max_deliverable_order == self.next_orders[-1]:
            self.max_deliverable_order = None
    
    # ----------------------------------------------------------------------------------------------

    def best_orders(self) -> tuple[None|str, list[DeliveryOrder]]:
        """
        Method to select the best orders for the drone from the available warehouses.

        Returns:
            tuple[None|str, list[DeliveryOrder]]: The warehouse id and the list of orders to pick up.
        """
        winner : str | None = None
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
                
            capacity_level = calculate_capacity_level(orders, self.params.max_capacity - self.params.curr_capacity)
            drone_utility = utility(len(orders), travel_distance, self.params.curr_autonomy, capacity_level)
        
        for warehouse, orders in self.available_order_sets.items():
            if orders is None:
                continue
            new_orders = orders.copy()
            if self.next_orders:
                new_orders += self.next_orders
            distance_warehouse = haversine_distance(
                self.position["latitude"], 
                self.position["longitude"], 
                self.warehouse_positions[warehouse]['latitude'], 
                self.warehouse_positions[warehouse]['longitude']
            )
            closest_to_warehouse = closest_order(
                self.warehouse_positions[warehouse]['latitude'], 
                self.warehouse_positions[warehouse]['longitude'], 
                new_orders
            )
            distance_warehouse_to_closest_order = haversine_distance(
                self.warehouse_positions[warehouse]['latitude'], 
                self.warehouse_positions[warehouse]['longitude'], 
                closest_to_warehouse.destination_position['latitude'], 
                closest_to_warehouse.destination_position['longitude']
            )
            path = generate_path(new_orders, closest_to_warehouse)
            travel_distance = distance_warehouse + distance_warehouse_to_closest_order + calculate_travel_distance(path)
            capacity_level = calculate_capacity_level(new_orders, self.params.max_capacity - self.params.curr_capacity)
            new_utility = utility(len(new_orders), travel_distance, self.params.max_autonomy, capacity_level)
                
            if new_utility >= drone_utility:
                winner = warehouse
                drone_utility = new_utility
                
        return (winner, self.available_order_sets[winner] if winner else [])
        
# ----------------------------------------------------------------------------------------------

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
STATE_DELIVER = "deliver"
STATE_DEAD = "dead"

TIME_MULTIPLIER = 500.0


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
        fsm.add_state(name=STATE_DELIVER, state=DeliverOrdersBehaviour())
        fsm.add_state(name=STATE_DEAD, state=DeadBehaviour())
        fsm.add_transition(source=STATE_AVAILABLE, dest=STATE_SUGGEST)
        fsm.add_transition(source=STATE_SUGGEST, dest=STATE_PICKUP)
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

    def recharge(self) -> None:
        """
        Method to recharge the drone.
        """
        self.params.curr_autonomy = self.params.max_autonomy

    def update_position(self, target_latitude : float, target_longitude : float) -> None:
        position = next_position(
            self.position['latitude'], self.position['longitude'],
            target_latitude, target_longitude,
            self.params.velocity * TIME_MULTIPLIER
        )
            
        self.params.curr_autonomy -= haversine_distance(
            self.position['latitude'], self.position['longitude'],
            position['latitude'], position['longitude']
        )
        
        self.position = position
        
        if self.params.curr_autonomy < 0:
            self.logger.log(f"Drone out of battery")
            raise Exception("Drone out of battery")
        

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
        self.params.add_order(order.weight, order.get_order_destination_position())
        
    def drop_order(self) -> None:
        """
        Method to remove an order from the drone's current orders.
        Updates the current capacity and empties the current order field

        """
        
        order = self.next_orders.pop(0) 
        self.params.drop_order(order.weight)
        # Only append the order to the total orders list if it has been delivered
        self.total_orders.append(order)
        
        order.mark_as_delivered()
        self.orders_to_visualize.append(order)
        
        self.next_order = order

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
        
# ----------------------------------------------------------------------------------------------

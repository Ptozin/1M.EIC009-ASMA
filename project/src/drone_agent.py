# ----------------------------------------------------------------------------------------------

import json
import datetime
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
from misc.distance import haversine_distance, next_position
from order import DeliveryOrder
from misc.log import Logger

# ----------------------------------------------------------------------------------------------

STATE_IDLE = 0
STATE_DELIVERING = 10
STATE_DISMISSED = 20
STATE_ERROR = 30
STATE_RETURNED = 40

TIME_MULTIPLIER = 500 # increases the speed per tick to 10km/s, with a base velocity of 20 m/s

# ----------------------------------------------------------------------------------------------

class DroneParameters:
    def __init__(self, id : str, capacity : int, autonomy : float , velocity : float) -> None:
        # ---- Metrics ----
        self.__total_trips : int = 0
        self.__total_distance : float = 0.0 # Can be converted to time with velocity
        self.__min_distance_on_trip : float = float('inf') # Measured in meters
        self.__max_distance_on_trip : float = 0.0 # Measured in meters
        self.__avg_distance_on_trip : float = 0.0 # Measured in meters
        self.orders_delivered : int = 0 # Total Orders Delivered
        self.__orders_to_deliver : int = 0 # Number of orders carried by the drone on the current trip
        self.__occupiance_rate : float = 0.0 # Average Occupiance Rate Per Trip, calculated with `orders_delivered / total_trips`
        self.__energy_consumption : float = 0.0 # Total Energy Consumption, calculated with `total_distance / autonomy`

        # --- Parameters ---
        self.id : str = id
        self.velocity : float = velocity # in m/s
        self.max_capacity : int = capacity # in kg
        self.max_autonomy : float = autonomy # in meters
        self.curr_capacity : int = 0
        self.curr_autonomy : float = autonomy
    
    def add_trip(self, distance : float) -> None:
        self.__total_trips += 1
        self.__total_distance += distance
        self.__min_distance_on_trip = min(self.__min_distance_on_trip, distance)
        self.__max_distance_on_trip = max(self.__max_distance_on_trip, distance)
        self.__avg_distance_on_trip = self.__total_distance / self.__total_trips
        self.__occupiance_rate = self.orders_delivered / self.__total_trips
        self.__energy_consumption = self.__total_distance / self.max_autonomy
        
    def add_order(self, capacity : int) -> None:
        self.__orders_to_deliver += 1
        self.curr_capacity += capacity
    
    def drop_order(self, capacity : int) -> None:
        self.__orders_to_deliver -= 1
        self.orders_delivered += 1
        self.curr_capacity -= capacity
        
    def __str__(self) -> str:
        return "{} - Drone with capacity ({}/{}) and autonomy ({}/{}) delivering {} orders, with {} completed orders"\
            .format(self.id, self.curr_capacity, self.max_capacity, 
                    round(self.curr_autonomy,2), self.max_autonomy, 
                    self.__orders_to_deliver, self.orders_delivered)
            
    def __repr__(self) -> str:
        return json.dumps({
            "id":       self.id,
            "capacity": self.max_capacity,
            "autonomy": self.max_autonomy,
            "velocity": self.velocity,
        })
        
    def metrics(self) -> None:
        """
        Method to print the final metrics of the drone.
        """
        
        # Set the final metrics
        self.__occupiance_rate = self.orders_delivered / self.__total_trips
        
        return "{} Metrics - {}"\
              .format(self.id, 
                        [
                            {"Total Trips": self.__total_trips},
                            {"Total Distance": round(self.__total_distance,2)},
                            {"Min Distance": round(self.__min_distance_on_trip,2)},
                            {"Max Distance": round(self.__max_distance_on_trip,2)},
                            {"Avg Distance": round(self.__avg_distance_on_trip,2)},
                            {"Orders Delivered": self.orders_delivered},
                            {"Occupiance Rate": round(self.__occupiance_rate,2)},
                            {"Energy Consumption": str(round(self.__energy_consumption * 100,2)) + "%"}
                        ]
                    )
              
        
# ----------------------------------------------------------------------------------------------

class IdleBehav(CyclicBehaviour):
    async def on_start(self) -> None:
        self.counter = 0
        self.limit = 3
    
    
    async def run(self):
        target = self.agent.closest_warehouse()
        msg = Message(to=target)
        msg.set_metadata("performative", "inform")
        msg.body = self.agent.__repr__()
        await self.send(msg)
        msg = await self.receive(timeout=5)
        if msg is None:
            self.counter += 1
            if self.counter >= self.limit:
                self.kill(exit_code=STATE_DISMISSED)
                return 
            self.agent.logger.log(f"[{self.agent.params.id}] Waiting for tasks...")
        else:
            self.counter = 0            
            if msg.metadata["performative"] == "inform":
                proposed_orders = json.loads(msg.body)
                orders = []
                for order in proposed_orders:
                    order = json.loads(order)
                    orders.append(DeliveryOrder(**order))
                    
                # TODO: Required Autonomy should be taken into account later
                self.agent.required_autonomy = self.agent.compute_route(orders)
                self.kill(exit_code=STATE_DELIVERING)
                
            elif msg.metadata["performative"] == "refuse":
                # remove warehouse from available list, since it has no orders
                self.agent.logger.log(f"[REFUSED] {self.agent.params.id} - {msg.sender}")
                self.agent.remove_warehouse(target.split("@")[0])
                
                # if no more warehouses available, dismiss agent
                if not self.agent.available_warehouses():
                    self.kill(exit_code=STATE_DISMISSED)
            
    async def on_end(self):
        if self.exit_code == STATE_DELIVERING:
            self.agent.add_behaviour(DelivBehav(period=1.0, start_at=datetime.datetime.now()))
        elif self.exit_code == STATE_DISMISSED:
            # Show agent metrics and stop
            self.agent.logger.log(self.agent.params.metrics())
            await self.agent.stop()
            
# ----------------------------------------------------------------------------------------------

class DelivBehav(PeriodicBehaviour):
    async def run(self):
        if len(self.agent.curr_orders) == 0:
            self.kill()
        else:
            if self.agent.curr_order is None:
                self.agent.curr_order = self.agent.curr_orders[0]
                            
            position = next_position(
                    self.agent.position['latitude'],
                    self.agent.position['longitude'],
                    self.agent.curr_order.destination_position['latitude'],
                    self.agent.curr_order.destination_position['longitude'],
                    self.agent.params.velocity * TIME_MULTIPLIER
                )
            
            self.agent.params.curr_autonomy -= haversine_distance(
                self.agent.position['latitude'],
                self.agent.position['longitude'],
                position['latitude'],
                position['longitude']
            )
            
            self.agent.position = position
            
            self.agent.logger.log("[DELIVERING] {} - {} meters to next drop-off"\
                .format(str(self.agent), 
                        round(
                            haversine_distance(self.agent.position['latitude'], 
                                           self.agent.position['longitude'], 
                                           self.agent.curr_order.destination_position['latitude'], 
                                           self.agent.curr_order.destination_position['longitude']),
                            2
                        ))
                )
            
            if self.agent.arrived_to_target(self.agent.curr_order.destination_position['latitude'], self.agent.curr_order.destination_position['longitude']):
                self.agent.drop_order(self.agent.curr_order)
    
    async def on_end(self):
        self.agent.add_behaviour(ReturnBehav(period=1.0, start_at=datetime.datetime.now()))
                
# ----------------------------------------------------------------------------------------------

class ReturnBehav(PeriodicBehaviour):
    async def run(self):
        if not self.agent.available_warehouses():
            self.kill(exit_code=STATE_ERROR)
            return 

        # TODO: later dynamically define next warehouse based on proposals

        self.agent.position = next_position(
                self.agent.position['latitude'],
                self.agent.position['longitude'],
                self.agent.warehouse_positions[self.agent.next_warehouse]['latitude'],
                self.agent.warehouse_positions[self.agent.next_warehouse]['longitude'],
                self.agent.params.velocity * TIME_MULTIPLIER
            )
        
        if self.agent.arrived_to_target(self.agent.warehouse_positions[self.agent.next_warehouse]['latitude'], self.agent.warehouse_positions[self.agent.next_warehouse]['longitude']):
            self.agent.params.curr_autonomy = self.agent.params.max_autonomy
            self.agent.next_warehouse = None
            self.kill(exit_code=STATE_RETURNED)
        else:
            self.agent.logger.log("[RETURNING] {} - Distance to warehouse: {} meters"\
                .format(self.agent.params.id, 
                        round(haversine_distance(
                            self.agent.position['latitude'], 
                            self.agent.position['longitude'], 
                            self.agent.warehouse_positions[self.agent.next_warehouse]['latitude'], 
                            self.agent.warehouse_positions[self.agent.next_warehouse]['longitude']
                        ),2)
                    )
                )
    
    async def on_end(self):
        if self.exit_code == STATE_ERROR:
            self.agent.logger.log(f"[ERROR] {self.agent.params.id} - No warehouse available to return to. Self Destruction activated.")
            await self.agent.stop()
        elif self.exit_code == STATE_RETURNED:
            self.agent.logger.log(f"[RETURNED] {self.agent.params.id}")
            self.agent.add_behaviour(IdleBehav())
        else:
            self.agent.logger.log(f"[ERROR] {self.agent.params.id} - Unexpected error")
            await self.agent.stop()
        
# ----------------------------------------------------------------------------------------------
        
class DroneAgent(Agent):
    def __init__(self, id, jid, password, initialPos, capacity = 0, autonomy = 0, velocity = 0, warehouse_positions = {}) -> None:
        super().__init__(jid, password)
        self.total_orders : list[DeliveryOrder] = [] 
        self.curr_orders : list[DeliveryOrder] = []
        self.curr_order : DeliveryOrder = None
        
        self.required_autonomy : float = 0.0
        
        self.warehouse_positions : dict = warehouse_positions    
        self.next_warehouse : dict = None
        self.distance_to_next_warehouse = 0.0
    
        self.position = {
            "latitude": warehouse_positions[initialPos]["latitude"],
            "longitude": warehouse_positions[initialPos]["longitude"]
        } 
        
        self.params = DroneParameters(id, capacity, autonomy, velocity)
        
        self.logger = Logger(filename = id)

    def destiny_warehouse(self, latitude : float, longitude : float) -> str:
        """
        Method to find the destiny warehouse to the unarbitrary position.

        Returns:
            str: The ID of the closest warehouse.
        """
        min_dist = float('inf')
        closest = None
        for warehouse_id, parameters in self.warehouse_positions.items():
            dist = haversine_distance(
                latitude,
                longitude,
                parameters['latitude'],
                parameters['longitude']
            )
            if dist < min_dist:
                min_dist = dist
                closest = warehouse_id
        return closest
    
    def closest_warehouse(self, retrieve_JID : bool = True) -> str:
        """
        Method to find the closest warehouse to the drone.

        Returns:
            str: The JID or ID of the closest warehouse.
        """
        min_dist = float('inf')
        closest = None
        for warehouse_id, parameters in self.warehouse_positions.items():
            dist = haversine_distance(
                self.position['latitude'],
                self.position['longitude'],
                parameters['latitude'],
                parameters['longitude']
            )
            if dist < min_dist:
                min_dist = dist
                closest = parameters['jid'] if retrieve_JID else warehouse_id
        return closest
    
    def available_warehouses(self) -> bool:
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

    def arrived_to_target(self, target_lat : float, target_lon : float) -> bool:
        return self.position['latitude'] == target_lat and self.position['longitude'] == target_lon

# ----------------------------------------------------------------------------------------------
# Orders management
# ----------------------------------------------------------------------------------------------

    def closest_order(self) -> DeliveryOrder:
        """
        Method to find the closest order to the drone.

        Returns:
            DeliveryOrder: The closest order.
        """
        min_dist = float('inf')
        closest = None
        for order in self.curr_orders:
            dist = haversine_distance(
                self.position['latitude'],
                self.position['longitude'],
                order.destination_position['latitude'],
                order.destination_position['longitude']
            )
            if dist < min_dist:
                min_dist = dist
                closest = order
        return closest

    def add_order(self, order : DeliveryOrder) -> None:
        """
        Method to add an order to the drone's current orders.
        Updates the current capacity and the current orders list.

        Args:
            order (DeliveryOrder): The order to add.
        """
        self.curr_orders.append(order)
        self.total_orders.append(order)
        self.params.add_order(order.weight)

    def drop_order(self, order : DeliveryOrder) -> None:
        """
        Method to remove an order from the drone's current orders.
        Updates the current capacity and empties the current order field

        Args:
            order (DeliveryOrder): The order to add.
        """
        self.params.drop_order(order.weight)
        self.curr_orders.remove(order)
        self.curr_order = None

    def compute_route(self, orders : list[DeliveryOrder]) -> float:
        """
        Computes the delivery route using a greedy approach and calculates the total distance.
        
        Args:
            orders (list[DeliveryOrder]): A list of DeliveryOrder objects to be delivered.
        
        Returns:
            float: The total distance of the route for fuel estimation.
        """
        total_distance = 0.0
        if orders:
            first_order = min(orders, key=lambda order: haversine_distance(
                self.position['latitude'], self.position['longitude'],
                order.destination_position['latitude'], order.destination_position['longitude']))
            total_distance += haversine_distance(
                self.position['latitude'], self.position['longitude'],
                first_order.destination_position['latitude'], first_order.destination_position['longitude'])
            ordered_queue = [first_order]
            orders.remove(first_order)
            while orders:
                last_order = ordered_queue[-1]
                next_order = min(orders, key=lambda order: haversine_distance(
                    last_order.destination_position['latitude'], last_order.destination_position['longitude'],
                    order.destination_position['latitude'], order.destination_position['longitude']))
                total_distance += haversine_distance(
                    last_order.destination_position['latitude'], last_order.destination_position['longitude'],
                    next_order.destination_position['latitude'], next_order.destination_position['longitude'])
                ordered_queue.append(next_order)
                orders.remove(next_order)
            for order in ordered_queue:
                self.add_order(order)
            if self.curr_orders:
                last_order_position = self.curr_orders[-1].destination_position
                closest_warehouse = self.destiny_warehouse(last_order_position['latitude'], last_order_position['longitude'])
                total_distance += haversine_distance(
                    last_order_position['latitude'], last_order_position['longitude'],
                    self.warehouse_positions[closest_warehouse]['latitude'], self.warehouse_positions[closest_warehouse]['longitude'])
                self.next_warehouse = closest_warehouse
                
        self.params.add_trip(total_distance)        
                
        return total_distance

# ----------------------------------------------------------------------------------------------

    async def setup(self) -> None:
        print(f"{self.params.id} - [SETUP]")
        self.add_behaviour(IdleBehav())

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
    
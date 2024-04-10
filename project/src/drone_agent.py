# ----------------------------------------------------------------------------------------------

import json
import datetime
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
from misc.distance import haversine_distance, next_position
from order import DeliveryOrder

# ----------------------------------------------------------------------------------------------

STATE_IDLE = 0
STATE_DELIVERING = 10
STATE_DISMISSED = 20
STATE_ERROR = 30
STATE_RETURNED = 40

TIME_MULTIPLIER = 500 # increases the speed to 10km/s

# ----------------------------------------------------------------------------------------------

class IdleBehav(CyclicBehaviour):
    async def run(self):
        target = self.agent.closest_warehouse()
        msg = Message(to=target)
        msg.set_metadata("performative", "inform")
        msg.body = self.agent.__repr__()
        await self.send(msg)
        msg = await self.receive(timeout=5)
        if msg is None:
            print(f"[{self.agent.id}] Waiting for tasks...")
        else:            
            if msg.metadata["performative"] == "inform":
                orders = json.loads(msg.body) # TODO: later check if it even wants to accept the task
                for order in orders:
                    order = json.loads(order)
                    self.agent.curr_orders.append(DeliveryOrder(**order))
                
                self.kill(exit_code=STATE_DELIVERING)
                
            elif msg.metadata["performative"] == "refuse":
                # remove warehouse from available list, since it has no orders
                print(f"{self.agent.id} - [REFUSED] {msg.sender}")
                self.agent.remove_warehouse(target.split("@")[0])
                
                # if no more warehouses available, dismiss agent
                if not self.agent.available_warehouses():
                    self.kill(exit_code=STATE_DISMISSED)
            
    async def on_end(self):
        if self.exit_code == STATE_DELIVERING:
            self.agent.add_behaviour(DelivBehav(period=1.0, start_at=datetime.datetime.now()))
        elif self.exit_code == STATE_DISMISSED:
            await self.agent.stop()
            
# ----------------------------------------------------------------------------------------------

class DelivBehav(PeriodicBehaviour):
    async def run(self):
        if len(self.agent.curr_orders) == 0:
            self.kill()
        else:
            if self.agent.curr_order is None:
                self.agent.curr_order = self.agent.closest_order()
            self.agent.position = next_position(
                    self.agent.position['latitude'],
                    self.agent.position['longitude'],
                    self.agent.curr_order.destination_position['latitude'],
                    self.agent.curr_order.destination_position['longitude'],
                    self.agent.velocity * TIME_MULTIPLIER
                )
            
            print(f"{self.agent.id} - [DELIVERING] {len(self.agent.curr_orders)} orders - {haversine_distance(self.agent.position['latitude'], self.agent.position['longitude'], self.agent.curr_order.destination_position['latitude'], self.agent.curr_order.destination_position['longitude'])} meters to target")
            
            if self.agent.arrived_to_target(self.agent.curr_order.destination_position['latitude'], self.agent.curr_order.destination_position['longitude']):
                # TODO: add autonomy consumption and fix capacity
                self.agent.curr_capacity += self.agent.curr_order.weight
                self.agent.position['latitude'] = self.agent.curr_order.destination_position['latitude']
                self.agent.position['longitude'] = self.agent.curr_order.destination_position['longitude']
                self.agent.curr_orders.remove(self.agent.curr_order)
                self.agent.curr_order = None
    
    async def on_end(self):
        self.agent.add_behaviour(ReturnBehav(period=1.0, start_at=datetime.datetime.now()))
                
# ----------------------------------------------------------------------------------------------

class ReturnBehav(PeriodicBehaviour):
    async def run(self):
        if not self.agent.available_warehouses():
            self.kill(exit_code=STATE_ERROR)
            return 
        
        if self.agent.curr_warehouse is None:
            self.agent.curr_warehouse = self.agent.closest_warehouse(retrieve_JID=False)
                
        self.agent.position = next_position(
                self.agent.position['latitude'],
                self.agent.position['longitude'],
                self.agent.warehouse_positions[self.agent.curr_warehouse]['latitude'],
                self.agent.warehouse_positions[self.agent.curr_warehouse]['longitude'],
                self.agent.velocity * TIME_MULTIPLIER
            )
        
        if self.agent.arrived_to_target(self.agent.warehouse_positions[self.agent.curr_warehouse]['latitude'], self.agent.warehouse_positions[self.agent.curr_warehouse]['longitude']):     
            self.agent.curr_warehouse = None
            self.kill(exit_code=STATE_RETURNED)
        else:
            # show prints of the distance to the warehouse
            print(f"{self.agent.id} - [RETURNING] - Distance to warehouse: {haversine_distance(self.agent.position['latitude'], self.agent.position['longitude'], self.agent.warehouse_positions[self.agent.curr_warehouse]['latitude'], self.agent.warehouse_positions[self.agent.curr_warehouse]['longitude'])} meters")
    
    async def on_end(self):
        if self.exit_code == STATE_ERROR:
            print (f"{self.agent.id} - [ERROR] - No warehouse available to return to.")
            await self.agent.stop()
        elif self.exit_code == STATE_RETURNED:
            print(f"{self.agent.id} - [RETURNED]")
            self.agent.add_behaviour(IdleBehav())
        else:
            print(f"{self.agent.id} - [ERROR] - Unexpected error")
            await self.agent.stop()
        
# ----------------------------------------------------------------------------------------------
        
class DroneAgent(Agent):
    def __init__(self, id, jid, password, initialPos, capacity = 0, autonomy = 0, velocity = 0, warehouse_positions = {}):
        super().__init__(jid, password)
        self.id : str = id
        self.max_capacity : float = capacity # in kg
        self.max_autonomy : float = autonomy # in meters
        self.velocity : float = velocity # in m/s
        
        self.curr_capacity : float = 0.0
        self.curr_autonomy : float = autonomy
        self.curr_orders : list[DeliveryOrder] = []
        self.curr_order = None
        
        self.warehouse_positions : dict = warehouse_positions    
        self.curr_warehouse : dict = None
        self.distance_to_curr_warehouse = 0.0
    
        self.position = {
            "latitude": warehouse_positions[initialPos]["latitude"],
            "longitude": warehouse_positions[initialPos]["longitude"]
        } 

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
    
    def closest_order(self):
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

    def arrived_to_target(self, target_lat, target_lon):
        # check if it can be perfectly equal in coords (or if it needs a tolerance)
        return self.position['latitude'] == target_lat and self.position['longitude'] == target_lon

    async def setup(self):
        print(f"{self.id} - [SETUP]")
        self.add_behaviour(IdleBehav())

    def __str__(self) -> str:
        return "{} - Drone with capacity {} and autonomy {}"\
            .format(str(self.id), self.max_capacity, self.max_capacity, 
                    self.velocity, self.warehouse_positions)
            
    def __repr__(self) -> str:
        return json.dumps({
            "id": self.id,
            "capacity": self.max_capacity,
            "autonomy": self.max_autonomy,
            "velocity": self.velocity,
        })
            
# ----------------------------------------------------------------------------------------------
    
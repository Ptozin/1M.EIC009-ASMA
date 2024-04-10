# ----------------------------------------------------------------------------------------------

import json
import datetime
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
from misc.distance import haversine_distance

# ----------------------------------------------------------------------------------------------

STATE_IDLE = 0
STATE_DELIVERING = 10
STATE_DISMISSED = 20

# ----------------------------------------------------------------------------------------------

class IdleBehav(CyclicBehaviour):
    async def run(self):
        target = self.agent.closest_warehouse() + "@localhost"
        msg = Message(to=target)
        msg.set_metadata("performative", "inform")
        msg.body = json.dumps({
            "id": self.agent.id,
            "capacity": self.agent.max_capacity,
            "autonomy": self.agent.max_autonomy,
            "velocity": self.agent.velocity
        })
        await self.send(msg)
        msg = await self.receive(timeout=5)
        if msg is None:
            print(f"[{self.agent.id}] Waiting for tasks...")
        else:
            print(f"\n{self.agent.id} - [MESSAGE] {msg.body}\n")
            self.agent.curr_orders = json.loads(msg.body) # TODO: later check if it even wants to accept the task
            if self.agent.curr_orders:
                self.kill(exit_code=STATE_DELIVERING)
            else:
                pass
                # remove warehouse from available list, since it has no orders
                #self.agent.update_warehouses_available(target.split("@")[0])
                
                # if no more warehouses available, dismiss agent
                #if !self.agent.available_warehouses():
                #    self.kill(exit_code=STATE_DISMISSED)
            
    async def on_end(self):
        #if self.exit_code == STATE_DELIVERING:
            self.agent.add_behaviour(DelivBehav(period=1.0, start_at=datetime.datetime.now()))
        #elif self.exit_code == STATE_DISMISSED:
        #    await self.agent.stop()
            
# ----------------------------------------------------------------------------------------------

class DelivBehav(PeriodicBehaviour):
    async def run(self):
        print(f"{self.agent.id} - [DELIVERING] {len(self.agent.curr_orders)} orders")
        if len(self.agent.curr_orders) == 0:
            self.kill()
        else:
            if self.agent.curr_order is None:
                self.agent.curr_order = self.agent.closest_order()
                self.agent.distance_to_curr_order = haversine_distance(
                    self.agent.position['latitude'],
                    self.agent.position['longitude'],
                    self.agent.curr_order['latitude'],
                    self.agent.curr_order['longitude']
                )

            #print(f"{self.agent.id} - [DELIVERING] {self.agent.distance_to_curr_order}km to {self.agent.curr_order['id']}")
            self.agent.distance_to_curr_order -= 1 # self.agent.velocity * 0.001 # hardcoded 1km per second for testing purposes
            if self.agent.distance_to_curr_order <= 0:
                self.agent.curr_capacity += self.agent.curr_order['weight']
                self.agent.curr_autonomy -= self.agent.distance_to_curr_order # TODO: add autonomy consumption
                self.agent.position['latitude'] = self.agent.curr_order['latitude']
                self.agent.position['longitude'] = self.agent.curr_order['longitude']
                self.agent.curr_orders.remove(self.agent.curr_order)
                self.agent.curr_order = None
                self.agent.distance_to_curr_order = 0.0
    
    async def on_end(self):
        self.agent.add_behaviour(ReturnBehav(period=1.0, start_at=datetime.datetime.now()))
                
# ----------------------------------------------------------------------------------------------

class ReturnBehav(PeriodicBehaviour):
    async def run(self):
        if self.agent.curr_warehouse is None:
            self.agent.curr_warehouse = self.agent.closest_warehouse()
            self.agent.distance_to_curr_warehouse = haversine_distance(
                self.agent.position['latitude'],
                self.agent.position['longitude'],
                self.agent.warehouse_positions[self.agent.curr_warehouse]['latitude'],
                self.agent.warehouse_positions[self.agent.curr_warehouse]['longitude']
            )

        print(f"{self.agent.id} - [RETURNING] to {self.agent.curr_warehouse}")            
        self.agent.distance_to_curr_warehouse -= 1 # self.agent.velocity * 0.001 # hardcoded 1km per second for testing purposes
        if self.agent.distance_to_curr_warehouse <= 0:
            self.agent.curr_warehouse = None
            self.agent.distance_to_curr_warehouse = 0.0
            self.kill()
    
    async def on_end(self):
        self.agent.add_behaviour(IdleBehav())
        
# ----------------------------------------------------------------------------------------------
        
class DroneAgent(Agent):
    def __init__(self, id, jid, password, initialPos, capacity = 0, autonomy = 0, velocity = 0, warehouse_positions = {}):
        super().__init__(jid, password)
        self.id = id
        self.max_capacity : float = capacity # in kg
        self.max_autonomy : float = autonomy # in meters
        self.velocity : float = velocity # in m/s
        
        self.curr_capacity : float = 0.0
        self.curr_autonomy : float = autonomy
        self.curr_orders = []
        self.curr_order = None
        self.distance_to_curr_order = 0.0
    
        self.warehouse_positions = warehouse_positions    
        self.curr_warehouse = None
        self.distance_to_curr_warehouse = 0.0
    
        self.position = {
            "latitude": warehouse_positions[initialPos]["latitude"],
            "longitude": warehouse_positions[initialPos]["longitude"]
        } 

    def closest_warehouse(self):
        min_dist = float('inf')
        closest = None
        for warehouse in self.warehouse_positions:
            dist = haversine_distance(
                self.position['latitude'],
                self.position['longitude'],
                self.warehouse_positions[warehouse]['latitude'],
                self.warehouse_positions[warehouse]['longitude']
            )
            if dist < min_dist:
                min_dist = dist
                closest = warehouse
        return closest
    
    def closest_order(self):
        min_dist = float('inf')
        closest = None
        for order in self.curr_orders:
            dist = haversine_distance(
                self.position['latitude'],
                self.position['longitude'],
                order['latitude'],
                order['longitude']
            )
            if dist < min_dist:
                min_dist = dist
                closest = order
        return closest

    async def setup(self):
        print(f"{self.id} - [SETUP]")
        self.add_behaviour(IdleBehav())

    def __str__(self) -> str:
        return "{} - Drone with capacity {} and autonomy {}"\
            .format(str(self.id), self.max_capacity, self.max_capacity, 
                    self.velocity, self.warehouse_positions)
            
# ----------------------------------------------------------------------------------------------
    
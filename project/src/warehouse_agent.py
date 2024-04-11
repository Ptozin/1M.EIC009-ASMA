# ----------------------------------------------------------------------------------------------

from order import DeliveryOrder
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template
import json

# ----------------------------------------------------------------------------------------------

STATE_DISMISSED = 20

# ----------------------------------------------------------------------------------------------

class WarehouseAgent(Agent):
        
    class HandOutBehav(CyclicBehaviour):
        def handle_orders(self, drone_capacity : float) -> str:
            """
            Handle orders to be delivered by the drone.

            Args:
                drone_capacity (float): The drone capacity.

            Returns:
                str: A JSON string containing the orders to be delivered.
            """
            
            orders_to_remove = []
            orders_to_deliver = []
            
            for order_id, order in list(self.agent.inventory.items()):
                if order.weight <= drone_capacity:                    
                    orders_to_remove.append(order_id)
                    orders_to_deliver.append(order.__repr__())
                    drone_capacity -= order.weight
                    if drone_capacity == 0: break
            
            # For now, we will remove all delivered orders instead of checking drone confirmation
            for order_id in orders_to_remove:
                del self.agent.inventory[order_id]
                
            self.agent.inventory_size = len(self.agent.inventory)
            
            return json.dumps(orders_to_deliver)
            
        async def run(self):
            recv_msg = await self.receive(timeout=5)
            if recv_msg is None:
                print("[HANDOUT] Waiting for available drones... - {}".format(str(self.agent)))
            else:
                print(f"{self.agent.id} - [MESSAGE] {recv_msg.body}")
                drone_data = json.loads(recv_msg.body) 

                # Send orders to drone
                msg = Message(to=str(recv_msg.sender)) 
                msg.set_metadata("performative", "inform")
                msg.body = self.handle_orders(drone_data['capacity'])
                                
                await self.send(msg)
                
                print(f"{self.agent.id} - Inventory: ({len(self.agent.inventory)}/{self.agent.initial_inventory_size})")
                
                if len(self.agent.inventory) == 0:
                    self.kill(exit_code=STATE_DISMISSED)
                    
        async def on_end(self):
            if self.exit_code == STATE_DISMISSED:
                self.agent.add_behaviour(self.agent.RefuseOrderBehav())
            else:
                # print(f"{self.agent.id} - [RESTART]")
                # self.agent.add_behaviour(self)
                await self.agent.stop()
                
    class RefuseOrderBehav(CyclicBehaviour):
        async def on_start(self) -> None:
            self.counter = 0
            self.limit = 5
        
        async def run(self):
            self.counter += 1
            recv_msg = await self.receive(timeout=5)
            if recv_msg is None:
                print(f"{self.agent.id} - [REFUSING] - Waiting for available drones...")
                if self.counter == self.limit:
                    self.kill()
            else:
                self.counter = 0 
                print(f"{self.agent.id} - [REFUSING] - [MESSAGE] {recv_msg.body}")
                msg = Message(to=str(recv_msg.sender))
                msg.set_metadata("performative", "refuse")
                await self.send(msg)
        
        async def on_end(self):
            print(f"{self.agent.id} - [DISMISSING] No more orders to deliver & drones to attend to.")
            await self.agent.stop()
    
    def __init__(self, id, jid, password, latitude, longitude, orders) -> None:
        super().__init__(jid, password)
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.position = {
            "latitude": latitude,
            "longitude": longitude
        } 
        self.inventory = {}
        def create_order(order):
            self.inventory[order["id"]] = DeliveryOrder(
                order["id"],
                self.position["latitude"],
                self.position["longitude"],
                order["latitude"],
                order["longitude"],
                order["weight"]
            )
        for order in orders:
            create_order(order)
        
        self.initial_inventory_size = len(self.inventory)
        self.inventory_size = len(self.inventory)

    async def setup(self):
        print(f"{self.id} - [SETUP]")
        b = self.HandOutBehav()
        self.add_behaviour(b)
        
    def __str__ (self) -> str:
        return "Warehouse {} - at ({}, {}) with ({}/{}) orders remaining"\
            .format(self.id, self.latitude, self.longitude, self.inventory_size, self.initial_inventory_size)

# ----------------------------------------------------------------------------------------------

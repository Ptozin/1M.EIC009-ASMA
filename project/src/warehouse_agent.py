from order import DeliveryOrder
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template
import json

class WarehouseAgent(Agent):
    class HandOutBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if msg is None:
                print(f"{self.agent.id} - Waiting for available drones...")
            else:
                print(f"\n{self.agent.id} - [MESSAGE] {msg.body}\n")

                drone_data = json.loads(msg.body) 
                drone = drone_data['id']
                capacity = drone_data['capacity']
                orders = []
                orders_to_remove = [] 

                for order_id, order in list(self.agent.inventory.items()):
                    if order.weight <= capacity:
                        orders.append({
                            "id": order.id,
                            "latitude": order.destination_position["latitude"],
                            "longitude": order.destination_position["longitude"],
                            "weight": order.weight
                        })
                        capacity -= order.weight
                        orders_to_remove.append(order_id) 

                target = drone + '@localhost'
                msg = Message(to=target) 
                msg.set_metadata("performative", "inform")
                msg.body = json.dumps(orders)       
                await self.send(msg)

                # later check drone confirmation before removing orders
                for order_id in orders_to_remove:
                    del self.agent.inventory[order_id]
                    
        async def on_end(self):
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

    async def setup(self):
        print(f"{self.id} - [SETUP]")
        b = self.HandOutBehav()
        self.add_behaviour(b)

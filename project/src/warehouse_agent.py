from order import DeliveryOrder
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template
import json

class HandOutBehav(CyclicBehaviour):
    async def run(self):
        # wait for available drone
        print(f"{self.agent.id} - [BEHAVIOUR] HandOutBehav - Waiting for drone")
        msg = await self.receive(timeout=5)
        if msg is None:
            print(f"{self.agent.id} - No message received")
        else:
            print(f"{self.agent.id} - [MESSAGE] {msg.body}")
            drone_data = json.loads(msg.body) 
            drone = drone_data['id']
            capacity = drone_data['capacity']
            orders = []
            orders_to_remove = [] 

            for order_id, order in list(self.agent.inventory.items()):
                if order.weight <= capacity:
                    orders.append(str(order))
                    capacity -= order.weight
                    orders_to_remove.append(order_id) 

            target = drone + '@localhost'
            msg = Message(to=target) 
            msg.set_metadata("performative", "inform")
            msg.body = '|'.join(orders)  
            print(msg.body)             
            await self.send(msg)

            # later check drone confirmation before removing orders
            for order_id in orders_to_remove:
                del self.agent.inventory[order_id]

        self.kill(exit_code=10)
    
    async def on_end(self) -> None:
        print(f"{self.agent.id} - Goodbye")

class WarehouseAgent(Agent):
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
        print(f"[SETUP] {self.id}")
        b = HandOutBehav()
        #template = Template()
        #template.set_metadata("performative", "inform")
        self.add_behaviour(b)#, template)

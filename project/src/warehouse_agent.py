from order import DeliveryOrder
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message

class InformBehav(OneShotBehaviour):
    async def run(self):
        msg = await self.receive(timeout=5)
        print(f"[MESSAGE] {msg.body}")
        # TODO: parse message
        await self.agent.stop()

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
        b = InformBehav()
        self.add_behaviour(b)

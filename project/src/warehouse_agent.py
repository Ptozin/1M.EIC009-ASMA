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
    def __init__(self, jid, latitude, longitude, orders):
        self.password = 'admin' # TODO: receive main unique password
        super().__init__(jid, self.password)
        self.latitude = latitude
        self.longitude = longitude
        self.inventory = {}
        def create_order(order):
            self.inventory[order["id"]] = DeliveryOrder(
                order["id"],
                self.latitude,
                self.longitude,
                order["latitude"],
                order["longitude"],
                order["weight"]
            )
        for order in orders:
            create_order(order)

    async def setup(self):
        print(f"[SETUP] {self.jid}")
        b = InformBehav()
        self.add_behaviour(b)

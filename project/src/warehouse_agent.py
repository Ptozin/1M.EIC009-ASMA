from order import DeliveryOrder
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message

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

    class InformBehav(OneShotBehaviour):
        async def run(self):
            print("InformBehav running")
            drone = "drone1"
            target = drone + "@localhost"
            msg = Message(to=target)  
            msg.set_metadata("performative", "inform")  
            msg.body = f"Hello {drone}, I'm Warehouse {self.agent.jid} and I have the following proposal:\nGang"            

            await self.send(msg)
            print("Message sent!")

            await self.agent.stop()

    async def setup(self):
        print("[WAREHOUSE] Hello, I'm agent {}".format(str(self.jid)))
        b = self.InformBehav()
        self.add_behaviour(b)

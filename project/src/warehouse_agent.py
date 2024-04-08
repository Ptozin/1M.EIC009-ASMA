from spade.agent import Agent
from order import DeliveryOrder

class WarehouseAgent(Agent):
    def __init__(self, jid, latitude, longitude, orders):
        self.password = 'admin' # TO-DO: receive main unique password
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
        print("[WAREHOUSE] Hello, I'm agent {}".format(str(self.jid)))
        print("Latitude:", self.latitude)
        print("Longitude:", self.longitude)

# ----------------------------------------------------------------------------------------------

from spade.agent import Agent

from src.order import DeliveryOrder
from misc.log import Logger
from behaviours.idle import IdleBehaviour
from behaviours.visualization import EmitSetupBehav
from flask_socketio import SocketIO
            
# ----------------------------------------------------------------------------------------------

class WarehouseAgent(Agent):
    def __init__(self, id, jid, password, latitude, longitude, orders, socketio : SocketIO) -> None:
        super().__init__(jid, password)
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.position = {
            "latitude": latitude,
            "longitude": longitude
        } 
        self.inventory : dict[DeliveryOrder]= {}
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
        
        self.curr_drone = None

        self.logger = Logger(filename=id)
        self.socketio = socketio

    async def setup(self):
        self.logger.log(f"{self.id} - [SETUP]")
        self.add_behaviour(EmitSetupBehav())
        self.add_behaviour(IdleBehaviour())

# ----------------------------------------------------------------------------------------------
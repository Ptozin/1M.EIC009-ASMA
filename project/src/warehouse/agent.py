# ----------------------------------------------------------------------------------------------

from spade.agent import Agent
from flask_socketio import SocketIO

from order import DeliveryOrder
from misc.log import Logger
from warehouse.behaviours import EmitSetupBehaviour
from warehouse.utils import OrdersMatrix
            
# ----------------------------------------------------------------------------------------------

class WarehouseAgent(Agent):
    def __init__(self, id : str, jid : str, password : str, latitude : float, longitude : float, orders : dict , socketio : SocketIO) -> None:
        super().__init__(jid, password)
        self.id : str = id
        self.latitude : float = latitude
        self.longitude : str = longitude
        self.position : dict = {
            "latitude": latitude,
            "longitude": longitude
        } 
        self.inventory : dict[DeliveryOrder]= {}
        self.orders_to_be_picked : list[str] = []

        for order in orders:
            self.inventory[order["id"]] = DeliveryOrder(
                order["id"],
                self.position["latitude"],
                self.position["longitude"],
                order["latitude"],
                order["longitude"],
                order["weight"]
            )
        
        self.curr_drone : str | None = None

        self.logger = Logger(filename=id)
        self.socketio = socketio
        
        self.orders_matrix : OrdersMatrix = None

    async def setup(self) -> None:
        self.logger.log(f"{self.id} - [SETUP]")
        self.add_behaviour(EmitSetupBehaviour())

# ----------------------------------------------------------------------------------------------
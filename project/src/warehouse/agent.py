# ----------------------------------------------------------------------------------------------

from spade.agent import Agent

from order import DeliveryOrder
from misc.log import Logger
from warehouse.behaviours import IdleBehaviour, EmitSetupBehav
from flask_socketio import SocketIO
            
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
        
        self.curr_drone : str | None = None

        self.logger = Logger(filename=id)
        self.socketio = socketio

    async def setup(self) -> None:
        self.logger.log(f"{self.id} - [SETUP]")
        self.add_behaviour(EmitSetupBehav())
        self.add_behaviour(IdleBehaviour())

# ----------------------------------------------------------------------------------------------
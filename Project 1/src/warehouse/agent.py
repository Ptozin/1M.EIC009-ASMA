# ----------------------------------------------------------------------------------------------

from spade.agent import Agent
from flask_socketio import SocketIO

from order import DeliveryOrder
from misc.log import Logger
from warehouse.behaviours import EmitSetupBehaviour, IdleBehaviour
from warehouse.utils import OrdersMatrix
            
# ----------------------------------------------------------------------------------------------

class WarehouseAgent(Agent):
    def __init__(self, id : str, jid : str, password : str, latitude : float, longitude : float, orders : dict , socketio : SocketIO) -> None:
        super().__init__(jid, password)
        self.id : str = id
        self.latitude : float = latitude
        self.longitude : float = longitude
        self.position : dict = {
            "latitude": latitude,
            "longitude": longitude
        } 
        self.inventory : dict[DeliveryOrder]= {}

        for order in orders:
            self.inventory[order["id"]] = DeliveryOrder(
                order["id"],
                self.position["latitude"],
                self.position["longitude"],
                order["latitude"],
                order["longitude"],
                order["weight"]
            )
        
        # See if we can get rid of this
        self.orders_to_be_picked : dict[str, list[DeliveryOrder]] = {}

        self.logger = Logger(filename=id)
        self.socketio = socketio
        self.orders_matrix : OrdersMatrix = OrdersMatrix(
                self.inventory, 
                divisions=5, 
                capacity_multiplier=3,
                warehouse_position=self.position
            )

    async def setup(self) -> None:
        self.logger.log(f"{self.id} - [SETUP]")
        self.add_behaviour(IdleBehaviour())
        self.add_behaviour(EmitSetupBehaviour())
        
# ----------------------------------------------------------------------------------------------
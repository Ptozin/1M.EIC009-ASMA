# ----------------------------------------------------------------------------------------------

from spade.behaviour import OneShotBehaviour
from spade.message import Message

from ..agent import WarehouseAgent
from utils import select_orders
from drone_orders import DroneOrdersBehaviour

# ----------------------------------------------------------------------------------------------

class HandOutBehaviour(OneShotBehaviour):
    async def on_start(self):
        self.agent : WarehouseAgent = self.agent
    
    async def run(self):
        message = Message()
        message.to = self.agent.curr_drone["id"] + "@localhost"
        message.body = select_orders(self.agent.inventory)
        message.set_metadata("performative", "inform")
        await self.send(message)
        
    async def on_end(self):
        self.agent.add_behaviour(DroneOrdersBehaviour())
        
# ----------------------------------------------------------------------------------------------
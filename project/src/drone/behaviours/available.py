# ----------------------------------------------------------------------------------------------

from spade.behaviour import OneShotBehaviour
from spade.message import Message

from ..agent import DroneAgent
from receive_orders import ReceiveOrdersBehaviour

# ----------------------------------------------------------------------------------------------

class AvailableBehaviour(OneShotBehaviour):
    async def on_start(self):
        self.agent : DroneAgent = self.agent
    
    async def run(self):
        for warehouse in self.agent.warehouse_positions.keys():
            message = Message()
            message.to = warehouse + "@localhost"
            message.body = self.agent.__repr__()
            message.set_metadata("performative", "inform")
            await self.send(message)
            
    async def on_end(self):
        self.agent.add_behaviour(ReceiveOrdersBehaviour())
            
# ----------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------

import json
from spade.behaviour import OneShotBehaviour

from ..agent import WarehouseAgent
from idle import IdleBehaviour

# ----------------------------------------------------------------------------------------------

class DroneOrdersBehaviour(OneShotBehaviour):
    async def on_start(self):
        self.agent : WarehouseAgent = self.agent
    
    async def run(self):
        message = await self.receive(timeout=5)
        if message is None:
            pass # TODO: deal with timeout (drone did not respond with orders chosen)
        else:
            drone_data = json.loads(message.body)
            for order in drone_data["orders"]:
                pass # TODO: update order status (delivering)
            
    async def on_end(self):
        # TODO: check if there are more orders to deliver - if not, call dismiss behaviour
        self.agent.add_behaviour(IdleBehaviour())

# ----------------------------------------------------------------------------------------------
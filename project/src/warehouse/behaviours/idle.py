# ----------------------------------------------------------------------------------------------

import json
from spade.behaviour import CyclicBehaviour

from ..agent import WarehouseAgent
from hand_out import HandOutBehaviour

# ----------------------------------------------------------------------------------------------
        
class IdleBehaviour(CyclicBehaviour):
    async def on_start(self):
        self.agent : WarehouseAgent = self.agent
    
    async def run(self):
        message = await self.receive(timeout=5)
        if message is None:
            self.agent.logger.log("[HANDOUT] Waiting for available drones... - {}".format(str(self.agent)))
        else:
            self.agent.curr_drone = json.loads(message.body)
            self.kill()
            
    async def on_end(self):
        self.agent.add_behaviour(HandOutBehaviour())
        
# ----------------------------------------------------------------------------------------------
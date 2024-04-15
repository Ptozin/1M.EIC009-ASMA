# ----------------------------------------------------------------------------------------------

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from ..agent import WarehouseAgent

# ----------------------------------------------------------------------------------------------

class DismissBehaviour(CyclicBehaviour):
    async def on_start(self):
        self.agent : WarehouseAgent = self.agent
        self.counter = 0
        self.limit = 3
    
    async def run(self):
        self.counter += 1
        message = await self.receive(timeout=5)
        if message is None:
            self.agent.logger.log(f"{self.agent.id} - [REFUSING] - Waiting for available drones... try {self.counter}/{self.limit}")
            if self.counter >= self.limit:
                self.kill()
        else:
            self.counter = 0 
            self.agent.logger.log(f"{self.agent.id} - [REFUSING] - [MESSAGE] {message.body}")
            msg = Message(to=str(message.sender))
            msg.set_metadata("performative", "refuse")
            await self.send(msg)
    
    async def on_end(self):
        self.agent.logger.log(f"{self.agent.id} - [DISMISSING] No more orders to deliver & drones to attend to.")
        await self.agent.stop()
            
# ----------------------------------------------------------------------------------------------
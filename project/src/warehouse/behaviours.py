# ----------------------------------------------------------------------------------------------

import json
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from warehouse.utils import *

# ----------------------------------------------------------------------------------------------

class DismissBehaviour(CyclicBehaviour):
    async def on_start(self):
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
            message = Message(to=str(message.sender))
            message.set_metadata("performative", "refuse")
            await self.send(message)
    
    async def on_end(self):
        self.agent.logger.log(f"{self.agent.id} - [DISMISSING] No more orders to deliver & drones to attend to.")
        await self.agent.stop()
            
# ----------------------------------------------------------------------------------------------

class DroneOrdersBehaviour(OneShotBehaviour):
    async def run(self):
        message = await self.receive(timeout=5)
        if message is None:
            pass # TODO: deal with timeout (drone did not respond with orders chosen)
        else:
            if message.metadata["performative"] == "refuse":
                self.kill()
            elif message.metadata["performative"] == "agree":
                drone_data = json.loads(message.body)
                for order in drone_data["orders"]:
                    continue # TODO: update order status (delivering)
            
    async def on_end(self):
        # TODO: check if there are more orders to deliver - if not, call dismiss behaviour
        self.agent.add_behaviour(IdleBehaviour())

# ----------------------------------------------------------------------------------------------

class HandOutBehaviour(OneShotBehaviour):
    async def run(self):
        message = Message()
        message.to = self.agent.curr_drone["id"] + "@localhost"
        message.body = select_orders(self.agent.inventory)
        message.set_metadata("performative", "inform")
        await self.send(message)
        
    async def on_end(self):
        self.agent.add_behaviour(DroneOrdersBehaviour())
        
# ----------------------------------------------------------------------------------------------

class IdleBehaviour(CyclicBehaviour):
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

class EmitSetupBehav(OneShotBehaviour):
    async def run(self):
        data = [order.get_order_for_visualization() for order in self.agent.inventory.values()]
        data.append({
            'id': self.agent.id,
            'latitude': self.agent.position['latitude'],
            'longitude': self.agent.position['longitude'],
            'type': 'warehouse'
        })
        self.agent.socketio.emit(
            'update_data', 
            data
        )
            
# ----------------------------------------------------------------------------------------------
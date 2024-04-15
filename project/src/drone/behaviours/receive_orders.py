# ----------------------------------------------------------------------------------------------

import json
from spade.behaviour import CyclicBehaviour

from ..agent import DroneAgent
from src.order import DeliveryOrder
from decide_orders import DecideOrdersBehaviour

# ----------------------------------------------------------------------------------------------

DECIDING = 10
DISMISSED = 20

# ----------------------------------------------------------------------------------------------

class ReceiveOrdersBehaviour(CyclicBehaviour):
    async def on_start(self):
        self.agent : DroneAgent = self.agent
        self.counter = 0
        self.limit = 3
        self.agent.final_order_choices = {}
    
    async def run(self):
        if len(self.final_order_choices) == len(self.agent.warehouse_positions):
            self.kill(exit_code=DECIDING)
        
        message = await self.receive(timeout=5)
        if message is None:
            self.agent.logger.log(f"{self.agent.params.id} - [WAITING] - Waiting for available orders... try {self.counter}/{self.limit}")
            self.counter += 1
            if self.counter >= self.limit:
                self.kill()
        else:
            if message.metadata["performative"] == "inform":
                proposed_orders = json.loads(message.body)
                orders = []
                for order in proposed_orders:
                    order = json.loads(order)
                    orders.append(DeliveryOrder(**order))
                    
                order_choices = self.agent.best_order_set(orders)
                self.agent.final_order_choices[message.sender.split("@")[0]] = order_choices
                
            elif message.metadata["performative"] == "refuse":
                self.agent.logger.log(f"[REFUSED] {self.agent.params.id} - {message.sender}")
                self.agent.remove_warehouse(message.sender.split("@")[0])
                
                if not self.agent.available_warehouses():
                    self.kill(exit_code=DISMISSED)
            
    async def on_end(self):
        self.agent.add_behaviour(DecideOrdersBehaviour())
            
# ----------------------------------------------------------------------------------------------
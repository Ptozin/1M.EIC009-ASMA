# ----------------------------------------------------------------------------------------------

import json
from spade.behaviour import CyclicBehaviour

from ..agent import DroneAgent
from src.order import DeliveryOrder
from decide_orders import DecideOrdersBehaviour
from utils import best_available_orders

# ----------------------------------------------------------------------------------------------

DECIDING = 10
DISMISSED = 20

# ----------------------------------------------------------------------------------------------

class ReceiveOrdersBehaviour(CyclicBehaviour):
    async def on_start(self):
        self.agent : DroneAgent = self.agent
        self.counter = 0
        self.limit = 3
        self.agent.available_order_sets = {}
    
    async def run(self):
        if len(self.agent.available_order_sets) == len(self.agent.warehouse_positions):
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
                    
                order_choices = best_available_orders(orders, self.agent.params.curr_capacity)
                self.agent.available_order_sets[message.sender.split("@")[0]] = order_choices
                
            elif message.metadata["performative"] == "refuse":
                self.agent.logger.log(f"[REFUSED] {self.agent.params.id} - {message.sender}")
                self.agent.remove_warehouse(message.sender.split("@")[0])
                
                if not self.agent.available_warehouses():
                    self.kill(exit_code=DISMISSED)
            
    async def on_end(self):
        if self.exit_code == DECIDING:
            self.agent.add_behaviour(DecideOrdersBehaviour())
        elif self.exit_code == DISMISSED:
            self.agent.logger.log(self.agent.params.metrics())
            self.agent.params.store_results()
            await self.agent.stop()
            
# ----------------------------------------------------------------------------------------------
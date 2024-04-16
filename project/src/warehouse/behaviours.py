# ----------------------------------------------------------------------------------------------

import json
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from warehouse.utils import *

# ----------------------------------------------------------------------------------------------

class DismissBehaviour(CyclicBehaviour):    
    async def run(self):
        # It will be self-terminated when all drones finish their tasks
        
        message = await self.receive(timeout=5)
        if message is None:
            self.agent.logger.log(f"{self.agent.id} - [REFUSING] - Waiting for drones to refuse...")
        else:
            self.agent.logger.log(f"{self.agent.id} - [REFUSING] - [MESSAGE] {str(message.sender)}")
            message = Message(to=str(message.sender))
            message.set_metadata("performative", "refuse")
            await self.send(message)
    
    async def on_end(self):
        self.agent.logger.log(f"{self.agent.id} - [DISMISSING] No more orders to deliver & drones to attend to.")
        await self.agent.stop()
          
# ----------------------------------------------------------------------------------------------

class HandleOrderPickupBehav(CyclicBehaviour):
    async def run(self):
        # TODO: DO NOT AWAIT FOR MESSAGES, USE IDLE BEHAVIOUR AND PROCESS MESSAGE HERE
        message = await self.receive(timeout=5)
        if message is None:
            self.agent.logger.log("[PICKUP] Waiting for drones to pickup {} order(s)... - {}"\
                .format(str(len(self.orders_to_be_picked)),str(self.agent)))
        else:
            orders = json.loads(message.body)
            for order in orders:
                # Assuming that there is never a race condition
                self.orders_to_be_picked.remove(order["id"])
                
            self.agent.logger.log("[PICKUP] {} Orders picked up by drone - {}"\
                .format(str(len(orders)),str(self.agent)))
            
            answer = Message()
            answer.to = str(message.sender)
            answer.metadata = {"performative": "accept"}
            
            await self.send(answer)
            

# ----------------------------------------------------------------------------------------------

class HandleSuggestionsBehav(OneShotBehaviour):
    async def run(self):
        message = await self.receive(timeout=5)
        if message is None:
            # Go back to idle behaviour
            self.kill()
        else:
            if message.metadata["performative"] == "refuse":
                self.kill()
            elif message.metadata["performative"] == "agree":
                drone_data = json.loads(message.body)
                
                orders_id = []
                for order in drone_data["orders"]:
                    self.agent.inventory[order["id"]].update_order_status()
                    self.orders_to_be_picked.append(order["id"])
                    orders_id.append(order["id"])
                self.agent.matrix.remove_order(orders_id = orders_id)
            
            
    async def on_end(self):
        # Dismiss if there are no more orders available
        orders_left = sum([1 for order in self.agent.inventory.values() if order.order_status == False])
        if orders_left == 0:
            self.agent.add_behaviour(DismissBehaviour())
        else:
            self.agent.add_behaviour(IdleBehaviour())

# ----------------------------------------------------------------------------------------------

class SuggestOrdersBehav(OneShotBehaviour):
    async def run(self):
        message = Message()
        message.to = self.agent.curr_drone["id"] + "@localhost"
        message.body = self.agent.orders_matrix.select_orders(self.agent.position['latitude'],
                                                              self.agent.position['longitude'], 
                                                              self.agent.curr_drone["capacity"])
        message.set_metadata("performative", "inform")
        await self.send(message)
        
    async def on_end(self):
        self.agent.add_behaviour(HandleSuggestionsBehav())
        
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
        self.agent.add_behaviour(SuggestOrdersBehav())
        
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

class SetupOrdersMatrixBehav(OneShotBehaviour):
    async def run(self):
        self.agent.orders_matrix = OrdersMatrix(self.agent.inventory, divisions=5, capacity_multiplier=3)

# ----------------------------------------------------------------------------------------------
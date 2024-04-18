# ----------------------------------------------------------------------------------------------

import json
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from warehouse.utils import *

# ----------------------------------------------------------------------------------------------

SUGGEST_ORDER = "suggest"
ORDER_PICKUP = "pickup_orders"
RECHARGE_DRONE = "recharge"
DISMISS = 30
HANDLE_SUGGESTION = 40
ERROR = 60

METADATA_NEXT_BEHAVIOUR = "next_behaviour"

# ----------------------------------------------------------------------------------------------

class SetupOrdersMatrixBehaviour(OneShotBehaviour):
    async def run(self):
        self.agent.orders_matrix = OrdersMatrix(
                self.agent.inventory, 
                divisions=5, 
                capacity_multiplier=3,
                warehouse_position=self.agent.position
            )

class EmitSetupBehaviour(OneShotBehaviour):
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
    
    async def on_end(self):
        self.agent.add_behaviour(SetupOrdersMatrixBehaviour())

# ----------------------------------------------------------------------------------------------

class IdleBehaviour(CyclicBehaviour):
    async def run(self):
        self.message = None
        message = await self.receive(timeout=5)
        if message is None:
            self.agent.logger.log("[IDLE] Waiting for available drones... - {}".format(str(self.agent)))
        else:
            self.message = message
            self.agent.logger.log("[IDLE] - [MESSAGE] - {} - from {} with metadata :{}".format(str(self.agent), str(message.sender), str(message.metadata)))
            self.kill(exit_code=message.metadata["next_behaviour"])
            
    async def on_end(self):
        if self.exit_code == SUGGEST_ORDER:
            self.agent.logger.log("[IDLE] - [SUGGEST] - Suggesting orders to drone - {}".format(str(self.agent)))
            self.agent.add_behaviour(SuggestOrdersBehaviour(self.message))
        elif self.exit_code == ORDER_PICKUP:
            self.agent.logger.log("[IDLE] - [PICKUP] - Picking up orders - {}".format(str(self.agent)))
            self.agent.add_behaviour(OrdersPickupBehaviour(self.message))
        elif self.exit_code == RECHARGE_DRONE:
            self.agent.logger.log("[IDLE] - [RECHARGE] - Recharging drone - {}".format(str(self.agent)))
            self.agent.add_behaviour(RechargeDroneBehaviour(self.message))
        else:
            self.agent.logger.log("[IDLE] - [ERROR] - Invalid exit code. {}".format(str(self.agent)))
            self.agent.add_behaviour(IdleBehaviour())
        
# ----------------------------------------------------------------------------------------------

class SuggestOrdersBehaviour(OneShotBehaviour):
    def __init__(self, message : Message):
        super().__init__()
        self.sender = str(message.sender)
        self.drone_capacity = json.loads(message.body)["capacity"]
        
    async def run(self):
        message = Message()
        message.to = self.sender

        orders : list[DeliveryOrder] = self.agent.orders_matrix.select_orders(self.agent.position['latitude'],
                                                              self.agent.position['longitude'], 
                                                              self.drone_capacity)
        
        message.body = json.dumps([order.__repr__() for order in orders])
        
        message.set_metadata("performative", "propose")
        
        self.agent.logger.log("[SUGGEST] - {} orders suggested to drone - {}".format(str(len(orders)), str(self.agent)))

        await self.send(message)
        self.response = await self.receive(timeout=5)
                
        self.kill(exit_code=HANDLE_SUGGESTION)
        
    async def on_end(self):
        self.agent.add_behaviour(HandleSuggestionsBehaviour(self.response))
        
# ----------------------------------------------------------------------------------------------

class HandleSuggestionsBehaviour(OneShotBehaviour):
    def __init__(self, message : Message):
        super().__init__()
        self.message = message
    
    async def run(self):
        if self.message is None:
            self.agent.logger.log("[HANDLE] - [ERROR] - No message received. {}".format(str(self.agent)))
            self.kill()
        else:
            self.agent.logger.log("[HANDLE] - [RESPONSE] - {} - from {} with metadata :{}".format(str(self.agent.id), str(self.message.sender), str(self.message.metadata)))
            if self.message.metadata["performative"] == "refuse-proposal":
                self.kill()
            elif self.message.metadata["performative"] == "agree-proposal":
                orders = json.loads(self.message.body)
                
                # This has to be verified if the drone is asking for orders only given to him
                orders_id = []
                for order_str in orders:
                    order = json.loads(order_str)
                    self.agent.inventory[order["id"]].mark_as_taken()
                    self.agent.orders_to_be_picked.append(order["id"])
                    orders_id.append(order["id"])
                
                # These will not be available for other drones
                self.agent.orders_matrix.remove_orders(orders_id = orders_id)
            
    async def on_end(self):
        orders_left = sum([1 for order in self.agent.inventory.values() if order.order_status == False])
        if orders_left == 0:
            self.agent.add_behaviour(DismissBehaviour())
        else:
            self.agent.add_behaviour(IdleBehaviour())

# ----------------------------------------------------------------------------------------------

class DismissBehaviour(CyclicBehaviour):    
    async def run(self):
        message = await self.receive(timeout=5)
        if message is None:
            self.agent.logger.log(f"{self.agent.id} - [REFUSING] - Waiting for drones to refuse...")
        else:
            self.agent.logger.log(f"{self.agent.id} - [REFUSING] - [MESSAGE] {str(message.sender)}")
            message = Message(to=str(message.sender))
            message.set_metadata("performative", "refuse-proposal")
            await self.send(message)
    
    async def on_end(self):
        self.agent.logger.log(f"{self.agent.id} - [DISMISSING] No more orders to deliver & drones to attend to.")
        
# ----------------------------------------------------------------------------------------------

class OrdersPickupBehaviour(OneShotBehaviour):
    def __init__(self, message : Message):
        super().__init__()
        self.message : Message = message
        self.sender = str(message.sender)
    
    async def run(self):
        if self.message is None:
            self.kill(exit_code=ERROR)
            return
        
        orders = json.loads(self.message.body)
        
        for order in orders:
            # assuming that there is never a race condition
            if order['id'] not in self.orders_to_be_picked:
                self.kill(exit_code=ERROR)
                return
            self.orders_to_be_picked.remove(order["id"])
        
        self.agent.logger.log("[PICKUP] {} orders picked up by drone - {}"\
            .format(str(len(orders)),str(self.agent)))
        
        answer = Message()
        answer.to = self.sender
        answer.metadata = {"performative": "agree-proposal"}
        await self.send(answer)
        
    async def on_end(self):
        if self.exit_code == ERROR:
            self.agent.logger.log("[PICKUP] - [ERROR] - No message received. {}".format(str(self.agent)))
        self.agent.add_behaviour(IdleBehaviour())
        
# ----------------------------------------------------------------------------------------------

class RechargeDroneBehaviour(OneShotBehaviour):
    def __init__(self, message : Message):
        super().__init__()
        self.message : Message = message
        self.sender = str(message.sender)
        
    async def run(self):
        if self.message is None:
            self.kill(exit_code=ERROR)
            return
        
        answer = Message()
        answer.to = self.sender
        if self.message.metadata["performative"] == "request":
            self.agent.logger.log("[RECHARGE] Drone {} is requesting recharge... - {}".format(self.message.sender, str(self.agent)))
            answer.metadata = {"performative": "agree-proposal"}
        else:
            answer.metadata = {"performative": "refuse-proposal"}
            
        await self.send(answer)
    
    async def on_end(self):
        if self.exit_code == ERROR:
            self.agent.logger.log("[RECHARGE] - [ERROR] - No message received. {}".format(str(self.agent)))
        self.agent.add_behaviour(IdleBehaviour())
        
# ----------------------------------------------------------------------------------------------
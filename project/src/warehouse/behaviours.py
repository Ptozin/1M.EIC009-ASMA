
import json
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from order import DeliveryOrder
from spade.message import Message

# ----------------------------------------------------------------------------------------------

METADATA_NEXT_BEHAVIOUR = "next_behaviour"
SUGGEST= "suggest"
DECIDE = "decide"
PICKUP = "pickup_orders"

# ----------------------------------------------------------------------------------------------

def get_next_behav(message : Message) :
    if message.metadata[METADATA_NEXT_BEHAVIOUR] == SUGGEST:
        capacity = json.loads(message.body)["capacity"]
        return SuggestOrderBehaviour(sender=str(message.sender), drone_capacity=capacity)
    elif message.metadata[METADATA_NEXT_BEHAVIOUR] == DECIDE:
        return DecideOrdersBehaviour(sender=str(message.sender), message=message)
    elif message.metadata[METADATA_NEXT_BEHAVIOUR] == PICKUP:
        return PickupOrdersBehaviour(sender=str(message.sender), message=message)
    else:
        # In case of error
        return None

# ----------------------------------------------------------------------------------------------

class IdleBehaviour(CyclicBehaviour):
    
    async def run(self):
        if len(self.agent.inventory) == 0 and self.agent.orders_to_be_picked == {}:
            self.agent.logger.log("[IDLE] - No orders to be picked")
            self.kill()
            return
        
        message = await self.receive(timeout=5)
        if message is None:
            self.agent.logger.log("[IDLE] Waiting for available drones...")
        else:
            self.agent.logger.log("[IDLE] - [MESSAGE] - from {} with metadata :{}".format( str(message.sender), str(message.metadata)))
            
            b = get_next_behav(message)
            if b is not None:
                self.agent.add_behaviour(b)
            else:
                self.agent.logger.log("[IDLE] - [ERROR] - Next behaviour is None")
                self.kill()
                return
            
            
    async def on_end(self):
        self.agent.add_behaviour(DismissBehaviour()) 

# ----------------------------------------------------------------------------------------------

class SuggestOrderBehaviour(OneShotBehaviour):
    def __init__(self, sender : str, drone_capacity : int):
        super().__init__()
        self.sender : str = sender
        self.drone_capacity = drone_capacity
        
    async def run(self):
        orders : list[DeliveryOrder] = self.agent.orders_matrix.select_orders(self.agent.position['latitude'],
                                                              self.agent.position['longitude'], 
                                                              self.drone_capacity,
                                                              self.sender)
        message : Message = Message()
        message.to = self.sender
        message.set_metadata("performative", "propose")
        message.body = json.dumps([order.__repr__() for order in orders])
                
        await self.send(message)

# ----------------------------------------------------------------------------------------------

class DecideOrdersBehaviour(OneShotBehaviour):
    def __init__(self, sender : str, message : Message):
        super().__init__()
        self.sender : str = sender
        self.message : Message = message
    
    async def run(self):
        if self.message.metadata["performative"] == "accept-proposal":
            self.agent.logger.log(f"[DECIDING] - [ACCEPTED] - {self.sender}")
            
            if self.sender not in self.agent.orders_to_be_picked:
                self.agent.orders_to_be_picked[self.sender] = []
            # Reserve orders to drone
            orders = json.loads(self.message.body)
            # print("Inventory size Before: {}".format(len(self.agent.inventory)))
            for order_str in orders:
                order = json.loads(order_str)
                
                # Remove order from matrix
                self.agent.orders_matrix.remove_order(order["id"], self.sender)
                                
                self.agent.orders_to_be_picked[self.sender].append(self.agent.inventory[order["id"]])
                del self.agent.inventory[order["id"]]
                
            # Undo reservations for orders the drone refused, if any
            self.agent.orders_matrix.undo_reservations(self.sender)
            
            # print("Inventory size After: {}".format(len(self.agent.inventory)))


        elif self.message.metadata["performative"] == "reject-proposal":
            self.agent.logger.log(f"[DECIDING] - [REJECTED] - {self.sender}")
            
            self.agent.orders_matrix.undo_reservations(self.sender)
        
# ----------------------------------------------------------------------------------------------
  
class PickupOrdersBehaviour(OneShotBehaviour):
    def __init__(self, sender : str, message : Message):
        super().__init__()
        self.sender : str = sender
        self.message : Message = message
        
    async def run(self):
        orders = self.agent.orders_to_be_picked[self.sender]
        for order in orders:
            self.agent.logger.log(f"[PICKUP] - {order}")
        
        del self.agent.orders_to_be_picked[self.sender]
        
        message = Message(to=self.sender)
        message.set_metadata("performative", "confirm")

        await self.send(message)
          
# ----------------------------------------------------------------------------------------------

class DismissBehaviour(CyclicBehaviour):    
    async def run(self):
        message = await self.receive(timeout=5)
        if message is None:
            self.agent.logger.log(f"[REFUSING] - Waiting for drones to refuse...")
        else:
            self.agent.logger.log(f"[REFUSING] - [MESSAGE] {str(message.sender)}")
            message = Message(to=str(message.sender))
            message.set_metadata("performative", "refuse")
            await self.send(message)
        
# ----------------------------------------------------------------------------------------------

class EmitSetupBehaviour(OneShotBehaviour):
    async def run(self):
        data = [order.get_order_for_visualization() for order in self.agent.inventory.values()]
        data.append({
            'id': self.agent.id,
            'latitude': self.agent.position['latitude'],
            'longitude': self.agent.position['longitude'],
            'type': 'warehouse'
        })
        self.agent.socketio.emit('update_data', data)

# ----------------------------------------------------------------------------------------------
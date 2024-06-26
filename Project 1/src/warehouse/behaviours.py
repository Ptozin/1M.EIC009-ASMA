
import json
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from order import DeliveryOrder
from spade.message import Message

# ----------------------------------------------------------------------------------------------

METADATA_NEXT_BEHAVIOUR = "next_behaviour"
SUGGEST= "suggest"
DECIDE = "decide"
PICKUP = "pickup_orders"

TIMEOUT = 5.0


# ----------------------------------------------------------------------------------------------

class IdleBehaviour(CyclicBehaviour):
    
    def get_next_behav(self, message : Message) :
        if len(self.agent.inventory.keys()) == 0 and len(self.agent.orders_to_be_picked.keys()) == 0:
            self.agent.logger.log(f"[IDLE] - No orders to be picked - {str(message.sender)}")            
            return DismissBehaviour(message=message)
        
        elif message.metadata[METADATA_NEXT_BEHAVIOUR] == SUGGEST:
            capacity = json.loads(message.body)["capacity"]
            return SuggestOrderBehaviour(sender=str(message.sender), drone_capacity=capacity)
        elif message.metadata[METADATA_NEXT_BEHAVIOUR] == DECIDE:
            return DecideOrdersBehaviour(sender=str(message.sender), message=message)
        elif message.metadata[METADATA_NEXT_BEHAVIOUR] == PICKUP:
            return PickupOrdersBehaviour(sender=str(message.sender), message=message)
        else:
            # In case of error
            return None
    
    async def run(self):
        message = await self.receive(timeout=TIMEOUT)
        if message is None:
            self.agent.logger.log("[IDLE] Waiting for available drones... Didn't receive any message.")
        else:
            self.agent.logger.log("[IDLE] - [MESSAGE] - from {} with metadata :{}".format( str(message.sender), str(message.metadata)))
            
            b = self.get_next_behav(message)
            if b is not None:
                self.agent.add_behaviour(b)
                await b.join()
            else:
                self.agent.logger.log("[IDLE] - [ERROR] - Next behaviour is None. Ignoring message...")
                

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
                                                              self.sender,
                                                              self.agent.logger)
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

            for order_str in orders:
                order = json.loads(order_str)
                
                # Remove order from matrix
                self.agent.orders_matrix.remove_order(order["id"], self.sender)
                                
                self.agent.orders_to_be_picked[self.sender].append(self.agent.inventory[order["id"]])
                del self.agent.inventory[order["id"]]
                
            # Undo reservations for orders the drone refused, if any
            self.agent.orders_matrix.undo_reservations(self.sender, self.agent.logger)
            self.agent.logger.log(f"[DECIDING] - Orders remaining in inventory: {len(self.agent.inventory)}")

        elif self.message.metadata["performative"] == "reject-proposal":
            self.agent.logger.log(f"[DECIDING] - [REJECTED] - {self.sender}")
            
            self.agent.orders_matrix.undo_reservations(self.sender, self.agent.logger)
        
# ----------------------------------------------------------------------------------------------
  
class PickupOrdersBehaviour(OneShotBehaviour):
    def __init__(self, sender : str, message : Message):
        super().__init__()
        self.sender : str = sender
        self.message : Message = message
        # print("RECEIVE", self.sender, message.body)
        
    async def run(self):
        orders = self.agent.orders_to_be_picked[self.sender]
        for order in orders:
            self.agent.logger.log(f"[PICKUP] - {order} - from {self.sender}")
        
        del self.agent.orders_to_be_picked[self.sender]
        
        
        message : Message = Message(to=self.sender)
        message.set_metadata("performative", "confirm")

        await self.send(message)
          
# ----------------------------------------------------------------------------------------------

class DismissBehaviour(OneShotBehaviour):  
    def __init__(self, message : Message):
        super().__init__()
        self.message : Message = message
        
      
    async def run(self):
        if self.message is None:
            self.agent.logger.log(f"[REFUSING] - Waiting for drones to refuse...")
        else:
            self.agent.logger.log(f"[REFUSING] - [MESSAGE] {str(self.message.sender)}")
            message = Message(to=str(self.message.sender))
            message.set_metadata("performative", "refuse")
            message.set_metadata("Ja foste", "candido")
                        
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

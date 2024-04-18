from spade.behaviour import OneShotBehaviour, PeriodicBehaviour, CyclicBehaviour, FSMBehaviour, State
from spade.message import Message
import json

from order import DeliveryOrder
from drone.utils import best_available_orders
from misc.distance import next_position

# ----------------------------------------------------------------------------------------------

TIME_MULTIPLIER = 500 # increases the speed per tick to 10km/s, with a base velocity of 20 m/s
DECIDING = 10
DISMISSED = 20
DELIVERING = 30
RETURNING = 40
RETURNED = 50
ERROR = 60

# ---

SUGGEST_ORDER = "suggest"
DECIDE = "decide"
ORDER_PICKUP = "pickup_orders"
RECHARGE_DRONE = "recharge"


METADATA_NEXT_BEHAVIOUR = "next_behaviour"

# ---

STATE_AVAILABLE = "available"
STATE_SUGGEST = "suggest"
STATE_PICKUP = "pickup"
STATE_RECHARGE = "recharge"
STATE_DELIVER = "deliver"

# ----------------------------------------------------------------------------------------------

class FSMBehaviour(FSMBehaviour):
    async def on_start(self):
        print(f"FSM starting at initial state {self.current_state}")

    async def on_end(self):
        print(f"FSM finished at state {self.current_state}")
        self.agent.logger.log(self.agent.params.metrics())
        # self.agent.params.store_results()
        await self.agent.stop()

class AvailableBehaviour(State):
    async def run(self):
        self.warehouses_responses = []
        
        for warehouse in self.agent.warehouse_positions.keys():
            message = Message()
            message.to = warehouse + "@localhost"
            message.body = self.agent.__repr__()
            message.set_metadata("performative", "inform")
            message.set_metadata(METADATA_NEXT_BEHAVIOUR, SUGGEST_ORDER)
            tries = 3
            while tries > 0:
                tries -= 1
                await self.send(message)
                response = await self.receive(timeout=5)
                if response is not None:
                    self.agent.warehouses_responses.append(response)
                    break
        
        print(f"[AVAILABLE] - {self.agent.warehouses_responses}")
        self.set_next_state(STATE_SUGGEST)

class OrderSuggestionsBehaviour(State):
    async def start(self) -> None:
        self.agent.available_order_sets = {}
    
    async def run(self):
        responses = self.agent.warehouses_responses
        if responses == []:
            print("ERROR - No responses from warehouses")
        
        for response in responses:
            print(f"[RESPONSE] - {response.metadata}")
            if response.metadata["performative"] == "propose":
                self.agent.logger.log(f"[PROPOSED] - {str(response.sender)}")
                proposed_orders = json.loads(response.body)
                orders = []
                for order in proposed_orders:
                    order = json.loads(order)
                    orders.append(DeliveryOrder(**order))
                    order_choices = best_available_orders(
                        orders, 
                        self.agent.position["latitude"], 
                        self.agent.position["longitude"], 
                        self.agent.params.max_capacity, 
                        self.agent.params.velocity
                    )
                    
                self.agent.available_order_sets[str(response.sender).split("@")[0]] = order_choices
            elif response.metadata["performative"] == "refuse":
                # This means that the warehouse has no orders to suggest
                self.agent.logger.log(f"[REFUSED] - {str(response.sender)}")
                self.agent.remove_warehouse(str(response.sender).split("@")[0])
                
        # ----
        
        # If there are none, then there aren't available warehouses, so the drone should kiss the ground
        if len(self.agent.available_order_sets) > 0:
            winner, orders = self.agent.best_orders()
            print(f"[SUGGEST] - {winner} - {orders}")
            # For now, ignore the case where there is no winner
            if winner is not None:
                for warehouse in self.agent.available_order_sets.keys():
                    message = Message()
                    message.to = warehouse + "@localhost"
                    message.set_metadata(METADATA_NEXT_BEHAVIOUR, DECIDE)
                    
                    if warehouse == winner:
                        message.set_metadata("performative", "accept-proposal")
                        message.body = json.dumps([order.__repr__() for order in orders])
                        self.agent.next_warehouse = warehouse
                        await self.send(message)
                    else:
                        message.set_metadata("performative", "reject-proposal")                        
                        await self.send(message)
                
                # TODO: This may not be the case, but for now we will assume that it is the best choice
                self.agent.logger.log(f"[DECIDED] - {winner} - {orders}")
                self.set_next_state(ORDER_PICKUP)
                
class PickupOrdersBehaviour(State):
    async def run(self):
        # TODO: Now it includes the first stage of returning to the warehouse
        # Only at the end it sends a message to pickup
        ...
        next_warehouse_lat, next_warehouse_lon = self.agent.get_next_warehouse_position()
        position = next_position(
                self.agent.position['latitude'], self.agent.position['longitude'],
                next_warehouse_lat, next_warehouse_lon,
                self.agent.params.velocity * TIME_MULTIPLIER
            )
        

# ----------------------------------------------------------------------------------------------

class EmitPositionBehaviour(PeriodicBehaviour):
    async def run(self):
        data = [order.get_order_for_visualization() for order in self.agent.orders_to_visualize]
        data.append({
            'id': self.agent.params.id,
            'latitude': self.agent.position['latitude'],
            'longitude': self.agent.position['longitude'],
            'distance': self.agent.params.total_distance,
            'capacity': round(self.agent.params.curr_capacity * 100.0/self.agent.params.max_capacity,2),
            'autonomy': round(self.agent.params.curr_autonomy * 100.0/self.agent.params.max_autonomy,2),
            'orders_delivered': self.agent.params.orders_delivered,
            'type': 'drone'
        })        
        self.agent.socketio.emit('update_data', data)
        self.agent.orders_to_visualize = []
            
# ----------------------------------------------------------------------------------------------
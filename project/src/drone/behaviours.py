# ----------------------------------------------------------------------------------------------

import datetime
from spade.behaviour import OneShotBehaviour, PeriodicBehaviour, CyclicBehaviour
from spade.message import Message

from drone.utils import *
from misc.distance import haversine_distance, next_position
import json

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
ORDER_PICKUP = "pickup_orders"
RECHARGE_DRONE = "recharge"

METADATA_NEXT_BEHAVIOUR = "next_behaviour"

# ----------------------------------------------------------------------------------------------

class AvailableBehaviour(OneShotBehaviour):
    async def on_start(self):
        self.responses = []

    async def run(self):
        for warehouse in self.agent.warehouse_positions.keys():
            message = Message()
            message.to = warehouse + "@localhost"
            message.body = self.agent.__repr__()
            message.set_metadata("performative", "inform")
            message.set_metadata(METADATA_NEXT_BEHAVIOUR, SUGGEST_ORDER)
            await self.send(message)
            response = await self.receive(timeout=5)
            self.responses.append(response)
            
    async def on_end(self):
        self.agent.add_behaviour(OrderSuggestionsBehaviour(self.responses))
        
# ----------------------------------------------------------------------------------------------

class OrderSuggestionsBehaviour(CyclicBehaviour):
    def __init__(self, messages : list[Message]):
        super().__init__()
        self.messages = messages

    async def on_start(self):
        self.agent.available_order_sets = {}
    
    async def run(self):
        if len(self.agent.available_order_sets) == len(self.agent.warehouse_positions):
            self.kill(exit_code=DECIDING)
        
        for message in self.messages:
            if message is None:
                self.kill(exit_code=ERROR)
                return
            
            if message.metadata["performative"] == "propose":
                proposed_orders = json.loads(message.body)
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
                self.agent.available_order_sets[str(message.sender).split("@")[0]] = order_choices
                
            elif message.metadata["performative"] == "refuse":
                self.agent.logger.log(f"[REFUSED] {self.agent.params.id} - {str(message.sender)}")
                self.agent.remove_warehouse(str(message.sender).split("@")[0])
                
                if not self.agent.any_warehouse_available():
                    self.kill(exit_code=DISMISSED)
                    return
            
    async def on_end(self):
        if self.exit_code == ERROR:
            self.agent.logger.log(f"[ERROR] {self.agent.params.id} - No response from warehouse. Self Destruction activated.")
            await self.agent.stop()
        elif self.exit_code == DECIDING:
            self.agent.add_behaviour(DecideOrdersBehaviour())
        elif self.exit_code == DISMISSED:
            self.agent.logger.log(self.agent.params.metrics())
            self.agent.params.store_results()
            await self.agent.stop()
            
# ----------------------------------------------------------------------------------------------

class DecideOrdersBehaviour(OneShotBehaviour):
    async def run(self):
        winner = self.agent.best_order_decision()
        if winner is None:
            for warehouse in self.agent.warehouse_positions.keys():
                message = Message()
                message.to = warehouse + "@localhost"
                message.set_metadata("performative", "refuse")
                await self.send(message)
            self.kill(exit_code=DELIVERING)
        else:
            for warehouse in self.agent.warehouse_positions.keys():
                message = Message()
                message.to = warehouse + "@localhost"
                if warehouse == winner:
                    self.agent.next_orders += self.agent.available_order_sets[warehouse]
                    self.agent.next_warehouse = warehouse
                    message.set_metadata("performative", "agree")
                    message.body = self.agent.available_order_sets[winner]
                else:
                    message.set_metadata("performative", "refuse")
                await self.send(message)
            self.kill(exit_code=RETURNING)
            
    async def on_end(self):
        if self.exit_code == DELIVERING:
            self.agent.add_behaviour(DeliverBehaviour(period=1.0))
        elif self.exit_code == RETURNING:
            self.agent.add_behaviour(ReturnBehaviour(period=1.0))

# ----------------------------------------------------------------------------------------------

class DeliverBehaviour(PeriodicBehaviour):
    async def run(self):
        if len(self.agent.next_orders) == 0:
            self.kill()
        else:
            if self.agent.next_order is None:
                self.agent.next_order = self.agent.next_orders[0]
            next_order_lat = self.agent.next_order.destination_position['latitude']
            next_order_lon = self.agent.next_order.destination_position['longitude']
            position = next_position(
                    self.agent.position['latitude'],
                    self.agent.position['longitude'],
                    next_order_lat,
                    next_order_lon,
                    self.agent.params.velocity * TIME_MULTIPLIER
                )
            self.agent.params.curr_autonomy -= haversine_distance(
                self.agent.position['latitude'],
                self.agent.position['longitude'],
                position['latitude'],
                position['longitude']
            )
            self.agent.position = position
            if self.agent.arrived_to_target(next_order_lat, next_order_lon):
                self.agent.drop_order(self.agent.next_order)
                self.kill()
            else:
                self.agent.logger.log("[DELIVERING] {} - {} meters to next drop-off"\
                    .format(str(self.agent), 
                            round(
                                haversine_distance(
                                    self.agent.position['latitude'], 
                                    self.agent.position['longitude'], 
                                    next_order_lat, 
                                    next_order_lon
                                ), 2
                            ))
                    )
    
    async def on_end(self):
        self.agent.add_behaviour(AvailableBehaviour())
            
# ----------------------------------------------------------------------------------------------

class ReturnBehaviour(PeriodicBehaviour):
    async def run(self):
        if not self.agent.any_warehouse_available():
            self.kill(exit_code=ERROR)
            return 
        next_warehouse_lat, next_warehouse_lon = self.agent.get_next_warehouse_position()
        position = next_position(
                self.agent.position['latitude'],
                self.agent.position['longitude'],
                next_warehouse_lat,
                next_warehouse_lon,
                self.agent.params.velocity * TIME_MULTIPLIER
            )
        self.agent.params.curr_autonomy -= haversine_distance(
            self.agent.position['latitude'],
            self.agent.position['longitude'],
            position['latitude'],
            position['longitude']
        )
        self.agent.position = position
        if self.agent.arrived_to_target(next_warehouse_lat, next_warehouse_lon):
            self.agent.params.curr_autonomy = self.agent.params.max_autonomy
            self.agent.next_warehouse = None
            self.kill(exit_code=RETURNED)
        else:
            self.agent.logger.log("[RETURNING] {} - Distance to warehouse: {} meters"\
                .format(self.agent.params.id, 
                        round(haversine_distance(
                            self.agent.position['latitude'], 
                            self.agent.position['longitude'], 
                            next_warehouse_lat,
                            next_warehouse_lon
                        ), 2
                    ))
                )
    
    async def on_end(self):
        if self.exit_code == ERROR:
            self.agent.logger.log(f"[ERROR] {self.agent.params.id} - No warehouse available to return to. Self Destruction activated.")
            await self.agent.stop()
        elif self.exit_code == RETURNED:
            self.agent.logger.log(f"[RETURNED] {self.agent.params.id}")
            self.agent.add_behaviour(AvailableBehaviour())

# ----------------------------------------------------------------------------------------------

class PickUpOrdersBehaviour(OneShotBehaviour):
    async def run(self):
        # TODO: Implement this behaviour
        message = Message()
        message.to = self.agent.next_warehouse + "@localhost"
        message.set_metadata(METADATA_NEXT_BEHAVIOUR, ORDER_PICKUP)
        
        orders_id = [order.id for order in self.agent.next_orders]
        
        message.body = json.dumps(orders_id)
        
        await self.send(message)
        
        response = await self.receive(timeout=5)
        if response is None:
            self.agent.logger.log(f"[PICKUP] {self.agent.params.id} - No response from warehouse. Self Destruction activated.")
            self.kill(exit_code=ERROR)
        else:
            self.agent.logger.log(f"[PICKUP] {self.agent.params.id} - {response.sender}")
            ... # update the agent's orders
        
    async def on_end(self):
        if self.exit_code == ERROR:
            await self.agent.stop()
        else:
            self.agent.add_behaviour(RechargeBehaviour())
        
# ----------------------------------------------------------------------------------------------

class RechargeBehaviour(OneShotBehaviour):
    async def run(self):
        message = Message()
        message.to = self.agent.next_warehouse + "@localhost"
        message.set_metadata("performative", "request")
        message.set_metadata(METADATA_NEXT_BEHAVIOUR, RECHARGE_DRONE)
        await self.send(message)
        
        response = await self.receive(timeout=5)
        
        if response is None:
            self.agent.logger.log(f"[ERROR] {self.agent.params.id} - No response from warehouse to recharge. Self Destruction activated.")
            self.kill(exit_code=ERROR)
        else:
            if response.metadata["performative"] == "refuse":
                self.agent.logger.log(f"[ERROR] {self.agent.params.id} - Warehouse {response.sender} refused to recharge drone. Self Destruction activated.")
                self.kill(exit_code=ERROR)
            elif response.metadata["performative"] == "agree":
                self.agent.logger.log(f"[RECHARGE] {self.agent.params.id} at Warehouse {response.sender}")
                self.agent.params.refill_autonomy()
                self.kill()

    async def on_end(self):
        if self.exit_code == ERROR:
            await self.agent.stop()
        else:
            self.agent.add_behaviour(DeliverBehaviour(period=1.0))

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
        self.agent.socketio.emit(
            'update_data', 
            data
        )
        self.agent.orders_to_visualize = []
        
# ----------------------------------------------------------------------------------------------
        
class EmitSetupBehaviour(OneShotBehaviour):
    async def run(self):
        self.agent.socketio.emit(
            'update_data', 
            [
                {
                    'id': self.agent.params.id,
                    'latitude': self.agent.position['latitude'],
                    'longitude': self.agent.position['longitude'],
                    'type': 'drone'
                }
            ]
        )
        
    async def on_end(self) -> None:
        self.agent.add_behaviour(EmitPositionBehaviour(period=1.0))
        self.agent.add_behaviour(AvailableBehaviour())
            
# ----------------------------------------------------------------------------------------------
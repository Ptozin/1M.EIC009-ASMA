import asyncio
from spade.behaviour import OneShotBehaviour, PeriodicBehaviour, CyclicBehaviour, FSMBehaviour, State
from spade.message import Message
import json

from order import DeliveryOrder
from drone.utils import best_available_orders
from misc.distance import haversine_distance, next_position

# ----------------------------------------------------------------------------------------------

DECIDING = 10
DISMISSED = 20
DELIVERING = 30
RETURNING = 40
RETURNED = 50

# ---

SUGGEST_ORDER = "suggest"
DECIDE = "decide"
PICKUP = "pickup_orders"
RECHARGE_DRONE = "recharge"


METADATA_NEXT_BEHAVIOUR = "next_behaviour"

# ---

STATE_AVAILABLE = "available"
STATE_SUGGEST = "suggest"
STATE_PICKUP = "pickup"
STATE_RECHARGE = "recharge"
STATE_DELIVER = "deliver"
STATE_DEAD = "dead"

# ----------------------------------------------------------------------------------------------

class FSMBehaviour(FSMBehaviour):
    async def on_start(self):
        self.agent.logger.log(f"FSM starting at initial state {self.current_state}")
        print(f"FSM starting at initial state {self.current_state}")

    async def on_end(self):
        self.agent.logger.log(f"FSM finished at state {self.current_state}")
        print(f"FSM finished at state {self.current_state}")
        self.agent.need_to_stop = True
        orders_id = [order.id for order in self.agent.total_orders]
        
        self.agent.logger.log(self.agent.params.metrics(orders_id=orders_id))
        self.agent.params.store_results()

# ----------------------------------------------------------------------------------------------

class AvailableBehaviour(State):
    async def run(self):
        self.agent.warehouses_responses = []
        
        for warehouse in self.agent.warehouse_positions.keys():
            message = Message()
            message.to = warehouse + "@localhost"
            message.body = self.agent.__repr__()
            message.set_metadata("performative", "inform")
            message.set_metadata(METADATA_NEXT_BEHAVIOUR, SUGGEST_ORDER)
            await self.send(message)
            response = await self.receive(timeout=5)
            if response is not None:
                self.agent.warehouses_responses.append(response)
            else:
                self.agent.logger.log("[ERROR] - No response from warehouse")
                self.set_next_state(STATE_DEAD)
                return
        
        # print(f"[AVAILABLE] - {len(self.agent.warehouses_responses)}")
        self.set_next_state(STATE_SUGGEST)

# ----------------------------------------------------------------------------------------------

class OrderSuggestionsBehaviour(State):
    async def run(self):
        self.agent.available_order_sets = {}
        responses = self.agent.warehouses_responses
        if responses == []:
            print("ERROR - No responses from warehouses")
            self.set_next_state(STATE_DEAD)
            return
        
        for response in responses:
            if response.metadata["performative"] == "propose":
                self.agent.logger.log(f"[PROPOSED] - {str(response.sender)}")
                
                #TODO: check, this can come in empty!!! Why though??
                # ANSWER: all orders are reserved, but dosn't mean we can remove them
                # thats what we are doing, so we good
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
                if proposed_orders != []:
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
            self.agent.orders_to_be_picked[winner] = self.agent.available_order_sets[winner]
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
                self.set_next_state(STATE_PICKUP)
        else:
            self.agent.logger.log("[FINISH] - No available orders")
            self.set_next_state(STATE_DEAD)

# ----------------------------------------------------------------------------------------------
              
class PickupOrdersBehaviour(State):
    async def run(self):
        while not self.agent.arrived_at_next_warehouse():
            next_warehouse_lat, next_warehouse_lon = self.agent.get_next_warehouse_position()
            self.agent.update_position(next_warehouse_lat, next_warehouse_lon)
            await asyncio.sleep(self.agent.tick_rate)
        
        # If the drone has arrived at the warehouse, then it should pick up the orders
        message = Message()
        message.to = self.agent.next_warehouse + "@localhost"
        message.set_metadata(METADATA_NEXT_BEHAVIOUR, PICKUP)
        
        orders_id = [order.id for order in self.agent.orders_to_be_picked[self.agent.next_warehouse]]
        message.body = json.dumps(orders_id)
        
        await self.send(message)
        response = await self.receive(timeout=5)
        
        if response is not None:
            if response.metadata["performative"] == "confirm":
                self.agent.logger.log("[PICKUP] - {} Orders picked up at {}".format(len(orders_id), self.agent.next_warehouse))
                
                #TODO: recover autonomy, for now refills it
                self.agent.recharge()
                
                for order in self.agent.orders_to_be_picked[self.agent.next_warehouse]:
                    self.agent.add_order(order)
                
                del self.agent.orders_to_be_picked[self.agent.next_warehouse]
                
                self.set_next_state(STATE_DELIVER)
            else:
                self.agent.logger.log("[ERROR] - Orders not picked up")
                self.set_next_state(STATE_DEAD)
        else:
            self.agent.logger.log("[ERROR] - No response from warehouse")
            self.set_next_state(STATE_DEAD)
        
# ----------------------------------------------------------------------------------------------

class DeliverOrdersBehaviour(State):
    async def run(self):  
        # if not self.agent.has_inventory():
        #     self.agent.logger.log("[DELIVERING] - No orders to deliver")
        #     self.set_next_state(STATE_AVAILABLE)
        #     return
        
        while self.agent.has_inventory():
            while not self.agent.arrived_at_next_order():
                next_order_lat, next_order_lon = self.agent.get_next_order_position()
                self.agent.update_position(next_order_lat, next_order_lon)
                await asyncio.sleep(self.agent.tick_rate)
        
            # If the drone has arrived at the order's destination, then it should deliver the order
            self.agent.drop_order()
        
        self.set_next_state(STATE_AVAILABLE)

# ----------------------------------------------------------------------------------------------

class DeadBehaviour(State):
    async def run(self):
        self.agent.logger.log("[DEADBEHAVIOUR] - Drone out of battery or something like that")

# ----------------------------------------------------------------------------------------------

class EmitPositionBehaviour(PeriodicBehaviour):
    async def run(self):
        data = [order.get_order_for_visualization() for order in self.agent.orders_to_visualize]
        self.agent.orders_to_visualize = []
        data.append(self.agent.get_current_metrics())        
        self.agent.socketio.emit('update_data', data)
        
        if self.agent.need_to_stop:
            self.kill()
            await self.agent.stop()
            
# ----------------------------------------------------------------------------------------------

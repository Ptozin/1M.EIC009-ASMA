import asyncio
from spade.behaviour import PeriodicBehaviour, FSMBehaviour, State
from spade.message import Message
import json

from order import DeliveryOrder
from drone.utils import *

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
STATE_DELIVER = "deliver"
STATE_DEAD = "dead"

TRIES = 3
TIMEOUT = 2.0

# ----------------------------------------------------------------------------------------------

class FSMBehaviour(FSMBehaviour):
    async def on_start(self):
        self.agent.logger.log(f"FSM starting at initial state {self.current_state}")

    async def on_end(self):
        self.agent.logger.log(f"FSM finished at state {self.current_state}")
        self.agent.need_to_stop = True
        orders_id = [order.id for order in self.agent.total_orders]
        
        self.agent.logger.log(self.agent.params.metrics(orders_id=orders_id))
        self.agent.params.store_results()

# ----------------------------------------------------------------------------------------------

class AvailableBehaviour(State):
    async def run(self):
        self.agent.warehouses_responses = []
        
        warehouses = []
        if self.agent.required_warehouse is None:
            warehouses = self.agent.warehouse_positions.keys()
        else:
            warehouses = [self.agent.required_warehouse]
        
        for warehouse in warehouses:
            message = Message()
            message.to = warehouse + "@localhost"
            message.body = self.agent.__repr__()
            message.set_metadata("performative", "inform")
            message.set_metadata(METADATA_NEXT_BEHAVIOUR, SUGGEST_ORDER)
            response = None
            
            for _ in range(TRIES):
                await self.send(message)
                response = await self.receive(timeout=TIMEOUT)
                if response is not None:
                    self.agent.warehouses_responses.append(response)
                    break
                else:
                    self.agent.logger.log(f"[ERROR] - No response from warehouse {warehouse}, trying again...")
                    
            if response is None:
                self.agent.logger.log(f"[ERROR] - No response from warehouse {warehouse} - {warehouse in self.agent.warehouse_positions.keys()}")
                self.agent.died_successfully = False
                self.set_next_state(STATE_DEAD)
                return
        self.set_next_state(STATE_SUGGEST)

# ----------------------------------------------------------------------------------------------

class OrderSuggestionsBehaviour(State):
    async def run(self):
        self.agent.available_order_sets = {}
        responses = self.agent.warehouses_responses
        if not responses:
            self.agent.logger.log("[ERROR] - No responses from warehouses")
            self.agent.died_successfully = False
            self.set_next_state(STATE_DEAD)
            return
        for response in responses:
            performative = response.metadata.get("performative")
            sender = str(response.sender).split("@")[0]
            if performative == "propose":
                self._handle_proposal(response, sender)
            elif performative == "refuse":
                self._handle_refusal(sender)
        if self.agent.available_order_sets:
            await self._process_available_orders()
        elif self.agent.has_inventory():
            self.agent.logger.log("[ORDER SUGGESTION] - No available orders - Delivering remaining orders...")
            self.set_next_state(STATE_DELIVER)
        else:
            self.agent.logger.log(f"[FINISH] - No available orders - {self.agent.has_inventory()}")
            self.agent.died_successfully = True
            self.set_next_state(STATE_DEAD)
    
    def _handle_proposal(self, response, sender):
        self.agent.logger.log(f"[PROPOSED] - {sender}")
        proposed_orders = json.loads(response.body)
        orders = [DeliveryOrder(**json.loads(order)) for order in proposed_orders]
        self.agent.logger.log(f"PROPOSED ORDERS: {orders}")
        self.agent.logger.log(f"CURR CAPACITY: {self.agent.params.max_capacity - self.agent.params.curr_capacity}")
        self.agent.available_order_sets[sender] = best_available_orders(
            orders,
            self.agent.warehouse_positions[sender]["latitude"],
            self.agent.warehouse_positions[sender]["longitude"],
            self.agent.params.max_capacity - self.agent.params.curr_capacity,
            self.agent.params.max_autonomy
        )
    
    def _handle_refusal(self, sender):
        self.agent.logger.log(f"[REFUSED] - {sender}")
        self.agent.remove_warehouse(sender)
    
    async def _process_available_orders(self):
        # TODO: what is the if statement for? It is killing the program, need to check this ASAP
        #if self.agent.required_warehouse is None:
        #    winner, orders = self.agent.best_orders()
        #else:
        #    winner, orders = self.agent.required_warehouse, self.agent.available_order_sets[self.agent.required_warehouse]
        
        winner, orders = self.agent.best_orders()
        
        if winner:
            await self._send_proposal_accepted(winner, orders)
            self.agent.next_warehouse = winner
            self.agent.orders_to_be_picked[winner] = orders
            self.set_next_state(STATE_PICKUP)
        else:
            losers = self.agent.available_order_sets.keys()
            await self._send_proposal_rejected(losers)
            self.set_next_state(STATE_DELIVER)
    
    async def _send_proposal_accepted(self, winner, orders):
        message = Message()
        message.to = winner + "@localhost"
        message.set_metadata(METADATA_NEXT_BEHAVIOUR, DECIDE)
        message.set_metadata("performative", "accept-proposal")
        message.body = json.dumps([order.__repr__() for order in orders] if orders else [])
        await self.send(message)
        self.agent.logger.log(f"[DECIDED] - {winner} - {orders}")
        losers = [warehouse for warehouse in self.agent.available_order_sets.keys() if warehouse != winner]
        await self._send_proposal_rejected(losers)
    
    async def _send_proposal_rejected(self, losers):
        for warehouse in losers:
            message = Message()
            message.to = warehouse + "@localhost"
            message.set_metadata(METADATA_NEXT_BEHAVIOUR, DECIDE)
            message.set_metadata("performative", "reject-proposal")
            await self.send(message)
        self.agent.logger.log("[DECIDED] - None - None")

# ----------------------------------------------------------------------------------------------

class PickupOrdersBehaviour(State):
    async def run(self):
        while not self.agent.arrived_at_next_warehouse():
            next_warehouse_lat, next_warehouse_lon = self.agent.get_next_warehouse_position()
            self.agent.update_position(next_warehouse_lat, next_warehouse_lon)
            await asyncio.sleep(self.agent.tick_rate)

        if self.agent.orders_to_be_picked[self.agent.next_warehouse] is None:
            self.handle_no_orders_to_pick()
        else:
            await self.pickup_orders()

    def handle_no_orders_to_pick(self):
        if self.agent.next_orders:
            closest_order_warehouse = closest_order(
                self.agent.warehouse_positions[self.agent.next_warehouse]["latitude"],
                self.agent.warehouse_positions[self.agent.next_warehouse]["longitude"],
                self.agent.next_orders
            )
            self.update_after_pickup(closest_order_warehouse)
        else:
            self.set_next_state(STATE_AVAILABLE)

    async def pickup_orders(self):
        orders_id = [order.id for order in self.agent.orders_to_be_picked[self.agent.next_warehouse]]
        message = Message()
        message.to = self.agent.next_warehouse + "@localhost"
        message.set_metadata(METADATA_NEXT_BEHAVIOUR, PICKUP)
        message.body = json.dumps(orders_id)
        await self.send(message)
        response = await self.receive(timeout=TIMEOUT)
        if response and response.metadata["performative"] == "confirm":
            self.agent.logger.log("[PICKUP] - {} Orders picked up at {} - {}".format(len(orders_id), self.agent.next_warehouse, orders_id))
            self.agent.recharge()
            for order in self.agent.orders_to_be_picked[self.agent.next_warehouse]:
                self.agent.add_order(order)
            del self.agent.orders_to_be_picked[self.agent.next_warehouse]
            closest_order_next_warehouse = closest_order(
                self.agent.warehouse_positions[self.agent.next_warehouse]["latitude"],
                self.agent.warehouse_positions[self.agent.next_warehouse]["longitude"],
                self.agent.next_orders
            )
            self.update_after_pickup(closest_order_next_warehouse)
        else:
            self.agent.logger.log("[ERROR] - Orders not picked up")
            self.agent.died_successfully = False
            self.set_next_state(STATE_DEAD)

    def update_after_pickup(self, closest_order_next_warehouse):
        self.agent.next_order = closest_order_next_warehouse
        self.agent.next_orders = generate_path(self.agent.next_orders, closest_order_next_warehouse)
        self.agent.tasks_in_range()
        self.set_next_state(STATE_DELIVER)
        
# ----------------------------------------------------------------------------------------------

class DeliverOrdersBehaviour(State):
    async def run(self):  
        if not self.agent.has_inventory():
            self.agent.logger.log("[DELIVERING] - No orders to deliver")
            self.set_next_state(STATE_AVAILABLE)
            return
        
        while not self.agent.arrived_at_next_order():
            next_order_lat, next_order_lon = self.agent.get_next_order_position()
            self.agent.update_position(next_order_lat, next_order_lon)
            await asyncio.sleep(self.agent.tick_rate)
            
        max_order = self.agent.next_order is not None and self.agent.next_order == self.agent.max_deliverable_order

        self.agent.drop_order()    
        if max_order:
            self.agent.required_warehouse = closest_warehouse(
                self.agent.position["latitude"],
                self.agent.position["longitude"],
                self.agent.warehouse_positions
            )
            
        # TODO: check if this fixes the killing behaviour
        if len(self.agent.warehouse_positions) == 0:
            self.agent.logger.log("[DELIVERING] - No warehouses left - Continuing to deliver orders...")
            self.set_next_state(STATE_DELIVER)
        else:  
            self.set_next_state(STATE_AVAILABLE)

# ----------------------------------------------------------------------------------------------

class DeadBehaviour(State):
    async def run(self):
        if self.agent.died_successfully:
            self.agent.logger.log("[DEAD BEHAVIOUR] - Drone successfully completed its mission.")
        else:
            self.agent.logger.log("[DEAD BEHAVIOUR] - Something went wrong.")

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

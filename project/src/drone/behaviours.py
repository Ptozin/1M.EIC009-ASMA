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

# ----------------------------------------------------------------------------------------------

class AvailableBehaviour(OneShotBehaviour):
    async def run(self):
        for warehouse in self.agent.warehouse_positions.keys():
            message = Message()
            message.to = warehouse + "@localhost"
            message.body = self.agent.__repr__()
            message.set_metadata("performative", "inform")
            await self.send(message)
            
    async def on_end(self):
        self.agent.add_behaviour(ReceiveOrdersBehaviour())
            
# ----------------------------------------------------------------------------------------------

class DecideOrdersBehaviour(OneShotBehaviour):
    async def run(self):
        winner = self.best_order_decision()
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
            self.agent.add_behaviour(DeliverBehaviour(period=1.0, start_at=datetime.datetime.now()))
        elif self.exit_code == RETURNING:
            self.agent.add_behaviour(ReturnBehaviour(period=1.0, start_at=datetime.datetime.now()))
      
    # ----------------------------------------------------------------------------------------------
      
    def best_order_decision(self) -> str:
        orders = self.agent.next_orders
        path = generate_path(orders)
        travel_time = self.time_to_order(orders) + calculate_travel_time(path, self.agent.params.velocity)
        capacity_level = calculate_capacity_level(orders, self.agent.params.max_capacity)
        utility = utility(travel_time, capacity_level)
        winner = None
        for warehouse, orders in self.agent.available_order_sets.items():
            orders = self.agent.next_orders + orders
            path = generate_path(orders)
            travel_time = self.time_to_warehouse(warehouse) + self.time_warehouse_to_order(warehouse, orders) + calculate_travel_time(path, self.agent.params.velocity)
            orders += self.agent.next_orders
            capacity_level = calculate_capacity_level(orders, self.agent.params.max_capacity)
            new_utility = utility(travel_time, capacity_level)
            if new_utility > utility:
                winner = warehouse
                utility = new_utility
        return winner

    def time_to_order(self, orders : list[DeliveryOrder]) -> float:
        closest = closest_order(
            self.agent.position["latitude"],
            self.agent.position["longitude"], 
            orders
        )
        distance = haversine_distance(self.agent.position, closest.destination_position)
        return distance / self.agent.params.velocity
        
    def time_to_warehouse(self, warehouse : str) -> float:
        distance = haversine_distance(self.agent.position, self.agent.warehouse_positions[warehouse])
        return distance / self.agent.params.velocity
    
    def time_warehouse_to_order(self, warehouse : str, orders : list[DeliveryOrder]) -> float:
        closest = closest_order(
            self.agent.warehouse_positions[warehouse]['latitude'], 
            self.agent.warehouse_positions[warehouse]['longitude'], 
            orders
        )
        distance = haversine_distance(self.agent.warehouse_positions[warehouse], closest.destination_position)
        return distance / self.agent.params.velocity

# ----------------------------------------------------------------------------------------------

class DeliverBehaviour(PeriodicBehaviour):
    async def run(self):
        if len(self.agent.next_orders) == 0:
            self.kill()
        else:
            if self.agent.next_order is None:
                self.agent.next_order = self.agent.next_orders[0]
                            
            position = next_position(
                    self.agent.position['latitude'],
                    self.agent.position['longitude'],
                    self.agent.next_order.destination_position['latitude'],
                    self.agent.next_order.destination_position['longitude'],
                    self.agent.params.velocity * TIME_MULTIPLIER
                )
            
            self.agent.params.curr_autonomy -= haversine_distance(
                self.agent.position['latitude'],
                self.agent.position['longitude'],
                position['latitude'],
                position['longitude']
            )
            
            self.agent.position = position
            
            self.agent.logger.log("[DELIVERING] {} - {} meters to next drop-off"\
                .format(str(self.agent), 
                        round(
                            haversine_distance(self.agent.position['latitude'], 
                                           self.agent.position['longitude'], 
                                           self.agent.next_order.destination_position['latitude'], 
                                           self.agent.next_order.destination_position['longitude']),
                            2
                        ))
                )
            
            if self.agent.arrived_to_target(self.agent.next_order.destination_position['latitude'], self.agent.next_order.destination_position['longitude']):
                self.agent.drop_order(self.agent.next_order)
                self.kill()
    
    async def on_end(self):
        self.agent.add_behaviour(AvailableBehaviour())

# ----------------------------------------------------------------------------------------------

class ReceiveOrdersBehaviour(CyclicBehaviour):
    async def on_start(self):
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
                self.kill(exit_code=DISMISSED)
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

class ReturnBehaviour(PeriodicBehaviour):
    async def run(self):
        if not self.agent.available_warehouses():
            self.kill(exit_code=ERROR)
            return 
        next_warehouse_lat, next_warehouse_lon = self.agent.get_next_warehouse_position()
        self.agent.position = next_position(
                self.agent.position['latitude'],
                self.agent.position['longitude'],
                next_warehouse_lat,
                next_warehouse_lon,
                self.agent.params.velocity * TIME_MULTIPLIER
            )
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
                        ),2)
                    )
                )
    
    async def on_end(self):
        if self.exit_code == ERROR:
            self.agent.logger.log(f"[ERROR] {self.agent.params.id} - No warehouse available to return to. Self Destruction activated.")
            await self.agent.stop()
        elif self.exit_code == RETURNED:
            self.agent.logger.log(f"[RETURNED] {self.agent.params.id}")
            self.agent.add_behaviour(AvailableBehaviour())
        else:
            self.agent.logger.log(f"[ERROR] {self.agent.params.id} - Unexpected error")
            await self.agent.stop()

# ----------------------------------------------------------------------------------------------

# Visualization Behaviours

class EmitPositionBehav(PeriodicBehaviour):
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
        
class EmitSetupBehav(OneShotBehaviour):
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
        self.agent.add_behaviour(EmitPositionBehav(period=1.0))
            
# ----------------------------------------------------------------------------------------------
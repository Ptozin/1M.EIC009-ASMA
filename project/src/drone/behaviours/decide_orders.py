# ----------------------------------------------------------------------------------------------

from spade.behaviour import OneShotBehaviour
from spade.message import Message

from src.drone.agent import DroneAgent
from utils import *
from misc.distance import haversine_distance

# ----------------------------------------------------------------------------------------------

class DecideOrdersBehaviour(OneShotBehaviour):
    async def on_start(self):
        self.agent : DroneAgent = self.agent
    
    async def run(self):
        winner = self.best_order_decision()
        if winner == "drone":
            for warehouse in self.agent.warehouse_positions.keys():
                message = Message()
                message.to = warehouse + "@localhost"
                message.set_metadata("performative", "refuse")
                await self.send(message)
        else:
            for warehouse in self.agent.warehouse_positions.keys():
                message = Message()
                message.to = warehouse + "@localhost"
                if warehouse == winner:
                    message.set_metadata("performative", "agree")
                    message.body = self.agent.available_order_sets[winner]
                else:
                    message.set_metadata("performative", "refuse")
                await self.send(message)
            
    async def on_end(self):
        # TODO: call deliver or returning behaviour, depending on mid-flight decisions
        pass
      
    # ----------------------------------------------------------------------------------------------
      
    def best_order_decision(self) -> str:
        orders = self.agent.next_orders
        path = generate_path(orders)
        travel_time = self.time_to_order(orders) + calculate_travel_time(path, self.agent.params.velocity)
        capacity_level = calculate_capacity_level(orders, self.agent.params.max_capacity)
        utility = utility(travel_time, capacity_level)
        winner = "drone"
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
        closest = closest_order(self.agent.position, orders)
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
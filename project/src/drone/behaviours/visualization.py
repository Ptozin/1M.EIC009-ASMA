# ----------------------------------------------------------------------------------------------

from spade.behaviour import PeriodicBehaviour, OneShotBehaviour

# ----------------------------------------------------------------------------------------------

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
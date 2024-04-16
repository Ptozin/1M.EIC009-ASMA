# ----------------------------------------------------------------------------------------------

from spade.behaviour import OneShotBehaviour

# ----------------------------------------------------------------------------------------------
        
class EmitSetupBehav(OneShotBehaviour):
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
            
# ----------------------------------------------------------------------------------------------
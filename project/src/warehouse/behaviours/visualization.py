# ----------------------------------------------------------------------------------------------

from spade.behaviour import PeriodicBehaviour, OneShotBehaviour

from ..agent import WarehouseAgent

# ----------------------------------------------------------------------------------------------
        
class EmitSetupBehav(OneShotBehaviour):
    async def on_start(self):
        self.agent : WarehouseAgent = self.agent
    async def run(self):
        self.agent.socketio.emit(
            'update_data', 
            [
                {
                    'id': self.agent.params.id,
                    'latitude': self.agent.position['latitude'],
                    'longitude': self.agent.position['longitude'],
                    'type': 'warehouse'
                },
                # TODO: This function needs to be tested beforehand
                order.get_order_for_visualization() for order in self.agent.inventory
            ]
        )
            
# ----------------------------------------------------------------------------------------------
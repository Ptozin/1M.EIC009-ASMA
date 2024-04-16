# ----------------------------------------------------------------------------------------------

from spade.behaviour import PeriodicBehaviour, OneShotBehaviour

from ..agent import DroneAgent

# ----------------------------------------------------------------------------------------------

class EmitPositionBehav(PeriodicBehaviour):
    async def on_start(self):
        self.agent : DroneAgent = self.agent
    
    async def run(self):
        # TODO: This function needs to be created in the agent
        self.agent.socketio.emit(
            'update_data', 
            [
                {
                    'id': self.agent.params.id,
                    'latitude': self.agent.position['latitude'],
                    'longitude': self.agent.position['longitude'],
                    'type': 'drone'
                },
                # ----
                # Needs to also include the orders with the status
                # ----
            ]
        )
        
class EmitSetupBehav(OneShotBehaviour):
    async def on_start(self):
        self.agent : DroneAgent = self.agent
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
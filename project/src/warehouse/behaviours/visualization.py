# ----------------------------------------------------------------------------------------------

from spade.behaviour import PeriodicBehaviour

from ..agent import WarehouseAgent

# ----------------------------------------------------------------------------------------------

class EmitPositionBehav(PeriodicBehaviour):
    async def on_start(self):
        self.agent : WarehouseAgent = self.agent
    
    async def run(self):
        # TODO: This function needs to be created in the agent
        self.agent.emit_to_socketio() 
            
# ----------------------------------------------------------------------------------------------
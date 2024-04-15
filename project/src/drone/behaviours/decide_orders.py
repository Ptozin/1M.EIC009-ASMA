# ----------------------------------------------------------------------------------------------

from spade.behaviour import OneShotBehaviour

from ..agent import DroneAgent

# ----------------------------------------------------------------------------------------------

class DecideOrdersBehaviour(OneShotBehaviour):
    async def on_start(self):
        self.agent : DroneAgent = self.agent
    
    async def run(self):
        # TODO: from final order choices, choose the best order set and communicate decisions to each available warehouse
        pass
            
    async def on_end(self):
        # TODO: call deliver or returning behaviour, depending on mid-flight decisions
        pass
            
# ----------------------------------------------------------------------------------------------
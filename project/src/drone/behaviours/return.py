# ----------------------------------------------------------------------------------------------

from spade.behaviour import PeriodicBehaviour

from ..agent import DroneAgent
from available import AvailableBehaviour

# ----------------------------------------------------------------------------------------------

TIME_MULTIPLIER = 500 # increases the speed per tick to 10km/s, with a base velocity of 20 m/s

# ----------------------------------------------------------------------------------------------

class ReturnBehaviour(PeriodicBehaviour):
    async def start(self):
        self.agent : DroneAgent = self.agent
    
    async def run(self):
        # TODO: make the drone move to the chosen warehouse, recharge and pack new orders
        pass
    
    async def on_end(self):
        self.agent.add_behaviour(AvailableBehaviour())

# ----------------------------------------------------------------------------------------------
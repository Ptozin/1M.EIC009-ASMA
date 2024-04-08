from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.template import Template

class DroneAgent(Agent):
    def __init__(self, jid, capacity = 0, autonomy = 0, velocity = 0, initialPos = None):
        self.password = 'admin' # TODO: receive main unique password
        super().__init__(jid, self.password)
        self.capacity = capacity
        self.autonomy = autonomy
        self.velocity = velocity
        self.initialPos = initialPos

        self.curr_weight = 0
        self.curr_autonomy = autonomy
        self.tracking_orders = []

    class RecvBehav(OneShotBehaviour):
        async def run(self):
            print("RecBehav running")

            msg = await self.receive(timeout=10)
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")

            await self.agent.stop()

    async def setup(self):
        print("[DRONE] Hello, I'm agent {}".format(str(self.jid)))
        b = self.RecvBehav()
        template = Template()
        template.set_metadata("performative", "inform")
        self.add_behaviour(b, template)

    def __str__(self) -> str:
        return "Drone {} with capacity {} and autonomy {}".format(str(self.jid), self.capacity, self.autonomy, self.velocity, self.initialPos)
    
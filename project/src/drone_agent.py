from spade.agent import Agent

class DroneAgent(Agent):
    def __init__(self, jid, capacity = 0, autonomy = 0, velocity = 0, initialPos = None):
        self.password = 'admin' # TO-DO: receive main unique password
        super().__init__(jid, self.password)
        self.capacity = capacity
        self.autonomy = autonomy
        self.velocity = velocity
        self.initialPos = initialPos

        self.curr_weight = 0
        self.curr_autonomy = autonomy
        self.tracking_orders = []

    async def setup(self):
        print("[DRONE] Hello, I'm agent {}".format(str(self.jid)))
        print("Capacity:", self.capacity)
        print("Autonomy:", self.autonomy)
        print("Velocity:", self.velocity)
        print("Initial Position:", self.initialPos)

    # Add drone behaviours here
    # ...

    def __str__(self) -> str:
        return "Drone {} with capacity {} and autonomy {}".format(str(self.jid), self.capacity, self.autonomy)
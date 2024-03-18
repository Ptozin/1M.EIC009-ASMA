from spade.agent import Agent

class DroneAgent(Agent):
    def __init__(self, jid, password = "admin", capacity = 0, autonomy = 0, velocity = 0):
        super().__init__(jid, password)
        self.capacity = capacity
        self.autonomy = autonomy
        self.velocity = velocity

        self.curr_weight = 0
        self.curr_autonomy = autonomy
        self.tracking_orders = []

    async def setup(self):
        print("[DRONE] Hello, I'm agent {}".format(str(self.jid)))
        print("Capacity:", self.capacity)
        print("Autonomy:", self.autonomy)
        print("Velocity:", self.velocity)

    # Add drone behaviours here
    # ...

    def __str__(self) -> str:
        return "Drone {} with capacity {} and autonomy {}".format(str(self.jid), self.capacity, self.autonomy)
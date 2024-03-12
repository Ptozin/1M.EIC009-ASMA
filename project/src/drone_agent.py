from spade.agent import Agent

class DroneAgent(Agent):
    def __init__(self, jid, password, capacity, autonomy, velocity, number):
        super().__init__(jid, password)
        self.capacity = capacity
        self.autonomy = autonomy
        self.velocity = velocity
        self.number = number

    async def setup(self):
        print("[DRONE] Hello, I'm agent {}".format(str(self.jid)))
        print("Capacity:", self.capacity)
        print("Autonomy:", self.autonomy)
        print("Velocity:", self.velocity)
        print("Number:", self.number)

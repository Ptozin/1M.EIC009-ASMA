from spade.agent import Agent

class WarehouseAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.inventory = {}

    async def setup(self):
        print("[WAREHOUSE] Hello, I'm agent {}".format(str(self.jid)))

from spade.agent import Agent

class WarehouseAgent(Agent):
    def __init__(self, jid, password = "admin"):
        super().__init__(jid, password)
        self.inventory = {}

    async def setup(self):
        print("[WAREHOUSE] Hello, I'm agent {}".format(str(self.jid)))

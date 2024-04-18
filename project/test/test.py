from spade.agent import Agent
from spade.message import Message
from spade import wait_until_finished
from spade.behaviour import OneShotBehaviour
import spade
import asyncio

class WarehouseAgent(Agent):
    class ReceiveBehaviour(OneShotBehaviour):
        async def run(self):
            print(f"Agent {self.agent.jid} running")
            msg = await self.receive(5)
            print(f"Agent {self.agent.jid} received message: {msg}")
    class SimpleBehaviour(OneShotBehaviour):
        async def run(self):
            message = Message(to="drone1@localhost")  # Instantiate the message
            message.metadata = {"performative": "inform"}  # Set the "inform" FIPA performative
            message.body = "Hello World"
            await self.send(message)  # Send the message
        async def on_end(self):
            print("Behaviour finished")
    def __init__(self, jid : str, password : str = "admin") -> None:
        super().__init__(jid, password)
    async def setup(self):
        print(f"SimpleBehaviour Agent {self.jid} started")
        self.add_behaviour(self.SimpleBehaviour())
        
class DroneAgent(Agent):
    class SimpleBehaviour(OneShotBehaviour):
        async def run(self):
            message = await self.receive(5)
            print(f"Agent {self.agent.jid} received message: {message}")
            
            response = Message(to=str(message.sender))
            response.body = "I am a drone"
            await self.send(response)
        async def on_end(self):
            print("SimpleBehaviour Behaviour finished")
    def __init__(self, jid : str, password : str = "admin") -> None:
        super().__init__(jid, password)
    async def setup(self):
        print(f"Agent {self.jid} started")
        self.add_behaviour(self.SimpleBehaviour())

async def start_logic2():
    try:
        warehouse = WarehouseAgent("center1@localhost")
        drone = DroneAgent("drone1@localhost")
        await drone.start()
        await warehouse.start()   
        await wait_until_finished(warehouse)
        await wait_until_finished(drone)
    except Exception as e:
        print("Error: {0}".format(e))
        drone.stop()
        warehouse.stop()
    
if __name__ == "__main__":
    spade.run(start_logic2())
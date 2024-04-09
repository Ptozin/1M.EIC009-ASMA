from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State, CyclicBehaviour
from spade.message import Message
from misc.distance import haversine_distance

import json

# states - maybe to change later
IDLE = "IDLE" # in warehouse and free
DELIVERING = "DELIVERING" # in route to deliver
RETURNING = "RETURNING" # in route to warehouse

class FSMBehav(FSMBehaviour):
    async def on_start(self):
        pass
    async def on_end(self):
        await self.agent.stop()

class Idle(State):
    async def run(self):
        print("[STATE] Idle")
        to = self.agent.closest_warehouse() + "@localhost"
        msg = Message(to=to)
        msg.body = "I'm ready to deliver!"
        await self.send(msg)
        # message = await self.receive(timeout=5)
        # TODO: parse message and start delivering
        self.set_next_state(DELIVERING)

class Delivering(State):
    async def run(self):
        print("[STATE] Delivering")
        self.set_next_state(RETURNING)

class Returning(State):
    async def run(self):
        print("[STATE] Returning")
        
class DroneAgent(Agent):
    class MyBehav(CyclicBehaviour):
        async def on_start(self):
            pass
            # print(f"[{self.agent.jid}] MyBehav started")
        
        async def run(self):
            # print(f"[{self.agent.jid}] MyBehav running")
            # send message to warehouse - using first warehouse for now
            to = self.agent.closest_warehouse() + "@localhost"
            msg = Message(to=to)
            msg.set_metadata("performative", "inform")
            msg.body = json.dumps({
                "id": self.agent.id,
                "capacity": self.agent.max_capacity,
                "autonomy": self.agent.max_autonomy,
                "velocity": self.agent.velocity
            })
            
            await self.send(msg)
            message = await self.receive(timeout=5)
            # print(f"[{self.agent.jid}] Received message: {message.body}")
            self.kill(exit_code=10)
            
        async def on_end(self):
            print(f"[{self.agent.jid}] MyBehav ended")
            await self.agent.stop()
    

    
    def __init__(self, id, jid, password, initialPos, capacity = 0, autonomy = 0, velocity = 0, warehouse_positions = {}):
        super().__init__(jid, password)
        self.id = id
        self.max_capacity : float = capacity # in kg
        self.max_autonomy : float = autonomy # in meters
        self.velocity : float = velocity # in m/s
        
        self.curr_capacity : float = 0.0
        self.curr_autonomy : float = autonomy
        
        self.warehouse_positions = warehouse_positions
        self.position = {
            "latitude": warehouse_positions[initialPos]["latitude"],
            "longitude": warehouse_positions[initialPos]["longitude"]
        } 
        
        self.tracking_orders = []

    def closest_warehouse(self):
        min_dist = float('inf')
        closest = None
        for warehouse in self.warehouse_positions:
            dist = haversine_distance(
                self.position['latitude'],
                self.position['longitude'],
                self.warehouse_positions[warehouse]['latitude'],
                self.warehouse_positions[warehouse]['longitude']
            )
            if dist < min_dist:
                min_dist = dist
                closest = warehouse
        print(f"Closest warehouse: {closest}")
        return closest

    async def setup(self):
        print(f"{self.id} - [SETUP]")
        b = self.MyBehav()
        self.add_behaviour(b)
        
        # fsm = FSMBehaviour()
        # fsm.add_state(name=IDLE, state=Idle(), initial=True)
        # fsm.add_state(name=DELIVERING, state=Delivering())
        # fsm.add_state(name=RETURNING, state=Returning())
        # fsm.add_transition(source=IDLE, dest=DELIVERING)
        # fsm.add_transition(source=DELIVERING, dest=RETURNING)
        # self.add_behaviour(fsm) # template in doubt for now, various templates should be used in different states in the state machine

    def __str__(self) -> str:
        return "{} - Drone with capacity {} and autonomy {}"\
            .format(str(self.id), self.max_capacity, self.max_capacity, 
                    self.velocity, self.warehouse_positions)
    
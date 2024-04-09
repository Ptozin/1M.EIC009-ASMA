from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
from misc.distance import haversine_distance

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
        
class DroneParameters:
    def __init__(self, capacity, autonomy, velocity, latitude, longitude):
        self.capacity = capacity
        self.autonomy = autonomy
        self.velocity = velocity
        self.position = {
            "latitude": latitude,
            "longitude": longitude
        } 

class DroneAgent(Agent):
    def __init__(self, id, jid, password, initialPos, capacity = 0, autonomy = 0, velocity = 0, warehouse_positions = {}):
        super().__init__(jid, password)
        self.id = id
        
        self.parameters = DroneParameters(
            capacity, 
            autonomy, 
            velocity, 
            warehouse_positions[initialPos]["latitude"], 
            warehouse_positions[initialPos]["longitude"]
        )

        self.curr_weight = 0
        self.curr_autonomy = autonomy
        self.tracking_orders = []
        
        self.warehouse_positions = warehouse_positions

    def closest_warehouse(self):
        min_dist = float('inf')
        closest = None
        for warehouse in self.warehouse_positions:
            dist = haversine_distance(
                self.curr_coords[0],
                self.curr_coords[1],
                self.warehouse_positions[warehouse][0],
                self.warehouse_positions[warehouse][1]
            )
            if dist < min_dist:
                min_dist = dist
                closest = warehouse
        return closest

    async def setup(self):
        fsm = FSMBehaviour()
        fsm.add_state(name=IDLE, state=Idle(), initial=True)
        fsm.add_state(name=DELIVERING, state=Delivering())
        fsm.add_state(name=RETURNING, state=Returning())
        fsm.add_transition(source=IDLE, dest=DELIVERING)
        fsm.add_transition(source=DELIVERING, dest=RETURNING)
        self.add_behaviour(fsm) # template in doubt for now, various templates should be used in different states in the state machine

    def __str__(self) -> str:
        return "Drone {} with capacity {} and autonomy {}".format(str(self.jid), self.capacity, self.autonomy, self.velocity, self.initialPos)
    
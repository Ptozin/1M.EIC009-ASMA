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
        
        # TODO: get coords (not hardcoded)
        self.warehouse_data = {
            "center1": (18.994237, 72.825553),
            "center2": (18.927584, 72.832585)
        }
        self.curr_coords = self.warehouse_data[self.initialPos]

    def closest_warehouse(self):
        min_dist = float('inf')
        closest = None
        for warehouse in self.warehouse_data:
            dist = haversine_distance(
                self.curr_coords[0],
                self.curr_coords[1],
                self.warehouse_data[warehouse][0],
                self.warehouse_data[warehouse][1]
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
    
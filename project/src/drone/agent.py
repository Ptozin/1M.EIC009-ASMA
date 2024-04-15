# ----------------------------------------------------------------------------------------------

import json
from spade.agent import Agent

from src.order import DeliveryOrder
from parameters import DroneParameters
from misc.log import Logger
from behaviours.available import AvailableBehaviour

# ----------------------------------------------------------------------------------------------

class DroneAgent(Agent):
    def __init__(self, id, jid, password, initialPos, capacity = 0, autonomy = 0, velocity = 0, warehouse_positions = {}) -> None:
        super().__init__(jid, password)
        self.total_orders : list[DeliveryOrder] = [] 
        self.curr_orders : list[DeliveryOrder] = []
        self.curr_order : DeliveryOrder = None
        
        self.required_autonomy : float = 0.0
        
        self.warehouse_positions : dict = warehouse_positions    
        self.next_warehouse_id : dict = None
        self.distance_to_next_warehouse = 0.0
        self.final_order_choices : dict = {}
    
        self.position = {
            "latitude": warehouse_positions[initialPos]["latitude"],
            "longitude": warehouse_positions[initialPos]["longitude"]
        } 
        
        self.params = DroneParameters(id, capacity, autonomy, velocity)
        
        self.logger = Logger(filename = id)
        
    async def setup(self) -> None:
        """
        Agent's setup method. It adds the IdleBehav behaviour.
        """
        print(f"{self.params.id} - [SETUP]")
        self.add_behaviour(AvailableBehaviour())

    def __str__(self) -> str:
        return str(self.params)

    def __repr__(self) -> str:
        return json.dumps({
            "id": self.params.id,
            "capacity": self.params.max_capacity,
            "autonomy": self.params.max_autonomy,
            "velocity": self.params.velocity,
        })     
        
# ----------------------------------------------------------------------------------------------

    def available_warehouses(self) -> bool:
        """
        Method to check if there are any warehouses available.

        Returns:
            bool: True if there are available warehouses, False otherwise.
        """
        return len(self.warehouse_positions) > 0
    
    def remove_warehouse(self, warehouse_id : str) -> None:
        """
        Method to remove a warehouse from the available list.

        Args:
            warehouse_id (str): The id of the warehouse to remove.
        """
        self.warehouse_positions.pop(warehouse_id)
        
# ----------------------------------------------------------------------------------------------
from warehouse.agent import WarehouseAgent
from drone.agent import DroneAgent
from flask_socketio import SocketIO
import spade
from asyncio import sleep

class DeliveryLogic:
    def __init__(self, delivery_drones : list[dict], warehouses : list[dict], socketio : SocketIO) -> None:
        
        # Create warehouse agents
        self.warehouses : list[WarehouseAgent] = [
            WarehouseAgent(
                warehouse["id"],
                warehouse["jid"],
                warehouse["password"],
                warehouse["latitude"],
                warehouse["longitude"],
                orders,
                socketio
            ) for warehouse, orders in warehouses
        ]
        
        # Store warehouse positions for drone navigation
        warehouse_positions : dict = {}
        for warehouse, _ in warehouses:
            warehouse_positions[warehouse["id"]] = {
                "latitude": warehouse["latitude"],
                "longitude": warehouse["longitude"],
                "jid": warehouse["jid"]
            }
                
        # Create drone agents
        self.delivery_drones = [
            DroneAgent(
                drone["id"],
                drone["jid"],
                drone["password"],
                drone["initialPos"],
                drone["capacity"],
                drone["autonomy"],
                drone["velocity"],
                warehouse_positions.copy(), # Need to copy the dictionary to avoid reference issues
                socketio
            ) for drone in delivery_drones
        ]

        # Start the agents and pray they work as expected.
        spade.run(self.start_logic())
        
    async def start_logic(self):
        for warehouse in self.warehouses:
            await warehouse.start()
            
        await sleep(2) # Wait for the warehouses to be ready
        
        for drone in self.delivery_drones:
            await drone.start()

        for drone in self.delivery_drones:
            await spade.wait_until_finished(drone)
            
        for drone in self.delivery_drones:
            await drone.stop()
        for warehouse in self.warehouses:
            await warehouse.stop()
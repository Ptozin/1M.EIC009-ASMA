from warehouse_agent import WarehouseAgent
from drone_agent import DroneAgent
import spade

class DeliveryLogic:
    def __init__(self, delivery_drones, warehouses):
        
        # Create warehouse agents
        self.warehouses = [
            WarehouseAgent(
                warehouse["id"],
                warehouse["jid"],
                warehouse["password"],
                warehouse["latitude"],
                warehouse["longitude"],
                orders
            ) for warehouse, orders in warehouses
        ]
        
        # Store warehouse positions for drone navigation
        warehouse_positions = {}
        for warehouse, _ in warehouses:
            warehouse_positions[warehouse["id"]] = {
                "latitude": warehouse["latitude"],
                "longitude": warehouse["longitude"]
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
                warehouse_positions
            ) for drone in delivery_drones
        ]

        # Start the agents and pray they work as expected.
        spade.run(self.start_logic())

    async def start_logic(self):
        # basic test
        for drone in self.delivery_drones:
            await drone.start()
            drone.web.start(hostname="localhost", port=10000)
            break

        for warehouse in self.warehouses:
            await warehouse.start()
            break
        
        drone = self.delivery_drones[0]
        await spade.wait_until_finished(drone)
        await drone.stop()
        
    def __exit__(self, exc_type, exc_value, traceback):
        for drone in self.delivery_drones:
            drone.stop()
        for warehouse in self.warehouses:
            warehouse.stop()

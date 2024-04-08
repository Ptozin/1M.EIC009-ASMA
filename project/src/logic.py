import warehouse_agent
import drone_agent
import spade

class DeliveryLogic:
    def __init__(self, delivery_drones, warehouses):
        """
        The warehouses & orders data should be in the following format:
        ```
        [
            (
                { // warehouse data
                    "id": str,
                    "latitude": float,
                    "longitude": float,
                    "weight": int,
                },
                [ // orders data
                    {
                        "id": str,
                        "latitude": float,
                        "longitude": float,
                        "weight": int,
                    },
                    ...
                ]
            ),
            ...
        ]
        ```
        """

        self.delivery_drones = [
            drone_agent.DroneAgent(
                drone["id"],
                drone["capacity"],
                drone["autonomy"],
                drone["velocity"],
                drone["initialPos"]
            ) for drone in delivery_drones
        ]

        self.warehouses = [
            warehouse_agent.WarehouseAgent(
                warehouse["id"],
                warehouse["latitude"],
                warehouse["longitude"],
                orders
            ) for warehouse, orders in warehouses
        ]

        """
        Now we can start the agents and pray they work as expected.
        """
        spade.run(self.start_agents())

    async def start_agents(self):
        for drone in self.delivery_drones:
            await drone.start()
        for warehouse in self.warehouses:
            await warehouse.start()
        

    def __exit__(self, exc_type, exc_value, traceback):
        for drone in self.delivery_drones:
            drone.stop()
        for warehouse in self.warehouses:
            warehouse.stop()

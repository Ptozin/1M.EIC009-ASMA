import warehouse_agent
import drone_agent

class DeliveryLogic:
    def __init__(self, delivery_drones, warehouses, orders):

        """
        The warehouses/orders data should be in the following format:
        {
            "id": str,
            "latitude": float,
            "longitude": float,
            "weight": int,
        }
        """

        print(delivery_drones)
        #print(warehouses)
        #print(orders)

    def get_data(self):
        return self.data
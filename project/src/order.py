from typing import Any

STATUS = {
    "IDLE": 0,
    "DELIVERING": 1,
    "DELIVERED": 2
}

class DeliveryOrder:
    """
    DeliveryOrder class to represent a delivery order.
    In a future implementation, in a given time interval, each delivery current position will be updated
    to be displayed in a map.
    """
    def __init__(self, id, origin_lat, origin_long, dest_lat, dest_long, weight) -> None:
        self.id : str = id
        self.weight : int = weight
        
        self.start_position : dict = {
            "latitude": origin_lat,
            "longitude": origin_long
        }
        self.destination_position : dict = {
            "latitude": dest_lat,
            "longitude": dest_long
        }
        
        self.order_status : int = STATUS["IDLE"]
    
    def get_order_status(self) -> str:
        return self.order_status
    
    # State machine of the order, according to the 3 possible status - idle, delivering and delivered
    def update_status(self) -> None:
        if self.order_status == STATUS["DELIVERED"]:
            print(f"Order {self.id} - Already delivered")
            return
        elif self.order_status == STATUS["IDLE"]:
            self.order_status = STATUS["DELIVERING"]
        elif self.order_status == STATUS["DELIVERING"]:
            self.order_status = STATUS["DELIVERED"]

    def __str__(self) -> str:
        return "Order {} - from {} to {} with weight {}"\
            .format(self.id, (self.start_position['latitude'], 
                              self.start_position['longitude']), 
                            (self.destination_position['latitude'], 
                            self.destination_position['longitude']), 
                    self.weight)
            
    def __repr__(self) -> str:
        return self.__str__()
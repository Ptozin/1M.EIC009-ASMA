from typing import Any
import json

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
    def __init__(self, id : str, origin_lat : float, origin_long : float, dest_lat : float, dest_long : float, weight : int) -> None:
        """
        DeliveryOrder class to represent a delivery order.
        
        Args:
            id (str): The order id.
            origin_lat (float): The latitude of the origin position.
            origin_long (float): The longitude of the origin position.
            dest_lat (float): The latitude of the destination position.
            dest_long (float): The longitude of the destination position.
            weight (int): The weight of the order.
        """
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
    
    #def get_order_status(self) -> str:
    #    return self.order_status
    
    # State machine of the order, according to the 3 possible status - idle, delivering and delivered
    #def update_status(self) -> None:
    #    if self.order_status == STATUS["DELIVERED"]:
    #        print(f"Order {self.id} - Already delivered")
    #        return
    #    elif self.order_status == STATUS["IDLE"]:
    #        self.order_status = STATUS["DELIVERING"]
    #    elif self.order_status == STATUS["DELIVERING"]:
    #        self.order_status = STATUS["DELIVERED"]

    def get_order_destination_position(self) -> dict:
        """
        Get the order_id with destination position.

        Returns:
            dict: The order_id with destination position.
        """
        return {self.id : self.destination_position}
    
    def __str__(self) -> str:
        return "Order {} - from {} to {} with weight {}"\
            .format(self.id, (self.start_position['latitude'], 
                              self.start_position['longitude']), 
                            (self.destination_position['latitude'], 
                            self.destination_position['longitude']), 
                    self.weight)        
            
    def __repr__(self) -> str:
        return json.dumps({
            "id": self.id,
            "origin_lat": self.start_position['latitude'],
            "origin_long": self.start_position['longitude'],
            "dest_lat": self.destination_position['latitude'],
            "dest_long": self.destination_position['longitude'],
            "weight": self.weight
        })
        
    def __gt__(self, weight : float) -> bool:
        return self.weight > weight
    
    def __lt__(self, weight : float) -> bool:
        return self.weight < weight
    
    def __eq__(self, weight : float) -> bool:
        return self.weight == weight
    
    def __le__(self, weight : float) -> bool:
        return self.weight <= weight
    
    def __ge__(self, weight : float) -> bool:
        return self.weight >= weight
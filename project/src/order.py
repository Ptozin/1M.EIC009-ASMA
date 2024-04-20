from typing import Any
import json

STATUS = {
    "FREE": False,
    "DELIVERED": True,
    "TAKEN": True
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
        
        self.order_status : bool = STATUS["FREE"]
        
    def mark_as_taken(self) -> None:
        """
        Mark the order as taken by a drone.
        """
        if self.order_status == STATUS["FREE"]:
            self.order_status = STATUS["TAKEN"]
        else:
            raise Exception("Order is not available to be taken.")

    def mark_as_delivered(self) -> None:
        """
        Mark the order as delivered by a drone.
        """
        if self.order_status == STATUS["TAKEN"]:
            self.order_status = STATUS["DELIVERED"]
        else:
            raise Exception("Order cannot be delivered as it hasn't been taken.")

    def is_available(self) -> bool:
        """
        Check if the order is available to be assigned to a drone.
        
        Returns:
            bool: True if the order is available, False otherwise.
        """
        return self.order_status == STATUS["FREE"]
    
    def get_order_for_visualization(self) -> dict:
        """
        Get the order formatted for visualization.

        Returns:
            dict: The order formatted for visualization.
        """
        return {
            "id": self.id,
            "latitude": self.destination_position['latitude'],
            "longitude": self.destination_position['longitude'],
            "status": self.order_status,
            "type": "order"
        }

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
    
    def __eq__(self, id : str) -> bool:
        return self.id == id
    
    def __le__(self, weight : float) -> bool:
        return self.weight <= weight
    
    def __ge__(self, weight : float) -> bool:
        return self.weight >= weight
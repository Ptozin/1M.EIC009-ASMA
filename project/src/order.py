
class DeliveryOrder:
    """
    DeliveryOrder class to represent a delivery order.
    In a future implementation, in a given time interval, each delivery current position will be updated
    to be displayed in a map.
    """
    def __init__(self, id, origin_lat, origin_long, dest_lat, dest_long, weight) -> None:
        self.id = id
        self.position = (origin_lat, origin_long)
        self.destination = (dest_lat, dest_long)
        self.weight = weight

    def __str__(self) -> str:
        return "Order {} from {} to {} with weight {}".format(self.id, self.position, self.destination, self.weight)
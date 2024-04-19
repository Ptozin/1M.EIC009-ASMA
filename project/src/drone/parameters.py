# ----------------------------------------------------------------------------------------------

import json

# ----------------------------------------------------------------------------------------------

class DroneParameters:
    def __init__(self, id : str, capacity : int, autonomy : float , velocity : float) -> None:
        # ---- Metrics ----
        self.__total_trips : int = 0 # TODO: update this later, as it should be 0
        self.total_distance : float = 0.0 # Can be converted to time with velocity
        self.metrics_total_distance : float = 0.0 # Same value as total_distance, but is updated to be used in visualization
        self.__min_distance_on_trip : float = float('inf') # Measured in meters
        self.__max_distance_on_trip : float = 0.0 # Measured in meters
        self.__avg_distance_on_trip : float = 0.0 # Measured in meters
        self.orders_delivered : int = 0 # Total Orders Delivered
        self.__orders_to_deliver : int = 0 # Number of orders carried by the drone on the current trip
        self.__occupiance_rate : float = 0.0 # Average Occupiance Rate Per Trip, calculated with `orders_delivered / total_trips`
        self.__energy_consumption : float = 0.0 # Total Energy Consumption, calculated with `total_distance / autonomy`
        self.__distance_on_prev_trip : float = 0.0 # Distance of the previous trip

        # --- Parameters ---
        self.id : str = id
        self.velocity : float = velocity # in m/s
        self.max_capacity : int = capacity # in kg
        self.max_autonomy : float = autonomy # in meters
        self.curr_capacity : int = 0
        self.curr_autonomy : float = autonomy
        self.__path : list[dict] = [] # List of trips with their respective coordinates. E.g [{"order_X": {"latitude": 37.7749, "longitude": -122.4194}}]
        
        test = [
            {"order_X": {"latitude": 37.7749, "longitude": -122.4194}},
            {"order_Y": {"latitude": 37.7749, "longitude": -122.4194}},
            {"center_Z": {"latitude": 37.7749, "longitude": -122.4194}},            
        ]
        
    def refill_autonomy(self, warehouse : dict) -> None:
        """
        Method to refill the drone's autonomy.
        Called when the drone returns to the warehouse.
        Updates the previous trip distance.
        """
        self.curr_autonomy = self.max_autonomy
        
        
        self.__path.append(warehouse)
        
        self.__total_trips += 1
        if (self.__distance_on_prev_trip > 0):
            self.add_trip(self.__distance_on_prev_trip)

# ----------------------------------------------------------------------------------------------
    
    def add_trip(self, distance : float) -> None:
        """
        Method to add a trip to the drone's metrics.
        Only called when the drone returns to the warehouse.

        Args:
            distance (float): The distance of the trip.
        """
        
        # TODO: this cannot be like this anymore, change it
        
        
        self.total_distance += distance
        self.__min_distance_on_trip = min(self.__min_distance_on_trip, distance)
        self.__max_distance_on_trip = max(self.__max_distance_on_trip, distance)
        self.__avg_distance_on_trip = self.total_distance / self.__total_trips
        self.__occupiance_rate = self.orders_delivered / self.__total_trips
        self.__energy_consumption = self.total_distance / self.max_autonomy
        
        self.__distance_on_prev_trip = 0
        
    def add_order(self, capacity : int) -> None:
        """
        Method to add an order to the drone's metrics.

        Args:
            capacity (int): The capacity of the order.
            destination (dict): The destination of the order with its coordinates.
        """
        self.__orders_to_deliver += 1
        self.curr_capacity += capacity
    
    def drop_order(self, capacity : int, distance_covered : int, destination : dict) -> None:
        """
        Method to drop an order from the drone's metrics.

        Args:
            capacity (int): The capacity of the order.
        """
        self.__distance_on_prev_trip += distance_covered
        self.__orders_to_deliver -= 1
        self.orders_delivered += 1
        self.curr_capacity -= capacity
        self.__path.append(destination)
        
    def update_distance(self, distance : float) -> None:
        """
        Method to update the distance covered by the drone.
        For visualization purposes only.
        """
        self.metrics_total_distance += distance
        
    def __str__(self) -> str:
        return "{} - Drone with capacity ({}/{}) and autonomy ({}/{}) delivering {} orders, with {} completed orders"\
            .format(self.id, self.curr_capacity, self.max_capacity, 
                    round(self.curr_autonomy,2), self.max_autonomy, 
                    self.__orders_to_deliver, self.orders_delivered)
            
    def __repr__(self) -> str:
        return json.dumps({
            "id":       self.id,
            "capacity": self.max_capacity,
            "autonomy": self.max_autonomy,
            "velocity": self.velocity,
        })
        
# ----------------------------------------------------------------------------------------------
        
    def metrics(self, orders_id : list[str]) -> None:
        """
        Method to print the final metrics of the drone.
        """
        self.__occupiance_rate = self.orders_delivered / self.__total_trips
        return "{} Metrics - {}"\
              .format(self.id, 
                        [
                            {"Total Trips": self.__total_trips},
                            {"Total Distance": round(self.total_distance,2)},
                            {"Min Distance": round(self.__min_distance_on_trip,2)},
                            {"Max Distance": round(self.__max_distance_on_trip,2)},
                            {"Avg Distance": round(self.__avg_distance_on_trip,2)},
                            {"Orders Delivered": self.orders_delivered},
                            {"Occupiance Rate": round(self.__occupiance_rate,2)},
                            {"Energy Consumption": str(round(self.__energy_consumption * 100,2)) + "%"},
                            {"Orders": orders_id}
                        ]
                    )
              
    def store_results(self) -> None:
        """
        Method to store the final metrics of the drone and of its trips
        """
        with open(f"logs/{self.id}.json", "w") as f:
            json.dump(
                { 
                    "Drone_parameters": {
                        "id":       self.id,
                        "capacity": self.max_capacity,
                        "autonomy": self.max_autonomy,
                        "velocity": self.velocity,
                    },
                    "Metrics":
                    {
                        "Total Trips": self.__total_trips,
                        "Total Distance": round(self.total_distance,2),
                        "Min Distance": round(self.__min_distance_on_trip,2),
                        "Max Distance": round(self.__max_distance_on_trip,2),
                        "Avg Distance": round(self.__avg_distance_on_trip,2),
                        "Orders Delivered": self.orders_delivered,
                        "Occupiance Rate": round(self.__occupiance_rate,2),
                        "Energy Consumption": str(round(self.__energy_consumption * 100,2)) + "%"
                    },
                    "Path": self.__path
                }, 
                f,
                indent=4)
              
# ----------------------------------------------------------------------------------------------
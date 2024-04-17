# ----------------------------------------------------------------------------------------------

import numpy as np
from collections import deque

from order import DeliveryOrder

# ----------------------------------------------------------------------------------------------

class OrdersMatrix:
    """
    OrdersMatrix class to represent a matrix of orders.
    
    Args:
        inventory (dict[str, DeliveryOrder]): The inventory of orders.
        divisions (int): The number of divisions for the matrix.
        capacity_multiplier (int): The capacity multiplier for the drones.
        
    Attributes:
        corners (list): The corners of the matrix.
        divisions (int): The number of divisions for the matrix.
        capacity_multiplier (int): The capacity multiplier for the drones.
        matrix (np.array): The matrix of orders.
    """
    def __init__(self, inventory : dict[str, DeliveryOrder], divisions : int = 5, capacity_multiplier : int = 3) -> None:
        self.corners : list = self.__setup(inventory)
        self.divisions : int = divisions
        self.capacity_multiplier : int = capacity_multiplier
        
        self.matrix : np.array = np.empty((self.divisions, self.divisions), dtype=object)
        
        self.__prev_order_selection : list[DeliveryOrder] = None
        self.__prev_coordinates = {"latitude": 0, "longitude": 0}
        
        for i in range(self.divisions):
            for j in range(self.divisions):
                self.matrix[i, j] = []
                
    # ----------------------------------------------------------------------------------------------            
                
    def __setup(self, inventory) -> list:
        # Extract the minimum and maximum coordinates for the destination positions, and add a small buffer
        buffer = 0.01
        
        min_dest_lat = min(order.destination_position["latitude"] for order in inventory.values()) - buffer
        max_dest_lat = max(order.destination_position["latitude"] for order in inventory.values()) + buffer
        min_dest_long = min(order.destination_position["longitude"] for order in inventory.values()) - buffer
        max_dest_long = max(order.destination_position["longitude"] for order in inventory.values()) + buffer

        bottom_left = (min_dest_lat, min_dest_long)
        bottom_right = (min_dest_lat, max_dest_long)
        top_left = (max_dest_lat, min_dest_long)
        top_right = (max_dest_lat, max_dest_long)
        
        return [bottom_left, bottom_right, top_left, top_right]
    
    # ----------------------------------------------------------------------------------------------
    
    def calculate_cell_index(self, latitude : float, longitude : float) -> tuple:        
        # Extract the coordinates of the top left corner
        top_left = self.corners[2]
        
        # Calculate the distance between the destination and the top left corner
        x_distance = longitude - top_left[1]
        y_distance = top_left[0] - latitude
        
        # Calculate the distance between the top left and top right corners
        x_corner_dist = self.corners[3][1] - self.corners[2][1]
        y_corner_dist = self.corners[2][0] - self.corners[0][0]
        
        # Calculate the cell index for the order
        j = int(x_distance * self.divisions / x_corner_dist)
        i = int(y_distance * self.divisions / y_corner_dist)
        
        return i, j
    
    # ----------------------------------------------------------------------------------------------
    
    def populate_matrix(self, inventory : dict[str, DeliveryOrder]) -> None:
        for order in inventory.values():
            # Calculate the cell index for the order
            i, j = self.calculate_cell_index(order.destination_position["latitude"], order.destination_position["longitude"])
            
            # Store the order in the orders matrix
            self.matrix[i, j].append(order)
            
            # print(f"Order {order.id} with {order.destination_position} is stored in cell ({i}, {j})")
    
    # ----------------------------------------------------------------------------------------------
    
    def select_orders(self, latitude: float, longitude: float, capacity: int) -> list[DeliveryOrder]:
        if self.__prev_order_selection is not None \
            and latitude == self.__prev_coordinates["latitude"] \
            and longitude == self.__prev_coordinates["longitude"]:
            return self.__prev_order_selection
        # Calculate the cell index for the order
        i, j = self.calculate_cell_index(latitude, longitude)
        
        # Drones will receive 3 times the capacity, so that they can choose the best orders
        total_orders_capacity = capacity * self.capacity_multiplier
        
        orders: list[DeliveryOrder] = []
        
        # Define directions: right, down, left, up
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        # Initialize a queue for spiral traversal
        queue = deque([(i, j)])
        
        # Initialize a set to keep track of visited cells
        visited = set([(i, j)])
        
        # Initialize total weight of orders retrieved
        total_weight = 0
        
        # Perform spiral traversal to retrieve orders
        while queue:
            x, y = queue.popleft()
            
            print(f"Retrieving orders from cell ({x}, {y})")
            
            # Retrieve orders in the current cell
            cell_orders = self.matrix[x, y]
            
            # Calculate the weight of orders in the current cell
            cell_weight = sum(order.weight for order in cell_orders)
            
            orders.extend(cell_orders)
            
            # If adding orders from this cell exceeds the total capacity, stop traversal
            if total_weight + cell_weight > total_orders_capacity:
                break
            
            # Add orders from this cell to the list of retrieved orders
            total_weight += cell_weight
            
            # Explore neighboring cells in all directions
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                # Check if the neighboring cell is within bounds and not visited
                if 0 <= nx < self.divisions and 0 <= ny < self.divisions and (nx, ny) not in visited:
                    queue.append((nx, ny))
                    visited.add((nx, ny))
        
        # Store the previous order selection and coordinates
        self.__prev_order_selection = orders
        self.__prev_coordinates = {"latitude": latitude, "longitude": longitude}
        
        return orders
    
    # ----------------------------------------------------------------------------------------------
    
    def remove_orders(self, *, orders: list[DeliveryOrder]) -> None:
        """
        Remove orders from the matrix.
        Only called when a Drone accepts an offer made by the warehouse.
        Clears the previous order selection.

        Args:
            orders (list[DeliveryOrder]): The list of orders to be removed.
        """
        orders_id = [order.id for order in orders]
        
        self.remove_orders(orders_id=orders_id)
        
    # ----------------------------------------------------------------------------------------------    
    
    def remove_orders(self, *, orders_id: list[str]) -> None:
        """
        Remove orders from the matrix.
        Only called when a Drone accepts an offer made by the warehouse.
        Clears the previous order selection.

        Args:
            orders_id (list[str]): The list of order ids to be removed.
        """
        for i in range(self.divisions):
            for j in range(self.divisions):
                self.matrix[i, j] = [order for order in self.matrix[i, j] if order.id not in orders_id]
                
        self.__prev_order_selection = None
        self.__prev_coordinates = {"latitude": 0, "longitude": 0}

# ----------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------

import numpy as np
from collections import deque

from order import DeliveryOrder

from time import time

# ----------------------------------------------------------------------------------------------

class OrdersMatrix:
    """
    OrdersMatrix class to represent a matrix of orders.
    
    Args:
        inventory (dict[str, DeliveryOrder]): The inventory of orders.
        divisions (int): The number of divisions for the matrix.
        capacity_multiplier (int): The capacity multiplier for the drones.
        warehouse_position (dict): The position of the warehouse.
        
    Attributes:
        corners (list): The corners of the matrix.
        divisions (int): The number of divisions for the matrix.
        capacity_multiplier (int): The capacity multiplier for the drones.
        matrix (np.array): The matrix of orders.
    """
    def __init__(self, inventory : dict[str, DeliveryOrder], divisions : int = 5, capacity_multiplier : int = 3, warehouse_position : dict = {}) -> None:
        self.corners : list = self.__setup(inventory, warehouse_position)
        self.divisions : int = divisions
        self.capacity_multiplier : int = capacity_multiplier
        
        self.matrix : np.array = np.empty((self.divisions, self.divisions), dtype=object)
        
        self.reserved_orders : dict[str, tuple] = {}
        self.reserved_orders_timer : dict[str, float] = {}
        self.__timeout : float = 5.0 # seconds
        
        for i in range(self.divisions):
            for j in range(self.divisions):
                self.matrix[i, j] = []

        self.populate_matrix(inventory)
                
    # ----------------------------------------------------------------------------------------------            
                
    def __setup(self, inventory : dict[str, DeliveryOrder], warehouse_position : dict ) -> list:
        """
        Setup the corners of the matrix.

        Args:
            inventory (dict[str, DeliveryOrder]): The inventory of orders.
            warehouse_position (dict): The position of the warehouse.

        Returns:
            list: The corners of the matrix.
        """
        # Extract the minimum and maximum coordinates for the destination positions, and add a small buffer
        buffer = 0.01
        
        min_dest_lat : float = min(order.destination_position["latitude"] for order in inventory.values()) - buffer
        max_dest_lat : float = max(order.destination_position["latitude"] for order in inventory.values()) + buffer
        min_dest_long : float = min(order.destination_position["longitude"] for order in inventory.values()) - buffer
        max_dest_long : float = max(order.destination_position["longitude"] for order in inventory.values()) + buffer

        min_dest_lat : float = min(min_dest_lat, warehouse_position["latitude"]) - buffer
        max_dest_lat : float = max(max_dest_lat, warehouse_position["latitude"]) + buffer
        min_dest_long : float = min(min_dest_long, warehouse_position["longitude"]) - buffer
        max_dest_long : float = max(max_dest_long, warehouse_position["longitude"]) + buffer

        bottom_left : tuple[float, float] = (min_dest_lat, min_dest_long)
        bottom_right : tuple[float, float] = (min_dest_lat, max_dest_long)
        top_left : tuple[float, float] = (max_dest_lat, min_dest_long)
        top_right : tuple[float, float] = (max_dest_lat, max_dest_long)
        
        return [bottom_left, bottom_right, top_left, top_right]
    
    # ----------------------------------------------------------------------------------------------
    
    def calculate_cell_index(self, latitude : float, longitude : float) -> tuple[int, int]:        
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
    
    def check_timeout(self) -> None:
        """
        Check if the timeout for a reservation has expired.
        If so, undo the reservations of the orders.
        """
        current_time : float = time()
        
        expired_owners = [owner for owner, timer in self.reserved_orders_timer.items() if current_time - timer > self.__timeout]
        for owner in expired_owners:
            self.undo_reservations(owner)
    
    # ----------------------------------------------------------------------------------------------
    
    def select_orders(self, latitude: float, longitude: float, capacity: int, owner : str) -> list[DeliveryOrder]:
        """
        Select orders for a drone based on its capacity and location.

        Args:
            latitude (float): latitude of the drone
            longitude (float): longitude of the drone
            capacity (int): free capacity of the drone

        Returns:
            list[DeliveryOrder]: list of orders selected for the drone. Can be empty.
        """
        
        # Check timeouts before reserving the order
        self.check_timeout()
        
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
            
            # print(f"Retrieving orders from cell ({x}, {y})")
            
            # Retrieve orders in the current cell
            cell_orders = self.matrix[x, y]
            
            # Calculate the weight of orders in the current cell
            cell_weight = sum(order.weight for order in cell_orders)
            
            
            # If adding orders from this cell exceeds the total capacity, stop traversal
            if total_weight + cell_weight > total_orders_capacity:
                for order in cell_orders:
                    if order.weight + total_weight < total_orders_capacity:
                        orders.append(order)
                        total_weight += order.weight
                break
            else:
                orders.extend(cell_orders)
            
            # Add orders from this cell to the list of retrieved orders
            total_weight += cell_weight
            
            # Explore neighboring cells in all directions
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                # Check if the neighboring cell is within bounds and not visited
                if 0 <= nx < self.divisions and 0 <= ny < self.divisions and (nx, ny) not in visited:
                    queue.append((nx, ny))
                    visited.add((nx, ny))
        
        # Now, reserve the orders for the drone
        for order in orders:
            self.reserve_order(
                order.destination_position["latitude"], 
                order.destination_position["longitude"], 
                order.id, 
                owner
            )
        
        return orders
    
    # ----------------------------------------------------------------------------------------------

    def reserve_order(self, lat : float, long : float, order_id : str, owner : str) -> None:
        """
        Reserve an order in the matrix.
        Only called when a Drone accepts an offer made by the warehouse.

        Args:
            lat (float): The latitude of the order to be reserved.
            long (float): The longitude of the order to be reserved.
            order_id (str): The id of the order to be reserved.
        """
        
        i, j = self.calculate_cell_index(lat, long)
        
        for order in self.matrix[i, j]:
            if order.id == order_id:
                self.matrix[i, j].remove(order)
                
                if owner not in self.reserved_orders:
                    self.reserved_orders[owner] = []
                self.reserved_orders[owner].append((order, i, j))
                break
            
        # Set the timer for the owner
        self.reserved_orders_timer[owner] = time()

    # ----------------------------------------------------------------------------------------------
    
    def remove_order(self, order_id : str, owner : str) -> None:
        """
        Remove an order from the matrix.
        Only called when a Drone delivers an order.

        Args:
            order_id (str): The id of the order to be removed.
            owner (str): The id of the owner of the order.
        """
                
        for order, i, j in self.reserved_orders[owner]:
            if order.id == order_id:
                self.reserved_orders[owner].remove((order, i, j))
                break
                            
    # ----------------------------------------------------------------------------------------------
    
    def undo_reservations(self, owner : str) -> None:
        """
        Undo the reservations of orders in the matrix.
        Called when a Drone refuses an offer made by the warehouse.
        Called when the timeout for a reservation expires.
        Called after removing all the orders for the owner, to undo the reservations of unaccepted orders.

        Args:
            owner (str): The id of the owner of the order.
        """
        
        if owner not in self.reserved_orders:
            return
        
        for order, i, j in self.reserved_orders[owner]:
            self.matrix[i, j].append(order)
            
        del self.reserved_orders[owner]
        del self.reserved_orders_timer[owner]

# ----------------------------------------------------------------------------------------------

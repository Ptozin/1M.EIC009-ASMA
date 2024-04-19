from math import radians, cos, sin, asin, sqrt, atan2, degrees

EARTH_RADIUS = 6_371 # Radius of earth in kilometers.

def haversine_distance(lat1 : float , lon1 : float, lat2 : float, lon2 : float, unit : str = "m") -> float:
    """
    Args:
        lat1 (float): Latitude of the first point.
        lon1 (float): lonitude of the first point.
        lat2 (float): Latitude of the second point.
        lon2 (float): lonitude of the second point.
        unit (str, optional): Unit of the distance. Can be "km" or "m". Defaults to "m".

    Returns:
        float: Distance between the two points in the specified unit.
    """
    R = EARTH_RADIUS if unit == "km" else EARTH_RADIUS * 1_000

    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
    c = 2*asin(sqrt(a))
    
    return R * c

def next_position(curr_lat : float, curr_lon : float, target_lat : float, target_lon : float, velocity : float) -> tuple[dict, float]:
    """
    Args:
        curr_lat (float): Current latitude of the drone.
        curr_lon (float): Current longitude of the drone.
        target_lat (float): Latitude of the target point.
        target_lon (float): Longitude of the target point.
        velocity (float): Velocity of the drone.
        
    Returns:
        tuple[dict, float]: The next position of the drone and the distance to the target point.
    """
    
    distance = haversine_distance(curr_lat, curr_lon, target_lat, target_lon)
    if distance == 0.0:
        return {
            "latitude": target_lat,
            "longitude": target_lon
        }, distance
        
    distance_covered = velocity if distance > velocity else distance 
        
    fraction = min(velocity / distance, 1.0)
    new_lat = curr_lat + fraction * (target_lat - curr_lat)
    new_lon = curr_lon + fraction * (target_lon - curr_lon)
    return {
        "latitude": new_lat,
        "longitude": new_lon
    }, distance_covered
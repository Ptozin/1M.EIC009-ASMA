from math import radians, cos, sin, asin, sqrt

def haversine_distance(lat1 : float , lon1 : float, lat2 : float, lon2 : float, unit : str = "km") -> float:
    """
    Args:
        lat1 (float): Latitude of the first point.
        lon1 (float): Longitude of the first point.
        lat2 (float): Latitude of the second point.
        lon2 (float): Longitude of the second point.
        unit (str, optional): Unit of the distance. Can be "km" or "m". Defaults to "km".

    Returns:
        float: Distance between the two points in the specified unit.
    """
    R = 6_371 if unit == "km" else 6_371_000 # Radius of earth in kilometers or meters.

    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
    c = 2*asin(sqrt(a))
    
    return R * c

def __test():
    # Test the haversine function
    lat1 = 19.017584
    lon1 = 72.922585
    lat2 = 18.994237
    lon2 = 72.825553
     
    print(haversine_distance(lat1, lon1, lat2, lon2), "KM")
    # Expected output: 10.526425869824223 KM
    
    
if __name__ == "__main__":
    __test()
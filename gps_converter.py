"""
GPS Coordinate Conversion Utilities

Converts trajectory coordinates (meters) to GPS lat/lon using:
- Haversine formula for geospatial calculations
- Flat-earth approximation for short distances (<500m)
"""

import math


def calculate_new_gps(start_lat, start_lon, distance_meters, bearing_degrees):
    """
    Calculate new GPS coordinates given a start point, distance, and bearing.
    
    Uses spherical Earth model (accurate for golf shot distances).
    
    Args:
        start_lat: Starting latitude (decimal degrees)
        start_lon: Starting longitude (decimal degrees)
        distance_meters: Distance to travel (meters)
        bearing_degrees: Direction to travel (0=North, 90=East, 180=South, 270=West)
        
    Returns:
        (new_lat, new_lon) tuple in decimal degrees
    """
    # Earth radius in meters
    R = 6378137
    
    # Convert to radians
    lat1 = math.radians(start_lat)
    lon1 = math.radians(start_lon)
    bearing = math.radians(bearing_degrees)
    
    # Calculate new latitude
    lat2 = math.asin(
        math.sin(lat1) * math.cos(distance_meters / R) +
        math.cos(lat1) * math.sin(distance_meters / R) * math.cos(bearing)
    )
    
    # Calculate new longitude
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(distance_meters / R) * math.cos(lat1),
        math.cos(distance_meters / R) - math.sin(lat1) * math.sin(lat2)
    )
    
    # Convert back to degrees
    return math.degrees(lat2), math.degrees(lon2)


def trajectory_to_gps(trajectory_points, start_lat, start_lon, initial_bearing_deg):
    """
    Convert a trajectory (list of [x, y, z] points in meters) to GPS coordinates.
    
    Args:
        trajectory_points: List of [x, y, z] in meters (x=forward, y=lateral, z=height)
        start_lat: Starting GPS latitude
        start_lon: Starting GPS longitude
        initial_bearing_deg: Initial shot direction (degrees from North)
        
    Returns:
        List of [lat, lon, elevation_meters] points
    """
    gps_trajectory = []
    
    for point in trajectory_points:
        x, y, z = point
        
        # Calculate distance and bearing for this point
        # x = distance forward, y = distance lateral (positive = right)
        distance = math.sqrt(x**2 + y**2)
        
        if distance < 0.1:  # Very close to start
            gps_trajectory.append([start_lat, start_lon, z])
            continue
        
        # Calculate bearing offset from lateral displacement
        # atan2(y, x) gives angle from forward direction
        lateral_angle = math.degrees(math.atan2(y, x))
        
        # Combine with initial bearing
        bearing = initial_bearing_deg + lateral_angle
        
        # Calculate GPS coordinates
        new_lat, new_lon = calculate_new_gps(start_lat, start_lon, distance, bearing)
        
        gps_trajectory.append([new_lat, new_lon, z])
    
    return gps_trajectory


def calculate_distance_between_gps(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS points using Haversine formula.
    
    Args:
        lat1, lon1: First point (decimal degrees)
        lat2, lon2: Second point (decimal degrees)
        
    Returns:
        Distance in meters
    """
    R = 6378137  # Earth radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return distance


def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate initial bearing from point 1 to point 2.
    
    Args:
        lat1, lon1: Start point (decimal degrees)
        lat2, lon2: End point (decimal degrees)
        
    Returns:
        Bearing in degrees (0=North, 90=East, etc.)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon))
    
    bearing = math.degrees(math.atan2(y, x))
    
    # Normalize to 0-360
    return (bearing + 360) % 360


def create_search_zone(landing_gps, radius_meters=15):
    """
    Create a circular search zone around predicted landing point.
    
    Args:
        landing_gps: [lat, lon] of predicted landing
        radius_meters: Search radius
        
    Returns:
        dict with search zone parameters
    """
    lat, lon = landing_gps[:2]
    
    # Create circle points (8 points around perimeter)
    circle_points = []
    for angle in range(0, 360, 45):
        point_lat, point_lon = calculate_new_gps(lat, lon, radius_meters, angle)
        circle_points.append([point_lat, point_lon])
    
    return {
        "center": {"lat": lat, "lon": lon},
        "radius_meters": radius_meters,
        "radius_yards": radius_meters * 1.09361,
        "perimeter_points": circle_points
    }


if __name__ == "__main__":
    """Test GPS conversion"""
    print("GPS Conversion Test")
    print("=" * 60)
    
    # Example: Tee box at a golf course
    tee_lat = 34.0522  # Los Angeles (example)
    tee_lon = -118.2437
    
    print(f"Tee position: {tee_lat}, {tee_lon}")
    
    # Test 1: 200 yards straight ahead (North)
    distance_meters = 200 * 0.9144  # yards to meters
    landing_lat, landing_lon = calculate_new_gps(tee_lat, tee_lon, distance_meters, 0)
    
    print(f"\n200 yards North:")
    print(f"  Landing: {landing_lat:.6f}, {landing_lon:.6f}")
    
    # Verify distance
    check_distance = calculate_distance_between_gps(tee_lat, tee_lon, landing_lat, landing_lon)
    print(f"  Distance check: {check_distance:.1f} meters ({check_distance * 1.09361:.1f} yards)")
    
    #Test 2: Slice (200 yards at 10° right of North)
    landing_lat2, landing_lon2 = calculate_new_gps(tee_lat, tee_lon, distance_meters, 10)
    
    print(f"\n200 yards at 10° right:")
    print(f"  Landing: {landing_lat2:.6f}, {landing_lon2:.6f}")
    
    # Test 3: Create search zone
    search_zone = create_search_zone([landing_lat, landing_lon], radius_meters=15)
    
    print(f"\nSearch zone (15m radius):")
    print(f"  Center: {search_zone['center']}")
    print(f"  Radius: {search_zone['radius_yards']:.1f} yards")
    print(f"  Perimeter points: {len(search_zone['perimeter_points'])}")
    
    print("\n" + "=" * 60)

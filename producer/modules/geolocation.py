import random
from math import radians, sin, cos, sqrt, atan2

def interpolate_route(start, end, steps=15):
    lat_diff = (end[0] - start[0]) / steps
    lon_diff = (end[1] - start[1]) / steps
    return [(round(start[0] + i * lat_diff, 4), round(start[1] + i * lon_diff, 4)) for i in range(steps + 1)]

def haversine_distance(coord1, coord2):
    R = 6371.0  # Earth radius in kilometers
    lat1, lon1 = map(radians, coord1)
    lat2, lon2 = map(radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def random_coord_within():
    WROCLAW_BOUNDS = {
        "min_lat": 51.05,
        "max_lat": 51.15,
        "min_lon": 16.90,
        "max_lon": 17.10
    }

    lat = round(random.uniform(WROCLAW_BOUNDS["min_lat"], WROCLAW_BOUNDS["max_lat"]), 5)
    lon = round(random.uniform(WROCLAW_BOUNDS["min_lon"], WROCLAW_BOUNDS["max_lon"]), 5)
    return (lat, lon)
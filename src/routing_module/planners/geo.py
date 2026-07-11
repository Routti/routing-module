"""Geographic helpers shared by planners."""

import math

from routing_module.maps.routes import LatLng


def haversine_km(a: LatLng, b: LatLng) -> float:
    """Distance in kilometers between two coordinates."""
    earth_radius_km = 6371.0
    lat1, lon1 = math.radians(a.latitude), math.radians(a.longitude)
    lat2, lon2 = math.radians(b.latitude), math.radians(b.longitude)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * earth_radius_km * math.asin(math.sqrt(h))


def cumulative_distances_km(points: list[LatLng]) -> list[float]:
    """Running total distance from the first point along the polyline."""
    if not points:
        return []
    totals = [0.0]
    for i in range(1, len(points)):
        totals.append(totals[-1] + haversine_km(points[i - 1], points[i]))
    return totals


def point_at_distance(points: list[LatLng], cumulative_km: list[float], target_km: float) -> LatLng:
    """Return the point on the polyline closest to target_km from the start."""
    if not points:
        raise ValueError("Polyline has no points")
    if target_km <= 0:
        return points[0]

    for i in range(1, len(points)):
        if cumulative_km[i] >= target_km:
            # Linear interpolation between segment endpoints
            seg_start_km = cumulative_km[i - 1]
            seg_end_km = cumulative_km[i]
            if seg_end_km == seg_start_km:
                return points[i]
            ratio = (target_km - seg_start_km) / (seg_end_km - seg_start_km)
            lat = points[i - 1].latitude + ratio * (points[i].latitude - points[i - 1].latitude)
            lng = points[i - 1].longitude + ratio * (points[i].longitude - points[i - 1].longitude)
            return LatLng(latitude=lat, longitude=lng)

    return points[-1]


def _point_to_segment_km(point: LatLng, start: LatLng, end: LatLng, steps: int = 20) -> float:
    """Approximate shortest distance from point to a polyline segment."""
    min_dist = float("inf")
    for step in range(steps + 1):
        ratio = step / steps
        lat = start.latitude + ratio * (end.latitude - start.latitude)
        lng = start.longitude + ratio * (end.longitude - start.longitude)
        dist = haversine_km(point, LatLng(latitude=lat, longitude=lng))
        if dist < min_dist:
            min_dist = dist
    return min_dist


def min_distance_to_polyline_km(point: LatLng, route_points: list[LatLng]) -> float:
    """Minimum distance from a point to the route polyline."""
    if not route_points:
        return float("inf")
    if len(route_points) == 1:
        return haversine_km(point, route_points[0])

    # Subsample long routes to keep ranking fast enough for CLI use.
    step = max(1, len(route_points) // 400)
    sampled = route_points[::step]
    if sampled[-1] is not route_points[-1]:
        sampled.append(route_points[-1])

    min_dist = float("inf")
    for index in range(len(sampled) - 1):
        dist = _point_to_segment_km(point, sampled[index], sampled[index + 1])
        if dist < min_dist:
            min_dist = dist
    return min_dist


def sample_points_along_route(points: list[LatLng], interval_km: float) -> list[LatLng]:
    """Sample coordinates at fixed distance intervals along the polyline."""
    if not points or interval_km <= 0:
        return []
    cumulative = cumulative_distances_km(points)
    total = cumulative[-1]
    samples: list[LatLng] = []
    distance = interval_km
    while distance < total:
        samples.append(point_at_distance(points, cumulative, distance))
        distance += interval_km
    return samples

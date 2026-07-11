"""Overnight stop planning along a route."""

from routing_module.maps.client import OrsClient
from routing_module.maps.places import search_places
from routing_module.maps.routes import LatLng, decode_polyline_points
from routing_module.models.request import OvernightStay, RouteRequest
from routing_module.models.result import Waypoint, WaypointType
from routing_module.planners.geo import cumulative_distances_km


def plan_overnight_stops(
    request: RouteRequest,
    encoded_polyline: str,
    client: OrsClient,
) -> list[Waypoint]:
    """Place overnight hotel stops in requested countries along the route."""
    if not request.overnight_stays:
        return []

    points = decode_polyline_points(encoded_polyline)
    cumulative = cumulative_distances_km(points)
    total_km = cumulative[-1] if cumulative else 0.0
    if total_km == 0:
        return []

    waypoints: list[Waypoint] = []
    segment_count = len(request.overnight_stays)

    for index, stay in enumerate(request.overnight_stays):
        # Spread overnight stops evenly along the route
        fraction = (index + 1) / (segment_count + 1)
        target_km = total_km * fraction
        target = _point_near_km(points, cumulative, target_km)

        query = f"hotel in {stay.country}"
        results = search_places(
            query=query,
            latitude=target.latitude,
            longitude=target.longitude,
            radius_meters=30_000,
            max_results=5,
            client=client,
        )

        place = _pick_hotel_in_country(results, stay.country)
        if place:
            waypoints.append(
                Waypoint(
                    place=place,
                    type=WaypointType.OVERNIGHT,
                    notes=stay.notes or f"{stay.nights} night(s) in {stay.country}",
                )
            )

    return waypoints


def _point_near_km(points: list[LatLng], cumulative: list[float], target_km: float) -> LatLng:
    """Find polyline point closest to target_km."""
    best = points[0]
    best_diff = float("inf")
    for i, dist in enumerate(cumulative):
        diff = abs(dist - target_km)
        if diff < best_diff:
            best_diff = diff
            best = points[i]
    return best


def _pick_hotel_in_country(results: list, country: str):
    """Prefer a hotel whose address mentions the requested country."""
    country_lower = country.lower()
    for place in results:
        if country_lower in place.address.lower() or country_lower in place.name.lower():
            return place
    return results[0] if results else None

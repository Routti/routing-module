"""OpenRouteService directions integration."""

from dataclasses import dataclass
from urllib.parse import quote

import polyline

from routing_module.maps.client import OrsClient
from routing_module.maps.geocode import geocode_address
from routing_module.models.result import ResolvedPlace


@dataclass
class LatLng:
    """Geographic coordinate."""

    latitude: float
    longitude: float


@dataclass
class RouteInfo:
    """Parsed response from ORS directions."""

    distance_meters: int
    duration_seconds: int
    encoded_polyline: str
    waypoint_addresses: list[str]


def compute_route(
    origin: str,
    destination: str,
    intermediates: list[str] | None = None,
    waypoint_places: list[ResolvedPlace] | None = None,
    client: OrsClient | None = None,
) -> RouteInfo:
    """Compute a driving route between origin and destination."""
    owns_client = client is None
    if owns_client:
        client = OrsClient()

    try:
        origin_place = geocode_address(origin, client)
        destination_place = geocode_address(destination, client)

        if waypoint_places:
            intermediate_coords = waypoint_places
            waypoint_addresses = [place.address for place in waypoint_places]
        else:
            waypoint_addresses = intermediates or []
            intermediate_coords = [
                geocode_address(address, client) for address in waypoint_addresses
            ]

        coordinates = [
            [origin_place.longitude, origin_place.latitude],
            *[[place.longitude, place.latitude] for place in intermediate_coords],
            [destination_place.longitude, destination_place.latitude],
        ]

        data = client.post(
            "/v2/directions/driving-car",
            {
                "coordinates": coordinates,
                "instructions": False,
                "geometry": True,
            },
        )
    finally:
        if owns_client:
            client.close()

    routes = data.get("routes", [])
    if not routes:
        raise ValueError(f"No route found from '{origin}' to '{destination}'")

    route = routes[0]
    summary = route.get("summary", {})
    geometry = route.get("geometry")
    if not geometry:
        raise ValueError(f"ORS returned no route geometry for '{origin}' to '{destination}'")

    return RouteInfo(
        distance_meters=int(summary.get("distance", 0)),
        duration_seconds=int(summary.get("duration", 0)),
        encoded_polyline=geometry,
        waypoint_addresses=waypoint_addresses,
    )


def decode_polyline_points(encoded: str) -> list[LatLng]:
    """Decode an ORS/Google encoded polyline into coordinates."""
    coords = polyline.decode(encoded)
    return [LatLng(latitude=lat, longitude=lng) for lat, lng in coords]


def build_maps_directions_url(origin: str, destination: str, waypoints: list[str]) -> str:
    """Build a shareable Google Maps directions URL (no API key required)."""
    base = "https://www.google.com/maps/dir/?api=1"
    parts = [f"origin={quote(origin)}", f"destination={quote(destination)}"]
    if waypoints:
        joined = "|".join(quote(w, safe="") for w in waypoints)
        parts.append(f"waypoints={joined}")
    parts.append("travelmode=driving")
    return base + "&" + "&".join(parts)

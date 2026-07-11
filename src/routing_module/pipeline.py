"""End-to-end trip planning orchestration."""

from routing_module.llm.parser import parse_trip_request
from routing_module.maps.client import OrsClient
from routing_module.maps.places import search_place_by_name
from routing_module.maps.routes import build_maps_directions_url, compute_route
from routing_module.models.request import RouteRequest
from routing_module.models.result import ResolvedPlace, RouteLeg, RouteResult, Waypoint, WaypointType
from routing_module.planners.fuel import plan_fuel_stops
from routing_module.planners.overnight import plan_overnight_stops


def plan_trip(user_input: str, request: RouteRequest | None = None) -> RouteResult:
    """Run the full pipeline from natural language (or pre-parsed request) to route result."""
    trip_request = request or parse_trip_request(user_input)
    warnings = list(trip_request.warnings)

    with OrsClient() as client:
        # Base route without waypoints to get the corridor polyline
        base_route = compute_route(
            origin=trip_request.origin,
            destination=trip_request.destination,
            client=client,
        )

        fuel_waypoints = plan_fuel_stops(trip_request, base_route.encoded_polyline, client)
        overnight_waypoints = plan_overnight_stops(
            trip_request, base_route.encoded_polyline, client
        )
        explicit_waypoints = _resolve_explicit_waypoints(trip_request, client)

        merged = _merge_waypoints(fuel_waypoints, overnight_waypoints, explicit_waypoints)

        intermediate_addresses = [wp.place.address for wp in merged]
        final_route = compute_route(
            origin=trip_request.origin,
            destination=trip_request.destination,
            waypoint_places=[wp.place for wp in merged] or None,
            client=client,
        )

    origin_wp = Waypoint(
        place=ResolvedPlace(
            name=trip_request.origin,
            address=trip_request.origin,
            latitude=0.0,
            longitude=0.0,
        ),
        type=WaypointType.ORIGIN,
    )
    destination_wp = Waypoint(
        place=ResolvedPlace(
            name=trip_request.destination,
            address=trip_request.destination,
            latitude=0.0,
            longitude=0.0,
        ),
        type=WaypointType.DESTINATION,
    )

    all_waypoints = [origin_wp, *merged, destination_wp]
    legs = _build_legs(all_waypoints, final_route.distance_meters, final_route.duration_seconds)

    maps_url = build_maps_directions_url(
        origin=trip_request.origin,
        destination=trip_request.destination,
        waypoints=intermediate_addresses,
    )

    return RouteResult(
        request_summary=f"{trip_request.origin} -> {trip_request.destination}",
        waypoints=all_waypoints,
        legs=legs,
        total_distance_meters=final_route.distance_meters,
        total_duration_seconds=final_route.duration_seconds,
        maps_url=maps_url,
        warnings=warnings,
    )


def _resolve_explicit_waypoints(request: RouteRequest, client: OrsClient) -> list[Waypoint]:
    """Turn named explicit waypoints into resolved places via ORS geocoding."""
    waypoints: list[Waypoint] = []
    for name in request.explicit_waypoints:
        place = search_place_by_name(name, client)
        if place:
            waypoints.append(
                Waypoint(place=place, type=WaypointType.EXPLICIT, notes=name)
            )
    return waypoints


def _merge_waypoints(*groups: list[Waypoint]) -> list[Waypoint]:
    """Combine waypoint lists and remove duplicates by address."""
    merged: list[Waypoint] = []
    seen: set[str] = set()
    for group in groups:
        for wp in group:
            if wp.place.address in seen:
                continue
            seen.add(wp.place.address)
            merged.append(wp)
    return merged


def _build_legs(
    waypoints: list[Waypoint],
    total_distance: int,
    total_duration: int,
) -> list[RouteLeg]:
    """Build leg summaries. Distributes totals evenly when per-leg data is unavailable."""
    if len(waypoints) < 2:
        return []

    leg_count = len(waypoints) - 1
    dist_each = total_distance // leg_count
    dur_each = total_duration // leg_count

    legs: list[RouteLeg] = []
    for i in range(leg_count):
        legs.append(
            RouteLeg(
                from_name=waypoints[i].place.name,
                to_name=waypoints[i + 1].place.name,
                distance_meters=dist_each,
                duration_seconds=dur_each,
            )
        )
    return legs

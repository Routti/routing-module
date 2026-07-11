"""Fuel stop planning along a route polyline."""

from routing_module.maps.places import search_places
from routing_module.maps.client import OrsClient
from routing_module.maps.routes import LatLng, decode_polyline_points
from routing_module.models.request import RouteRequest, StopPreference, StopType
from routing_module.models.result import ResolvedPlace, Waypoint, WaypointType
from routing_module.planners.geo import (
    cumulative_distances_km,
    min_distance_to_polyline_km,
    point_at_distance,
)

# Prefer motorway rest areas and similar stops when ranking candidates.
HIGHWAY_KEYWORDS = (
    "motorway",
    "highway",
    "autostrada",
    "autobahn",
    "rest area",
    "rest stop",
    "service area",
    "počivališče",
    "pocivalisce",
    "odpočivaliště",
    "odpocivliste",
    "mop",
    "a1",
    "a2",
    "a4",
)

MAX_OFF_ROUTE_KM = 3.0
FALLBACK_OFF_ROUTE_KM = 8.0


def _fuel_search_queries(pref: StopPreference) -> list[str]:
    """Build geocode queries from most specific to most general."""
    queries: list[str] = []

    for brand in pref.brands:
        queries.append(brand)
        queries.append(f"{brand} petrol station")

    if pref.type == StopType.GAS_STATION:
        queries.extend(["petrol station", "gas station", "fuel station"])
    elif pref.type == StopType.REST_STOP:
        queries.append("rest area")
    elif pref.type == StopType.FOOD:
        queries.append("restaurant")
    elif pref.type == StopType.SHOPPING:
        queries.append("shopping mall")

    for category in pref.categories:
        queries.append(category.replace("_", " "))

    queries.extend(pref.amenities)

    seen: set[str] = set()
    unique: list[str] = []
    for query in queries:
        key = query.lower()
        if key not in seen:
            seen.add(key)
            unique.append(query)

    return unique or ["petrol station"]


def _matches_brand(place: ResolvedPlace, pref: StopPreference) -> bool:
    """True when place matches a required brand, or no brand filter is set."""
    if not pref.brands:
        return True
    text = f"{place.name} {place.address}".lower()
    return any(brand.lower() in text for brand in pref.brands)


def _highway_bonus(place: ResolvedPlace) -> float:
    """Small score bonus for names that look like motorway service stops."""
    text = f"{place.name} {place.address}".lower()
    if any(keyword in text for keyword in HIGHWAY_KEYWORDS):
        return 1.0
    return 0.0


def _rank_place(place: ResolvedPlace, route_points: list[LatLng]) -> float:
    """Lower score is better. Prefer stops on the route and motorway service areas."""
    off_route_km = min_distance_to_polyline_km(LatLng(place.latitude, place.longitude), route_points)
    return off_route_km - _highway_bonus(place)


def _pick_best_on_route(
    results: list[ResolvedPlace],
    pref: StopPreference,
    route_points: list[LatLng],
    max_off_route_km: float,
) -> ResolvedPlace | None:
    """Pick the best fuel stop within max_off_route_km of the driving route."""
    candidates = [place for place in results if _matches_brand(place, pref)]
    if not candidates:
        return None

    within_limit = [
        place
        for place in candidates
        if min_distance_to_polyline_km(LatLng(place.latitude, place.longitude), route_points) <= max_off_route_km
    ]
    if not within_limit:
        return None

    return min(within_limit, key=lambda place: _rank_place(place, route_points))


def _collect_fuel_candidates(
    pref: StopPreference,
    latitude: float,
    longitude: float,
    client: OrsClient,
) -> list[ResolvedPlace]:
    """Run all search queries and merge unique place results."""
    merged: dict[str, ResolvedPlace] = {}
    for query in _fuel_search_queries(pref):
        results = search_places(
            query=query,
            latitude=latitude,
            longitude=longitude,
            radius_meters=25_000,
            max_results=10,
            client=client,
        )
        for place in results:
            merged.setdefault(place.address, place)
    return list(merged.values())


def _search_fuel_near(
    pref: StopPreference,
    latitude: float,
    longitude: float,
    route_points: list[LatLng],
    client: OrsClient,
) -> ResolvedPlace | None:
    """Find the best fuel stop near a route point, preferring places on the motorway."""
    candidates = _collect_fuel_candidates(pref, latitude, longitude, client)

    place = _pick_best_on_route(candidates, pref, route_points, MAX_OFF_ROUTE_KM)
    if place:
        return place

    return _pick_best_on_route(candidates, pref, route_points, FALLBACK_OFF_ROUTE_KM)


def _fuel_interval_km(request: RouteRequest) -> float | None:
    """Distance between fuel stops. Uses 80% of max range for safety margin."""
    max_range = request.max_range_km
    if max_range is None:
        return None
    return max_range * 0.8


def plan_fuel_stops(
    request: RouteRequest,
    encoded_polyline: str,
    client: OrsClient,
) -> list[Waypoint]:
    """Find fuel and rest stops along the route based on tank range and preferences."""
    interval = _fuel_interval_km(request)
    if interval is None:
        return []

    gas_prefs = [p for p in request.stop_preferences if p.type in {
        StopType.GAS_STATION, StopType.REST_STOP, StopType.FOOD, StopType.SHOPPING,
    }]
    if not gas_prefs:
        gas_prefs = [StopPreference(type=StopType.GAS_STATION)]

    points = decode_polyline_points(encoded_polyline)
    cumulative = cumulative_distances_km(points)
    total_km = cumulative[-1] if cumulative else 0.0

    waypoints: list[Waypoint] = []
    seen_addresses: set[str] = set()
    distance = interval

    while distance < total_km:
        target = point_at_distance(points, cumulative, distance)
        pref = gas_prefs[len(waypoints) % len(gas_prefs)]

        place = _search_fuel_near(pref, target.latitude, target.longitude, points, client)

        if place and place.address not in seen_addresses:
            seen_addresses.add(place.address)
            off_route = min_distance_to_polyline_km(
                LatLng(place.latitude, place.longitude), points
            )
            waypoints.append(
                Waypoint(
                    place=place,
                    type=WaypointType.FUEL,
                    notes=f"Fuel stop near {distance:.0f} km from origin ({off_route:.1f} km off route)",
                )
            )

        distance += interval

    return waypoints

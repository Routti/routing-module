"""Place search via OpenRouteService geocoding."""

from routing_module.maps.client import OrsClient
from routing_module.maps.geocode import geocode_address
from routing_module.models.result import ResolvedPlace


def search_places(
    query: str,
    latitude: float,
    longitude: float,
    radius_meters: int = 5000,
    max_results: int = 5,
    client: OrsClient | None = None,
) -> list[ResolvedPlace]:
    """Search for places near a coordinate using text query."""
    owns_client = client is None
    if owns_client:
        client = OrsClient()

    params: dict[str, str | int | float] = {
        "text": query,
        "size": max_results,
        "focus.point.lat": latitude,
        "focus.point.lon": longitude,
        "boundary.circle.lat": latitude,
        "boundary.circle.lon": longitude,
        "boundary.circle.radius": radius_meters / 1000,
    }

    try:
        data = client.get("/geocode/search", params=params)
    finally:
        if owns_client:
            client.close()

    places: list[ResolvedPlace] = []
    for feature in data.get("features", []):
        coordinates = feature.get("geometry", {}).get("coordinates", [])
        if len(coordinates) < 2:
            continue

        properties = feature.get("properties", {})
        name = properties.get("name") or properties.get("label") or query
        address = properties.get("label") or name

        places.append(
            ResolvedPlace(
                name=name,
                address=address,
                longitude=float(coordinates[0]),
                latitude=float(coordinates[1]),
                place_id=str(properties.get("id", "")) or None,
            )
        )

    return places


def search_place_by_name(name: str, client: OrsClient) -> ResolvedPlace | None:
    """Search for a named place without a coordinate hint."""
    try:
        return geocode_address(name, client)
    except ValueError:
        return None

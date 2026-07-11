"""OpenRouteService geocoding (Pelias)."""

from routing_module.maps.client import OrsClient
from routing_module.models.result import ResolvedPlace


def geocode_address(
    text: str,
    client: OrsClient,
    focus_latitude: float | None = None,
    focus_longitude: float | None = None,
    radius_meters: int | None = None,
) -> ResolvedPlace:
    """Resolve a place name or address to coordinates via ORS geocoding."""
    params: dict[str, str | int | float] = {
        "text": text,
        "size": 1,
    }

    if focus_latitude is not None and focus_longitude is not None:
        params["focus.point.lat"] = focus_latitude
        params["focus.point.lon"] = focus_longitude

    if radius_meters is not None and focus_latitude is not None and focus_longitude is not None:
        # ORS boundary circle radius is in kilometers.
        params["boundary.circle.lat"] = focus_latitude
        params["boundary.circle.lon"] = focus_longitude
        params["boundary.circle.radius"] = radius_meters / 1000

    data = client.get("/geocode/search", params=params)
    features = data.get("features", [])
    if not features:
        raise ValueError(f"No geocoding result for '{text}'")

    feature = features[0]
    coordinates = feature.get("geometry", {}).get("coordinates", [])
    if len(coordinates) < 2:
        raise ValueError(f"Invalid geocoding geometry for '{text}'")

    properties = feature.get("properties", {})
    name = properties.get("name") or properties.get("label") or text
    address = properties.get("label") or name

    return ResolvedPlace(
        name=name,
        address=address,
        longitude=float(coordinates[0]),
        latitude=float(coordinates[1]),
        place_id=str(properties.get("id", "")) or None,
    )

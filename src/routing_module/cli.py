"""CLI entry point for routing-module."""

import sys

import click

from routing_module.llm.parser import parse_trip_request
from routing_module.maps.places import search_places
from routing_module.maps.routes import compute_route
from routing_module.pipeline import plan_trip


def _handle_error(exc: Exception) -> None:
    """Print a clear CLI error and exit."""
    name = exc.__class__.__name__
    message = str(exc)
    if name in {"ResourceExhausted", "ClientError"} and ("429" in message or "quota" in message.lower()):
        click.echo(
            "Error: Gemini quota exceeded. "
            "Use GEMINI_MODEL=gemini-flash-latest in .env or wait and retry.",
            err=True,
        )
    else:
        click.echo(f"Error: {exc}", err=True)
    sys.exit(1)


def _format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _print_route_result(result) -> None:
    click.echo(f"\nTrip: {result.request_summary}")
    click.echo(f"Distance: {result.total_distance_km:.1f} km")
    click.echo(f"Duration: {_format_duration(result.total_duration_seconds)}")

    if result.warnings:
        click.echo("\nWarnings:")
        for warning in result.warnings:
            click.echo(f"  - {warning}")

    if result.waypoints:
        click.echo("\nStops:")
        for i, wp in enumerate(result.waypoints, 1):
            note = f" ({wp.notes})" if wp.notes else ""
            click.echo(f"  {i}. [{wp.type.value}] {wp.place.name} - {wp.place.address}{note}")

    if result.legs:
        click.echo("\nLegs:")
        for leg in result.legs:
            click.echo(
                f"  {leg.from_name} -> {leg.to_name}: "
                f"{leg.distance_meters / 1000:.1f} km, {_format_duration(leg.duration_seconds)}"
            )

    if result.maps_url:
        click.echo(f"\nMap link: {result.maps_url}")


@click.group()
def main() -> None:
    """Natural language trip planner."""


@main.command()
@click.argument("text")
def parse(text: str) -> None:
    """Parse natural language into structured trip JSON (Gemini)."""
    try:
        request = parse_trip_request(text)
        click.echo(request.model_dump_json(indent=2))
    except (ValueError, OSError) as exc:
        _handle_error(exc)
    except Exception as exc:
        _handle_error(exc)


@main.command()
@click.option("--origin", required=True, help="Start location.")
@click.option("--destination", required=True, help="End location.")
def route(origin: str, destination: str) -> None:
    """Compute a simple A-to-B driving route (OpenRouteService)."""
    try:
        info = compute_route(origin=origin, destination=destination)
        click.echo(f"Distance: {info.distance_meters / 1000:.1f} km")
        click.echo(f"Duration: {_format_duration(info.duration_seconds)}")
        click.echo(f"Polyline points: {len(info.encoded_polyline)} chars encoded")
    except (ValueError, OSError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@main.command()
@click.option("--query", required=True, help="Place search text.")
@click.option("--lat", required=True, type=float, help="Latitude for search center.")
@click.option("--lng", required=True, type=float, help="Longitude for search center.")
@click.option("--radius", default=5000, type=int, help="Search radius in meters.")
def search(query: str, lat: float, lng: float, radius: int) -> None:
    """Search for places near a coordinate (OpenRouteService)."""
    try:
        results = search_places(query=query, latitude=lat, longitude=lng, radius_meters=radius)
        if not results:
            click.echo("No places found.")
            return
        for place in results:
            click.echo(f"- {place.name} | {place.address} | ({place.latitude}, {place.longitude})")
    except (ValueError, OSError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@main.command()
@click.argument("text")
@click.option("--json-output", is_flag=True, help="Print full result as JSON.")
def plan(text: str, json_output: bool) -> None:
    """Plan a full trip from natural language."""
    try:
        result = plan_trip(text)
        if json_output:
            click.echo(result.model_dump_json(indent=2))
        else:
            _print_route_result(result)
    except (ValueError, OSError) as exc:
        _handle_error(exc)
    except Exception as exc:
        _handle_error(exc)


if __name__ == "__main__":
    main()

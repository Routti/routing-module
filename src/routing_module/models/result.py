"""Result models returned by the planning pipeline."""

from enum import Enum

from pydantic import BaseModel, Field


class WaypointType(str, Enum):
    """Why a waypoint was added to the route."""

    ORIGIN = "origin"
    DESTINATION = "destination"
    EXPLICIT = "explicit"
    FUEL = "fuel"
    OVERNIGHT = "overnight"
    REST = "rest"


class ResolvedPlace(BaseModel):
    """A place resolved via geocoding or search."""

    name: str
    address: str
    latitude: float
    longitude: float
    place_id: str | None = None


class Waypoint(BaseModel):
    """An ordered stop on the final route."""

    place: ResolvedPlace
    type: WaypointType
    notes: str | None = None


class RouteLeg(BaseModel):
    """One segment between two consecutive waypoints."""

    from_name: str
    to_name: str
    distance_meters: int
    duration_seconds: int


class RouteResult(BaseModel):
    """Complete output of the trip planning pipeline."""

    request_summary: str
    waypoints: list[Waypoint] = Field(default_factory=list)
    legs: list[RouteLeg] = Field(default_factory=list)
    total_distance_meters: int = 0
    total_duration_seconds: int = 0
    maps_url: str | None = None
    warnings: list[str] = Field(default_factory=list)

    @property
    def total_distance_km(self) -> float:
        return self.total_distance_meters / 1000

    @property
    def total_duration_hours(self) -> float:
        return self.total_duration_seconds / 3600

"""Tests for request and result models."""

import pytest
from pydantic import ValidationError

from routing_module.models.request import (
    FuelType,
    RouteRequest,
    StopPreference,
    StopType,
    VehicleInfo,
)
from routing_module.models.result import ResolvedPlace, RouteResult, Waypoint, WaypointType


def test_route_request_defaults():
    req = RouteRequest(origin="Bucharest", destination="Milan")
    assert req.vehicle.fuel_consumption_l_per_100km == 8.0
    assert req.needs_fuel_planning is False
    assert req.max_range_km is None


def test_route_request_fuel_range():
    req = RouteRequest(
        origin="Bucharest",
        destination="Milan",
        vehicle=VehicleInfo(fuel_tank_liters=60, fuel_consumption_l_per_100km=8.0),
    )
    assert req.needs_fuel_planning is True
    assert req.max_range_km == 750.0


def test_vehicle_tank_must_be_positive():
    with pytest.raises(ValidationError):
        VehicleInfo(fuel_tank_liters=-10)


def test_stop_preference_roundtrip():
    pref = StopPreference(
        type=StopType.GAS_STATION,
        brands=["OMV"],
        amenities=["food"],
    )
    data = pref.model_dump()
    assert StopPreference.model_validate(data).brands == ["OMV"]


def test_route_result_distance_helpers():
    result = RouteResult(
        request_summary="test",
        total_distance_meters=100_000,
        total_duration_seconds=7200,
    )
    assert result.total_distance_km == 100.0
    assert result.total_duration_hours == 2.0


def test_waypoint_with_resolved_place():
    wp = Waypoint(
        place=ResolvedPlace(
            name="OMV Budapest",
            address="Budapest, Hungary",
            latitude=47.5,
            longitude=19.0,
        ),
        type=WaypointType.FUEL,
    )
    assert wp.type == WaypointType.FUEL


def test_fuel_type_enum():
    vehicle = VehicleInfo(fuel_type=FuelType.DIESEL)
    assert vehicle.fuel_type == FuelType.DIESEL

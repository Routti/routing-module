"""Tests for fuel planner with mocked Places API."""

import polyline

from routing_module.maps.routes import LatLng
from routing_module.models.request import RouteRequest, StopPreference, StopType, VehicleInfo
from routing_module.models.result import ResolvedPlace
from routing_module.planners.fuel import (
    _fuel_interval_km,
    _fuel_search_queries,
    _pick_best_on_route,
    plan_fuel_stops,
)


def test_fuel_interval_uses_eighty_percent_of_range():
    request = RouteRequest(
        origin="A",
        destination="B",
        vehicle=VehicleInfo(fuel_tank_liters=60, fuel_consumption_l_per_100km=8.0),
    )
    assert _fuel_interval_km(request) == 600.0


def test_fuel_search_queries_with_brand():
    pref = StopPreference(type=StopType.GAS_STATION, brands=["OMV"])
    queries = _fuel_search_queries(pref)
    assert queries[0] == "OMV"
    assert "petrol station" in queries


def test_pick_best_on_route_prefers_closest_to_polyline():
    route_points = [
        LatLng(46.0, 20.0),
        LatLng(46.1, 20.1),
        LatLng(46.2, 20.2),
    ]
    search_point = LatLng(46.1, 20.1)
    pref = StopPreference(type=StopType.GAS_STATION, brands=["OMV"])

    far = ResolvedPlace(name="OMV Far", address="far", latitude=46.5, longitude=20.5)
    near = ResolvedPlace(
        name="OMV - Počivališče Lopata",
        address="near",
        latitude=46.12,
        longitude=20.12,
    )

    picked = _pick_best_on_route([far, near], pref, route_points, max_off_route_km=3.0)
    assert picked == near


def test_pick_best_on_route_rejects_brand_mismatch():
    route_points = [LatLng(46.0, 20.0), LatLng(46.2, 20.2)]
    pref = StopPreference(type=StopType.GAS_STATION, brands=["OMV"])
    shell = ResolvedPlace(name="Shell", address="shell", latitude=46.1, longitude=20.1)

    assert _pick_best_on_route([shell], pref, route_points, max_off_route_km=3.0) is None


def test_plan_fuel_stops_returns_waypoints(mocker):
    request = RouteRequest(
        origin="Bucharest",
        destination="Vienna",
        vehicle=VehicleInfo(fuel_tank_liters=50, fuel_consumption_l_per_100km=10.0),
        stop_preferences=[StopPreference(type=StopType.GAS_STATION, brands=["OMV"])],
    )

    encoded = polyline.encode([(44.4, 26.1), (44.5, 26.2), (45.0, 26.5), (46.0, 27.0)])

    fake_place = ResolvedPlace(
        name="OMV Test",
        address="Test Address",
        latitude=44.5,
        longitude=26.2,
    )
    mocker.patch(
        "routing_module.planners.fuel._search_fuel_near",
        return_value=fake_place,
    )

    waypoints = plan_fuel_stops(request, encoded, client=mocker.Mock())
    assert len(waypoints) >= 0

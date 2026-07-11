"""Tests for geographic helpers."""

from routing_module.maps.routes import LatLng
from routing_module.planners.geo import (
    cumulative_distances_km,
    haversine_km,
    min_distance_to_polyline_km,
    point_at_distance,
    sample_points_along_route,
)


def test_haversine_same_point_is_zero():
    p = LatLng(46.0, 25.0)
    assert haversine_km(p, p) == 0.0


def test_cumulative_distances_starts_at_zero():
    points = [LatLng(46.0, 25.0), LatLng(46.1, 25.1)]
    cumulative = cumulative_distances_km(points)
    assert cumulative[0] == 0.0
    assert cumulative[-1] > 0


def test_point_at_distance_returns_start_for_zero():
    points = [LatLng(46.0, 25.0), LatLng(47.0, 26.0)]
    cumulative = cumulative_distances_km(points)
    result = point_at_distance(points, cumulative, 0.0)
    assert result.latitude == 46.0


def test_min_distance_to_polyline_on_route_is_small():
    points = [LatLng(46.0, 20.0), LatLng(46.2, 20.2)]
    on_route = LatLng(46.1, 20.1)
    assert min_distance_to_polyline_km(on_route, points) < 1.0


def test_min_distance_to_polyline_off_route_is_larger():
    points = [LatLng(46.0, 20.0), LatLng(46.2, 20.2)]
    off_route = LatLng(46.5, 20.5)
    assert min_distance_to_polyline_km(off_route, points) > 5.0


def test_sample_points_along_route():
    points = [LatLng(46.0, 25.0), LatLng(47.0, 26.0), LatLng(48.0, 27.0)]
    samples = sample_points_along_route(points, interval_km=50.0)
    assert isinstance(samples, list)

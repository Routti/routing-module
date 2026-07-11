"""Tests for pipeline with mocked external services."""

from routing_module.models.request import RouteRequest, VehicleInfo
from routing_module.models.result import ResolvedPlace, RouteResult
from routing_module.pipeline import plan_trip


SAMPLE_REQUEST = RouteRequest(
    origin="Bucharest, Romania",
    destination="Cluj-Napoca, Romania",
    vehicle=VehicleInfo(fuel_tank_liters=None),
    warnings=[],
)


class _FakeRouteInfo:
    def __init__(self):
        self.distance_meters = 400_000
        self.duration_seconds = 14_400
        self.encoded_polyline = "encoded_polyline_stub"
        self.waypoint_addresses = []


def test_plan_trip_with_pre_parsed_request(mocker):
    mock_client = mocker.MagicMock()
    mocker.patch("routing_module.pipeline.OrsClient", return_value=mock_client)
    mock_client.__enter__ = mocker.Mock(return_value=mock_client)
    mock_client.__exit__ = mocker.Mock(return_value=False)

    mocker.patch("routing_module.pipeline.compute_route", return_value=_FakeRouteInfo())
    mocker.patch("routing_module.pipeline.plan_fuel_stops", return_value=[])
    mocker.patch("routing_module.pipeline.plan_overnight_stops", return_value=[])
    mocker.patch(
        "routing_module.pipeline.build_maps_directions_url",
        return_value="https://maps.google.com/test",
    )

    result = plan_trip("ignored input", request=SAMPLE_REQUEST)

    assert isinstance(result, RouteResult)
    assert result.total_distance_meters == 400_000
    assert result.maps_url == "https://maps.google.com/test"
    assert len(result.waypoints) >= 2

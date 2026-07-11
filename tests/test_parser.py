"""Tests for the Gemini parser with mocked responses."""

import json

import pytest

from routing_module.llm.parser import parse_trip_request
from routing_module.models.request import RouteRequest, StopType


SAMPLE_RESPONSE = {
    "origin": "Bucharest, Romania",
    "destination": "Milan, Italy",
    "vehicle": {
        "fuel_tank_liters": 60,
        "fuel_consumption_l_per_100km": 8.0,
        "fuel_type": "gasoline",
    },
    "stop_preferences": [
        {
            "type": "gas_station",
            "brands": ["OMV"],
            "amenities": ["food"],
            "categories": [],
            "notes": None,
        }
    ],
    "overnight_stays": [{"country": "Hungary", "nights": 1, "notes": None}],
    "explicit_waypoints": [],
    "warnings": [],
}


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text


class _FakeModels:
    def __init__(self, response_text: str):
        self._response_text = response_text

    def generate_content(self, model, contents, config=None):
        return _FakeResponse(self._response_text)


class _FakeClient:
    def __init__(self, response_text: str):
        self.models = _FakeModels(response_text)


def test_parse_trip_request_valid_json(mocker):
    mocker.patch(
        "routing_module.llm.parser.genai.Client",
        return_value=_FakeClient(json.dumps(SAMPLE_RESPONSE)),
    )
    mocker.patch("routing_module.llm.parser.get_gemini_api_key", return_value="test-key")
    mocker.patch("routing_module.llm.parser.get_gemini_model", return_value="gemini-flash-latest")

    result = parse_trip_request("Bucharest to Milan with 60L tank")

    assert isinstance(result, RouteRequest)
    assert result.origin == "Bucharest, Romania"
    assert result.vehicle.fuel_tank_liters == 60
    assert result.stop_preferences[0].type == StopType.GAS_STATION
    assert result.overnight_stays[0].country == "Hungary"


def test_parse_trip_request_invalid_json(mocker):
    mocker.patch(
        "routing_module.llm.parser.genai.Client",
        return_value=_FakeClient("not json"),
    )
    mocker.patch("routing_module.llm.parser.get_gemini_api_key", return_value="test-key")
    mocker.patch("routing_module.llm.parser.get_gemini_model", return_value="gemini-flash-latest")

    with pytest.raises(ValueError, match="invalid JSON"):
        parse_trip_request("test")

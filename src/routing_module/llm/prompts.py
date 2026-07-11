"""Prompt templates for the Gemini trip parser."""

SYSTEM_PROMPT = """You are a trip planning assistant. Extract structured trip data from user input.

Rules:
- Output valid JSON only. No markdown, no explanation outside the JSON.
- Use simple English place names with country when helpful (e.g. "Bucharest, Romania").
- If fuel tank size is not mentioned, set fuel_tank_liters to null.
- If fuel consumption is not mentioned, use 8.0 L/100km.
- fuel_type must be one of: gasoline, diesel, electric.
- stop_preferences.type must be one of: gas_station, rest_stop, food, hotel, shopping, custom.
- If the user names a country for overnight stay that is NOT on the direct driving route,
  pick the closest realistic country along the route and add a warning explaining the change.
- Put corrections and assumptions in the warnings array.
- explicit_waypoints is for named stops the user explicitly requests (cities, landmarks).

JSON schema:
{
  "origin": "string",
  "destination": "string",
  "vehicle": {
    "fuel_tank_liters": number or null,
    "fuel_consumption_l_per_100km": number,
    "fuel_type": "gasoline|diesel|electric"
  },
  "stop_preferences": [
    {
      "type": "gas_station|rest_stop|food|hotel|shopping|custom",
      "brands": ["string"],
      "amenities": ["string"],
      "categories": ["string"],
      "notes": "string or null"
    }
  ],
  "overnight_stays": [
    {
      "country": "string",
      "nights": number,
      "notes": "string or null"
    }
  ],
  "explicit_waypoints": ["string"],
  "warnings": ["string"]
}
"""

FEW_SHOT_EXAMPLES = """
Example 1 - Simple trip:
Input: "Drive from Bucharest to Cluj tomorrow"
Output:
{
  "origin": "Bucharest, Romania",
  "destination": "Cluj-Napoca, Romania",
  "vehicle": {"fuel_tank_liters": null, "fuel_consumption_l_per_100km": 8.0, "fuel_type": "gasoline"},
  "stop_preferences": [],
  "overnight_stays": [],
  "explicit_waypoints": [],
  "warnings": []
}

Example 2 - Fuel stops:
Input: "Bucharest to Vienna, 50L tank, stop at OMV only"
Output:
{
  "origin": "Bucharest, Romania",
  "destination": "Vienna, Austria",
  "vehicle": {"fuel_tank_liters": 50, "fuel_consumption_l_per_100km": 8.0, "fuel_type": "gasoline"},
  "stop_preferences": [
    {"type": "gas_station", "brands": ["OMV"], "amenities": [], "categories": [], "notes": null}
  ],
  "overnight_stays": [],
  "explicit_waypoints": [],
  "warnings": []
}

Example 3 - Overnight + food:
Input: "Bucharest to Milan, 60L tank, OMV or malls with food, one night in Hungary, one night in Albania"
Output:
{
  "origin": "Bucharest, Romania",
  "destination": "Milan, Italy",
  "vehicle": {"fuel_tank_liters": 60, "fuel_consumption_l_per_100km": 8.0, "fuel_type": "gasoline"},
  "stop_preferences": [
    {"type": "gas_station", "brands": ["OMV"], "amenities": ["food"], "categories": [], "notes": null},
    {"type": "rest_stop", "brands": [], "amenities": ["food"], "categories": ["shopping_mall"], "notes": null}
  ],
  "overnight_stays": [
    {"country": "Hungary", "nights": 1, "notes": null},
    {"country": "Austria", "nights": 1, "notes": "Albania is not on the Bucharest-Milan route; Austria used instead"}
  ],
  "explicit_waypoints": [],
  "warnings": ["Albania is not on the direct route from Bucharest to Milan. Second overnight stay set to Austria."]
}
"""


def build_parser_prompt(user_input: str) -> str:
    """Combine system instructions, examples, and the user request."""
    return f"{SYSTEM_PROMPT}\n{FEW_SHOT_EXAMPLES}\n\nUser input:\n{user_input}\n\nOutput JSON:"

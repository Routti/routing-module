# routing-module

CLI tool that turns natural-language trip requests into driving routes with fuel stops and overnight stays.

## How it works

1. You describe a trip in plain English.
2. Gemini extracts a structured trip plan (origin, destination, vehicle, stop preferences, overnight stays).
3. OpenRouteService resolves locations and builds the final route with waypoints.

## Requirements

- Python 3.11+
- Gemini API key (free tier via [Google AI Studio](https://aistudio.google.com/))
- OpenRouteService API key (free via [openrouteservice.org](https://openrouteservice.org/dev/#/signup))

OpenRouteService uses OpenStreetMap data. The free Standard plan includes roughly 2,000 direction requests and 1,000 geocoding requests per day.

## Setup

```bash
cd routing-module
python -m venv .venv
source .venv/bin/activate.fish   # fish shell
# or: source .venv/bin/activate   # bash/zsh
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your API keys
```

## Usage

```bash
# Parse a trip request into structured JSON (Gemini only)
routing-module parse "Drive from Bucharest to Milan with a 60L tank"

# Compute a simple A-to-B route (OpenRouteService only)
routing-module route --origin "Bucharest, Romania" --destination "Milan, Italy"

# Search for places near a point (OpenRouteService only)
routing-module search --query "OMV gas station" --lat 46.0 --lng 19.0

# Full trip planning pipeline
routing-module plan "I want to drive from Bucharest to Milan. My car has a 60L gas tank and uses about 8L per 100km. Stop only at OMV stations or malls where I can eat. Spend one night in Hungary and one night in Austria."
```

## Project layout

```
src/routing_module/
  cli.py          CLI entry point
  pipeline.py     End-to-end orchestration
  models/         Pydantic request and result schemas
  llm/            Gemini parser
  maps/           OpenRouteService client (geocoding, directions, search)
  planners/       Fuel and overnight stop logic
```

## Development

```bash
pytest
```

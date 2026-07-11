"""Parse natural language trip requests using Gemini."""

import json

from google import genai
from google.genai import types
from pydantic import ValidationError

from routing_module.config import get_gemini_api_key, get_gemini_model
from routing_module.llm.prompts import build_parser_prompt
from routing_module.models.request import RouteRequest


def parse_trip_request(user_input: str) -> RouteRequest:
    """Send user text to Gemini and return a validated RouteRequest."""
    client = genai.Client(api_key=get_gemini_api_key())

    response = client.models.generate_content(
        model=get_gemini_model(),
        contents=build_parser_prompt(user_input),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    raw_text = (response.text or "").strip()
    if not raw_text:
        raise ValueError("Gemini returned an empty response")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON: {raw_text[:200]}") from exc

    try:
        return RouteRequest.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Gemini JSON does not match RouteRequest schema: {exc}") from exc

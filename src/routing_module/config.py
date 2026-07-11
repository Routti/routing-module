"""Load settings from environment variables."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")
    return key


@lru_cache
def get_openrouteservice_api_key() -> str:
    key = os.getenv("OPENROUTESERVICE_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "OPENROUTESERVICE_API_KEY is not set. "
            "Sign up at https://openrouteservice.org/dev/#/signup and add your key to .env."
        )
    return key


def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()

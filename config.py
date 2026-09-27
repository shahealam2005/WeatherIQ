# config.py
"""Application configuration — loads environment variables at import time.

Priority order for secrets:
  1. st.secrets  (Streamlit Community Cloud — injected at runtime)
  2. .env file   (local development via python-dotenv)
  3. os.environ  (any other environment variable source)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env for local development (no-op if the file doesn't exist, e.g. on Cloud)
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)


def _secret(key: str, default: str = "") -> str:
    """Return a secret value, checking st.secrets first (Cloud), then os.environ."""
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


WEATHER_API_KEY: str       = _secret("WEATHER_API_KEY")
WEATHER_API_BASE_URL: str  = "https://api.openweathermap.org/data/2.5"
DB_PATH: str               = _secret("DB_PATH", "weather.db")
REQUEST_TIMEOUT_SECONDS: int = 10
GEMINI_API_KEY: str        = _secret("GEMINI_API_KEY")

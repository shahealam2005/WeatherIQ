# config.py
"""Application configuration — loads environment variables at import time."""

from pathlib import Path
from dotenv import load_dotenv
import os

# Use an explicit path and override=True so a previously cached environment
# variable (e.g. from a prior Streamlit run) is always refreshed from .env.
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
WEATHER_API_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
DB_PATH: str = os.getenv("DB_PATH", "weather.db")
REQUEST_TIMEOUT_SECONDS: int = 10
# tests/conftest.py
"""Shared pytest fixtures for WeatherIQ tests."""

import sqlite3
from unittest.mock import patch

import pytest

from models import CurrentWeather, DailyForecast


@pytest.fixture
def in_memory_db(monkeypatch):
    """Patch config.DB_PATH to use an in-memory SQLite database for tests."""
    monkeypatch.setattr("config.DB_PATH", ":memory:")
    import data_store
    data_store.init_db()
    return ":memory:"


@pytest.fixture
def sample_current_weather():
    """A sample CurrentWeather instance for use in tests."""
    return CurrentWeather(
        city="TestCity",
        timestamp_utc="2024-07-15T12:00:00Z",
        temperature=22.5,
        feels_like=21.0,
        humidity=65,
        wind_speed=15.0,
        pressure=1013,
        visibility=9.5,
        condition="Clear",
    )


@pytest.fixture
def sample_daily_forecast():
    """A sample DailyForecast instance for use in tests."""
    return DailyForecast(
        date="2024-07-16",
        temperature=24.0,
        condition="Sunny",
    )

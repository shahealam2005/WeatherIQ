# models.py
"""Shared dataclasses used across all WeatherIQ modules."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CurrentWeather:
    """Weather conditions at a single point in time for a specific city."""
    city: str
    timestamp_utc: str          # ISO-8601 UTC string e.g. "2024-07-15T12:00:00Z"
    temperature: Optional[float]      # °C
    feels_like: Optional[float]       # °C
    humidity: Optional[int]           # 0–100 %
    wind_speed: Optional[float]       # km/h (converted from m/s)
    pressure: Optional[int]           # hPa
    visibility: Optional[float]       # km, capped at 10.0
    condition: Optional[str]          # e.g. "Clear", "Rain"


@dataclass
class DailyForecast:
    """Representative forecast for a single calendar day (noon-selection rule)."""
    date: str                         # "YYYY-MM-DD"
    temperature: Optional[float]      # °C
    condition: Optional[str]


@dataclass
class AnalysisResult:
    """Output of the Analyzer for a city's historical records."""
    stats: dict = field(default_factory=dict)
    # stats shape: {"temperature": {"min": ..., "max": ..., "mean": ...}, "humidity": {...}, "wind_speed": {...}}
    trend_temperature: list = field(default_factory=list)
    # trend shape: [{"timestamp": "ISO-8601", "value": float}, ...]
    trend_humidity: list = field(default_factory=list)
    trend_wind_speed: list = field(default_factory=list)
    is_empty: bool = False
    error: Optional[str] = None


@dataclass
class Insight:
    """A human-readable insight message produced by the Insight_Engine."""
    message: str

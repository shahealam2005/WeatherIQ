# api_client.py
"""Weather API client — all OpenWeatherMap HTTP interactions."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from datetime import datetime, timezone
from typing import Optional, Union

import requests

import config
from models import CurrentWeather, DailyForecast

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class WeatherAPIError(Exception):
    """Raised for any failure communicating with the Weather API.

    kind values: "not_found" | "auth" | "timeout" | "network" | "unknown"
    The error message MUST NOT contain the API key value.
    """

    def __init__(self, message: str, kind: str) -> None:
        super().__init__(message)
        self.kind = kind


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _safe_visibility(raw_metres) -> Optional[float]:
    """Convert metres to km and cap at 10.0. Returns None if input is None."""
    if raw_metres is None:
        return None
    return min(round(raw_metres / 1000, 1), 10.0)


def _safe_wind_speed(raw_ms) -> Optional[float]:
    """Convert m/s to km/h. Returns None if input is None."""
    if raw_ms is None:
        return None
    return round(raw_ms * 3.6, 1)


def _parse_current_weather(data: dict) -> CurrentWeather:
    """Parse OWM /weather JSON into a CurrentWeather dataclass."""
    main = data.get("main", {})
    wind = data.get("wind", {})
    weather_list = data.get("weather", [{}])

    dt_unix = data.get("dt")
    if dt_unix is not None:
        timestamp_utc = datetime.utcfromtimestamp(dt_unix).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        timestamp_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    return CurrentWeather(
        city=data.get("name", "Unknown"),
        timestamp_utc=timestamp_utc,
        temperature=main.get("temp"),
        feels_like=main.get("feels_like"),
        humidity=main.get("humidity"),
        wind_speed=_safe_wind_speed(wind.get("speed")),
        pressure=main.get("pressure"),
        visibility=_safe_visibility(data.get("visibility")),
        condition=weather_list[0].get("main") if weather_list else None,
    )


def _select_noon_record(records: list) -> dict:
    """From a list of forecast records sharing the same date, return the one
    whose time component is closest to 12:00 noon (720 minutes from midnight).
    """

    def minutes_from_midnight(rec):
        dt_txt = rec.get("dt_txt", "")
        try:
            t = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
            return abs(t.hour * 60 + t.minute - 720)
        except ValueError:
            return 9999

    return min(records, key=minutes_from_midnight)


def _raise_for_status(response: requests.Response, city: str) -> None:
    """Inspect response status and raise a WeatherAPIError if not successful."""
    if response.status_code == 404:
        raise WeatherAPIError(
            f"City '{city}' was not found.",
            kind="not_found",
        )
    if response.status_code in (401, 403):
        raise WeatherAPIError(
            "Authentication failed. Please verify your API key configuration.",
            kind="auth",
        )
    if not response.ok:
        raise WeatherAPIError(
            f"Weather API returned an unexpected error (HTTP {response.status_code}).",
            kind="unknown",
        )


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def fetch_current_weather(city: str) -> CurrentWeather:
    """Fetch current weather for *city* from OpenWeatherMap.

    Raises WeatherAPIError on any failure.
    """
    url = f"{config.WEATHER_API_BASE_URL}/weather"
    params = {
        "q": city,
        "appid": config.WEATHER_API_KEY,
        "units": "metric",
    }
    try:
        response = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT_SECONDS)
    except requests.Timeout:
        raise WeatherAPIError(
            "The request timed out. Please try again.",
            kind="timeout",
        )
    except requests.ConnectionError:
        raise WeatherAPIError(
            "Could not reach the weather service. Please check your internet connection.",
            kind="network",
        )

    _raise_for_status(response, city)

    try:
        data = response.json()
    except ValueError:
        raise WeatherAPIError(
            "Received an unreadable response from the weather service.",
            kind="unknown",
        )

    return _parse_current_weather(data)


def fetch_forecast(city: str) -> list:
    """Fetch a 5-day forecast for *city*, returning one DailyForecast per calendar day.

    Applies the noon-selection rule: for each calendar date, selects the 3-hour
    interval entry closest to 12:00 noon local time.

    Raises WeatherAPIError on any failure.
    """
    url = f"{config.WEATHER_API_BASE_URL}/forecast"
    params = {
        "q": city,
        "appid": config.WEATHER_API_KEY,
        "units": "metric",
    }
    try:
        response = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT_SECONDS)
    except requests.Timeout:
        raise WeatherAPIError(
            "The forecast request timed out. Please try again.",
            kind="timeout",
        )
    except requests.ConnectionError:
        raise WeatherAPIError(
            "Could not reach the weather service for forecast data.",
            kind="network",
        )

    _raise_for_status(response, city)

    try:
        data = response.json()
    except ValueError:
        raise WeatherAPIError(
            "Received an unreadable forecast response from the weather service.",
            kind="unknown",
        )

    raw_list = data.get("list", [])
    if not raw_list:
        return []

    # Group by calendar date (date portion of dt_txt)
    by_date: dict = {}
    for entry in raw_list:
        dt_txt = entry.get("dt_txt", "")
        date_str = dt_txt[:10]  # "YYYY-MM-DD"
        if date_str:
            by_date.setdefault(date_str, []).append(entry)

    daily_forecasts = []
    for date_str in sorted(by_date.keys()):
        best = _select_noon_record(by_date[date_str])
        main = best.get("main", {})
        weather_list = best.get("weather", [{}])
        daily_forecasts.append(
            DailyForecast(
                date=date_str,
                temperature=main.get("temp"),
                condition=weather_list[0].get("main") if weather_list else None,
            )
        )

    return daily_forecasts


def fetch_comparison(cities: list) -> dict:
    """Fetch current weather for each city concurrently.

    Returns a dict mapping city name → CurrentWeather or WeatherAPIError.
    A per-city failure does NOT cancel the remaining requests.
    All requests complete or time out within 10 seconds.
    """
    results: dict = {}

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(fetch_current_weather, city): city for city in cities}
        try:
            for future in as_completed(futures, timeout=10):
                city = futures[future]
                try:
                    results[city] = future.result()
                except WeatherAPIError as exc:
                    results[city] = exc
        except FuturesTimeoutError:
            # Mark any city that hasn't completed yet as a timeout error
            completed = set(results.keys())
            for city in cities:
                if city not in completed:
                    results[city] = WeatherAPIError(
                        "Request timed out for this city.",
                        kind="timeout",
                    )

    return results

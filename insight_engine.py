# insight_engine.py
"""Weather insight engine — evaluates threshold rules against current conditions."""

from models import CurrentWeather, Insight

# Threshold constants
_TEMP_HIGH_THRESHOLD = 35.0       # °C
_HUMIDITY_HIGH_THRESHOLD = 85     # %
_WIND_HIGH_THRESHOLD = 50.0       # km/h
_TEMP_DELTA_THRESHOLD = 10.0      # °C between consecutive records


def evaluate(current: CurrentWeather, recent_history: list) -> list:
    """Evaluate insight thresholds independently against *current* weather.

    Args:
        current:        The most recently fetched CurrentWeather record.
        recent_history: The two most recent Historical_Records for this city
                        (list of dicts, sorted ascending by timestamp_utc).
                        May be empty or contain only one record.

    Returns:
        A list of Insight objects (may be empty). Thresholds whose required
        field is None are silently skipped; this function never raises.
    """
    insights: list = []

    # --- High temperature ---
    if current.temperature is not None and current.temperature > _TEMP_HIGH_THRESHOLD:
        insights.append(Insight(message="Unusually high temperature detected."))

    # --- High humidity ---
    if current.humidity is not None and current.humidity > _HUMIDITY_HIGH_THRESHOLD:
        insights.append(Insight(message="High humidity conditions."))

    # --- Strong wind ---
    if current.wind_speed is not None and current.wind_speed > _WIND_HIGH_THRESHOLD:
        insights.append(Insight(message="Strong wind conditions."))

    # --- Significant temperature change ---
    if len(recent_history) >= 2:
        latest = recent_history[-1]
        previous = recent_history[-2]
        latest_temp = latest.get("temperature")
        prev_temp = previous.get("temperature")
        if (
            latest_temp is not None
            and prev_temp is not None
            and abs(latest_temp - prev_temp) > _TEMP_DELTA_THRESHOLD
        ):
            insights.append(Insight(message="Significant temperature change since last reading."))

    return insights

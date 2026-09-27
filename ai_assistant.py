# ai_assistant.py
"""Gemini-powered AI Weather Assistant backend for WeatherIQ.

Architecture:
    Weather API → CurrentWeather/Forecast data → Gemini → AI response → UI

The API key is read server-side only; it is never sent to the frontend.
"""

import logging
from typing import Optional

import google.generativeai as genai

import config
from api_client import WeatherAPIError, fetch_current_weather, fetch_forecast
from models import CurrentWeather, DailyForecast

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini client initialisation
# ---------------------------------------------------------------------------

_gemini_ready = False
_gemini_model = None

def _init_gemini() -> bool:
    """Configure the Gemini client once.  Returns True on success."""
    global _gemini_ready, _gemini_model
    if _gemini_ready:
        return True
    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — AI Assistant disabled.")
        return False
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-3.8-flash")
        _gemini_ready = True
        logger.info("Gemini client initialised successfully.")
        return True
    except Exception as exc:
        logger.error("Gemini init error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Weather context builder
# ---------------------------------------------------------------------------

def _build_weather_context(city: str) -> tuple[Optional[str], Optional[str]]:
    """Fetch current weather + forecast for *city* and return a formatted
    context string and an error message (one will be None).
    """
    try:
        cw: CurrentWeather = fetch_current_weather(city)
    except WeatherAPIError as exc:
        return None, f"Could not fetch weather for '{city}': {exc}"

    lines = [
        f"=== Current Weather for {cw.city} ===",
        f"Timestamp (UTC): {cw.timestamp_utc}",
        f"Temperature: {cw.temperature} °C" if cw.temperature is not None else "Temperature: N/A",
        f"Feels Like: {cw.feels_like} °C" if cw.feels_like is not None else "Feels Like: N/A",
        f"Humidity: {cw.humidity} %" if cw.humidity is not None else "Humidity: N/A",
        f"Wind Speed: {cw.wind_speed} km/h" if cw.wind_speed is not None else "Wind Speed: N/A",
        f"Pressure: {cw.pressure} hPa" if cw.pressure is not None else "Pressure: N/A",
        f"Visibility: {cw.visibility} km" if cw.visibility is not None else "Visibility: N/A",
        f"Condition: {cw.condition}" if cw.condition else "Condition: N/A",
    ]

    try:
        forecast_list: list[DailyForecast] = fetch_forecast(city)
        if forecast_list:
            lines.append("\n=== 5-Day Forecast ===")
            for fc in sorted(forecast_list, key=lambda d: d.date):
                temp_str = f"{fc.temperature} °C" if fc.temperature is not None else "N/A"
                cond_str = fc.condition or "N/A"
                lines.append(f"{fc.date}: {temp_str}, {cond_str}")
    except WeatherAPIError:
        lines.append("\n(Forecast data unavailable)")

    return "\n".join(lines), None


def _build_comparison_context(cities: list[str]) -> tuple[Optional[str], Optional[str]]:
    """Fetch weather for multiple cities and return a comparison context block."""
    from api_client import fetch_comparison
    results = fetch_comparison(cities)

    lines = ["=== Multi-City Weather Comparison ==="]
    any_success = False
    for city, data in results.items():
        if isinstance(data, CurrentWeather):
            any_success = True
            lines.append(
                f"{data.city}: {data.temperature} °C, "
                f"Humidity {data.humidity}%, "
                f"Wind {data.wind_speed} km/h, "
                f"Condition: {data.condition or 'N/A'}"
            )
        else:
            lines.append(f"{city}: data unavailable")

    if not any_success:
        return None, "Could not fetch weather data for any of the requested cities."
    return "\n".join(lines), None


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_EN = (
    "You are WeatherIQ Assistant, a friendly and knowledgeable AI weather analyst. "
    "You will be given real-time weather data fetched from a live weather API. "
    "Use ONLY this data to answer the user's question — do not fabricate or assume values. "
    "Be concise, warm, and practical. Use bullet points where helpful. "
    "If asked about activities (running, cricket, cycling, travel, clothing), give clear, "
    "actionable recommendations backed by the weather numbers provided. "
    "If the data is insufficient to answer, say so honestly."
)

_SYSTEM_PROMPT_HI = (
    "आप WeatherIQ Assistant हैं — एक मित्रवत और जानकार AI मौसम विश्लेषक। "
    "आपको वास्तविक समय का मौसम डेटा दिया जाएगा जो लाइव वेदर API से लिया गया है। "
    "केवल इसी डेटा के आधार पर उत्तर दें — कोई मान गढ़ें नहीं। "
    "संक्षिप्त, स्पष्ट और व्यावहारिक रहें। जहाँ उपयुक्त हो, बुलेट पॉइंट का उपयोग करें। "
    "यदि गतिविधियों (दौड़, क्रिकेट, साइकिलिंग, यात्रा, कपड़े) के बारे में पूछा जाए, "
    "तो मौसम के आँकड़ों के आधार पर स्पष्ट सुझाव दें। "
    "यदि डेटा पर्याप्त न हो, तो ईमानदारी से कहें।"
)


def _build_prompt(
    user_query: str,
    weather_context: str,
    language: str,
) -> str:
    system = _SYSTEM_PROMPT_HI if language == "hi" else _SYSTEM_PROMPT_EN
    lang_note = (
        "IMPORTANT: Reply ENTIRELY in Hindi (Devanagari script)."
        if language == "hi"
        else "Reply in English."
    )
    return (
        f"{system}\n\n"
        f"--- LIVE WEATHER DATA ---\n{weather_context}\n"
        f"--- END WEATHER DATA ---\n\n"
        f"{lang_note}\n\n"
        f"User question: {user_query}"
    )


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

class AIAssistantError(Exception):
    """Raised when the AI assistant cannot produce a response."""
    pass


def ask(
    user_query: str,
    city: str,
    language: str = "en",
    comparison_cities: Optional[list[str]] = None,
) -> str:
    """Send *user_query* to Gemini with live weather context for *city*.

    Args:
        user_query:         The user's question.
        city:               Primary city to fetch weather for.
        language:           "en" (English) or "hi" (Hindi).
        comparison_cities:  Optional list of cities for multi-city comparison.

    Returns:
        A string with Gemini's response.

    Raises:
        AIAssistantError on any failure.
    """
    if not _init_gemini():
        raise AIAssistantError(
            "AI Assistant is not available. "
            "Please set GEMINI_API_KEY in your .env file and restart the app."
        )

    if not user_query or not user_query.strip():
        raise AIAssistantError("Please enter a question.")

    if len(user_query) > 1000:
        raise AIAssistantError("Question is too long (max 1000 characters).")

    # Build weather context
    if comparison_cities and len(comparison_cities) >= 2:
        weather_context, ctx_error = _build_comparison_context(comparison_cities)
    else:
        if not city or not city.strip():
            raise AIAssistantError(
                "Please enter a city name so I can fetch live weather data for your question."
            )
        weather_context, ctx_error = _build_weather_context(city.strip())

    if ctx_error:
        raise AIAssistantError(ctx_error)

    prompt = _build_prompt(user_query.strip(), weather_context, language)

    try:
        response = _gemini_model.generate_content(prompt)
        text = response.text.strip()
        if not text:
            raise AIAssistantError("Gemini returned an empty response. Please try again.")
        return text
    except AIAssistantError:
        raise
    except Exception as exc:
        logger.error("Gemini generation error: %s", exc)
        _handle_gemini_exception(exc)


def _handle_gemini_exception(exc: Exception) -> None:
    """Map Gemini SDK exceptions to user-friendly AIAssistantError messages."""
    msg = str(exc).lower()
    if "api_key" in msg or ("invalid" in msg and "key" in msg) or "authenticate" in msg or "api key" in msg:
        raise AIAssistantError(
            "Gemini API key is invalid or not authorised. "
            "Please check GEMINI_API_KEY in your .env file."
        )
    if "not found" in msg or "404" in msg:
        raise AIAssistantError(
            "Gemini model not available for this API key. "
            "Please check that your GEMINI_API_KEY is a valid Google AI Studio key."
        )
    if "quota" in msg or ("rate" in msg and "limit" in msg) or "429" in msg or "resource_exhausted" in msg:
        raise AIAssistantError(
            "Gemini API quota exceeded. Please wait a moment and try again."
        )
    if "timeout" in msg or "deadline" in msg:
        raise AIAssistantError(
            "Gemini request timed out. Please try again."
        )
    if "block" in msg or "safety" in msg or "harm" in msg:
        raise AIAssistantError(
            "Your question was blocked by Gemini's safety filters. Please rephrase it."
        )
    raise AIAssistantError(
        f"AI service error: {exc}. Please try again later."
    )


def gemini_available() -> bool:
    """Return True if Gemini is configured and ready."""
    return _init_gemini()

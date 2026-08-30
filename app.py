# app.py
"""WeatherIQ — Weather Analysis & Intelligence Dashboard.

Streamlit entry point and single error-catch boundary.
"""

import logging
from datetime import datetime, timezone

import streamlit as st

import config
from api_client import WeatherAPIError, fetch_comparison, fetch_current_weather, fetch_forecast
from analyzer import analyze
from chart_engine import (
    comparison_bar_chart,
    humidity_trend_chart,
    temperature_stats_chart,
    temperature_trend_chart,
    wind_speed_trend_chart,
)
from data_store import DataStoreError, init_db, load_historical_records, upsert_current_weather
from insight_engine import evaluate
from models import CurrentWeather, DailyForecast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="WeatherIQ",
    page_icon="WeatherIQ",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

:root {
    --bg: #070d18;
    --surface: #0d1626;
    --surface-2: #111d30;
    --line: #22324a;
    --text: #f4f7fb;
    --muted: #8c9ab0;
    --accent: #5b8cff;
    --accent-soft: rgba(91,140,255,.12);
    --green: #4ade80;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 8% 0%, rgba(91,140,255,.09), transparent 23%),
        radial-gradient(circle at 94% 10%, rgba(91,140,255,.055), transparent 21%),
        var(--bg);
    color: var(--text);
}

#MainMenu, footer, header, .stDeployButton { visibility: hidden; }

.block-container {
    max-width: 1240px;
    padding-top: .75rem;
    padding-bottom: 3rem;
}

/* ---------- Hero ---------- */
.hero-container {
    position: relative;
    overflow: hidden;
    margin: 0 0 1.25rem;
    padding: 1.35rem 1.5rem;
    border: 1px solid var(--line);
    border-radius: 18px;
    background: linear-gradient(135deg, #0e1a2c 0%, #0a1424 100%);
    box-shadow: 0 16px 42px rgba(0,0,0,.18);
}
.hero-container::before {
    content: "";
    position: absolute;
    width: 280px;
    height: 280px;
    right: -125px;
    top: -165px;
    border: 1px solid rgba(91,140,255,.16);
    border-radius: 50%;
    animation: drift 9s ease-in-out infinite;
}
.hero-container::after {
    content: "";
    position: absolute;
    width: 170px;
    height: 170px;
    right: -60px;
    top: -90px;
    border-radius: 50%;
    background: rgba(91,140,255,.08);
    animation: glow 6s ease-in-out infinite;
}
.hero-row {
    position: relative;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}
.hero-brand {
    color: var(--text);
    font-size: 2.15rem;
    font-weight: 700;
    letter-spacing: -.065em;
    line-height: 1;
}
.hero-brand span { color: #7ea4ff; }
.hero-tagline {
    margin-top: .48rem;
    color: var(--muted);
    font-size: .88rem;
}
.hero-meta {
    color: #9aa9bf;
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    text-align: right;
}
.live-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    margin-right: 6px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 4px rgba(74,222,128,.08);
    animation: pulse 2s ease-in-out infinite;
}

/* ---------- Sections ---------- */
.section-heading {
    display: flex;
    align-items: center;
    gap: .62rem;
    margin: 1.35rem 0 .65rem;
    color: #dbe4f1;
    font-size: .76rem;
    font-weight: 700;
    letter-spacing: .11em;
    text-transform: uppercase;
}
.section-heading::before {
    content: "";
    width: 4px;
    height: 16px;
    border-radius: 4px;
    background: var(--accent);
    box-shadow: 0 0 13px rgba(91,140,255,.3);
}

/* ---------- Native Streamlit inputs ---------- */
.stTextInput > div > div > input {
    min-height: 44px !important;
    border: 1px solid #2a3b55 !important;
    border-radius: 10px !important;
    background: #0a1423 !important;
    color: #f4f7fb !important;
    font-size: .9rem !important;
}
.stTextInput > div > div > input::placeholder { color: #66768d !important; }
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(91,140,255,.12) !important;
}
.stFormSubmitButton > button, .stButton > button {
    min-height: 44px !important;
    border-radius: 10px !important;
    border: 1px solid rgba(126,164,255,.24) !important;
    background: linear-gradient(135deg,#527ff0,#315fc9) !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-size: .85rem !important;
    transition: transform .16s ease, box-shadow .16s ease !important;
}
.stFormSubmitButton > button:hover, .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(49,95,201,.22);
}
label, .stMarkdown, .stCaption, .stTextInput label {
    color: #aebbd0 !important;
}

/* ---------- Search / current section backgrounds ---------- */
/* Streamlit's horizontal blocks are styled directly; no HTML wrapper around widgets. */
div[data-testid="stForm"] {
    padding: .72rem .78rem .78rem !important;
    border: 1px solid #22324a !important;
    border-radius: 14px !important;
    background: rgba(13,22,38,.78) !important;
    box-shadow: 0 10px 28px rgba(0,0,0,.12) !important;
}

/* ---------- Current weather cards ---------- */
.city-banner {
    position: relative;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: .65rem 1rem;
    margin-top: .25rem;
    padding: 1rem 1.1rem;
    border: 1px solid var(--line);
    border-radius: 15px;
    background: linear-gradient(135deg,#0e192b,#0b1524);
    box-shadow: 0 12px 32px rgba(0,0,0,.14);
    animation: rise .4s ease both;
}
.city-name {
    color: var(--text);
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -.04em;
}
.city-timestamp {
    color: #718199;
    font-size: .74rem;
}
.city-condition {
    margin-left: auto;
    padding: .34rem .7rem;
    border: 1px solid rgba(126,164,255,.23);
    border-radius: 999px;
    background: var(--accent-soft);
    color: #a8bfff;
    font-size: .71rem;
    font-weight: 600;
}
.metric-card {
    min-height: 88px;
    padding: .95rem 1rem;
    border: 1px solid #1f3047;
    border-radius: 13px;
    background: #0d1829;
    box-shadow: 0 8px 22px rgba(0,0,0,.11);
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
    animation: rise .45s ease both;
}
.metric-card:hover {
    transform: translateY(-3px);
    border-color: #31496b;
    box-shadow: 0 12px 25px rgba(0,0,0,.18);
}
.metric-label {
    margin-bottom: .4rem;
    color: #75849a;
    font-size: .64rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
}
.metric-value {
    color: #f7f9fc;
    font-size: 1.75rem;
    font-weight: 700;
}
.metric-value-sm {
    color: #eef3fa;
    font-size: 1.15rem;
    font-weight: 600;
}
.primary-temp {
    min-height: 88px;
    padding: .95rem 1rem;
    border: 1px solid rgba(91,140,255,.27);
    border-radius: 13px;
    background: linear-gradient(135deg,rgba(54,88,165,.32),#0d1829);
    box-shadow: 0 10px 26px rgba(0,0,0,.15);
}
.primary-temp .metric-label { color: #9cb3e9; }
.primary-temp .metric-value {
    font-size: 1.75rem;
    letter-spacing: -.04em;
}

/* ---------- Forecast ---------- */
.forecast-card {
    min-height: 120px;
    padding: .95rem .6rem;
    text-align: center;
    border: 1px solid #213149;
    border-radius: 12px;
    background: #0d1829;
    box-shadow: 0 7px 19px rgba(0,0,0,.10);
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
    animation: rise .45s ease both;
}
.forecast-card:hover {
    transform: translateY(-4px);
    border-color: #334b6c;
    box-shadow: 0 13px 26px rgba(0,0,0,.18);
}
.forecast-day {
    color: #aebbd0;
    font-size: .65rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
}
.forecast-date {
    margin: .27rem 0 .65rem;
    color: #63738b;
    font-size: .72rem;
}
.forecast-temp {
    color: #f6f8fb;
    font-size: 1.27rem;
    font-weight: 700;
}
.forecast-cond {
    margin-top: .32rem;
    color: #8291a7;
    font-size: .69rem;
}

/* ---------- Charts ---------- */
.chart-label {
    margin: .55rem 0 .25rem;
    color: #9eabc0;
    font-size: .69rem;
    font-weight: 700;
    letter-spacing: .09em;
    text-transform: uppercase;
}
.stPlotlyChart {
    border: 1px solid #1d2c41;
    border-radius: 13px;
    background: #0d1727;
    padding: .1rem;
    box-shadow: 0 8px 22px rgba(0,0,0,.14);
}

/* ---------- Insights / states ---------- */
.insight-card {
    margin-bottom: .6rem;
    padding: .9rem 1rem;
    border: 1px solid #263a56;
    border-left: 3px solid var(--accent);
    border-radius: 10px;
    background: #0d1a2c;
    color: #c6d2e3;
    font-size: .84rem;
    line-height: 1.5;
    animation: rise .4s ease both;
}
.empty-state {
    margin: .2rem 0;
    padding: 2.15rem 1.5rem;
    text-align: center;
    border: 1px dashed #2b3b54;
    border-radius: 14px;
    background: linear-gradient(145deg,#0c1727,#0a1423);
}
.empty-state-title {
    margin-bottom: .35rem;
    color: #dce5f2;
    font-size: .98rem;
    font-weight: 700;
}
.empty-state-body {
    max-width: 460px;
    margin: 0 auto;
    color: #73839a;
    font-size: .8rem;
    line-height: 1.5;
}
.status-error, .status-warning, .status-info {
    border-radius: 10px;
    padding: .82rem 1rem;
    font-size: .8rem;
}
.status-error {
    background:#281316;
    border:1px solid #5a252c;
    border-left:3px solid #ef5968;
    color:#f1a5ad;
}
.status-warning {
    background:#251d0e;
    border:1px solid #5a461d;
    border-left:3px solid #e5a83b;
    color:#e8c986;
}
.status-info {
    background:#0c1727;
    border:1px solid #24344b;
    color:#8291a7;
}

.stDataFrame {
    overflow: hidden;
    border: 1px solid #22324a !important;
    border-radius: 12px !important;
}

.stAlert { display: none !important; }

/* ---------- Motion ---------- */
@keyframes rise {
    from { opacity: 0; transform: translateY(7px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50% { opacity:.48; transform:scale(.82); }
}
@keyframes drift {
    0%,100% { transform: translate(0,0) rotate(0deg); }
    50% { transform: translate(-10px,12px) rotate(10deg); }
}
@keyframes glow {
    0%,100% { opacity:.65; transform:translate(0,0); }
    50% { opacity:1; transform:translate(-8px,10px); }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration:.01ms !important;
        animation-iteration-count:1 !important;
        transition-duration:.01ms !important;
    }
}
@media (max-width:800px) {
    .hero-row { align-items:flex-start; flex-direction:column; }
    .hero-meta { text-align:left; }
}
</style>
""", unsafe_allow_html=True)


# ── DB init ─────────────────────────────────────────────────────────────────

try:
    init_db()
except DataStoreError as _db_err:
    st.markdown(f'<div class="status-error">Database initialisation failed: {_db_err}</div>', unsafe_allow_html=True)
    st.stop()

# ── API key guard ────────────────────────────────────────────────────────────

if not config.WEATHER_API_KEY:
    st.markdown(
        '<div class="status-error">API key not configured. '
        'Set <code>WEATHER_API_KEY</code> in your <code>.env</code> file and restart the application.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Session state ─────────────────────────────────────────────────────────────

if "current_weather" not in st.session_state:
    st.session_state.current_weather = None
if "forecast" not in st.session_state:
    st.session_state.forecast = []
if "forecast_error" not in st.session_state:
    st.session_state.forecast_error = None
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = None


# ── Helper functions (logic unchanged) ───────────────────────────────────────

def validate_city_name(name: str):
    """Return an error message string, or None if the name is valid."""
    if not name or not name.strip():
        return "Please enter a city name."
    if len(name) > 100:
        return "City name must be 100 characters or fewer."
    return None


def validate_comparison_cities(raw: str):
    """Parse and validate a comma-separated list of 2–10 city names.

    Returns (list_of_cities, error_message). error_message is None on success.
    """
    cities = [c.strip() for c in raw.split(",") if c.strip()]
    if len(cities) < 2:
        return [], "Please enter at least 2 city names, separated by commas."
    if len(cities) > 10:
        return [], "You can compare a maximum of 10 cities at a time."
    for city in cities:
        if len(city) > 100:
            return [], f"City name '{city[:20]}...' exceeds 100 characters."
    return cities, None


def format_metric(value, formatter):
    """Return formatter(value) or 'N/A' when value is None."""
    if value is None:
        return "N/A"
    return formatter(value)


def _error_message_for(exc: WeatherAPIError) -> str:
    """Map a WeatherAPIError kind to a user-facing message (no key or trace)."""
    messages = {
        "not_found": "City not found. Please try a different name.",
        "auth": "API key configuration error. Please check your .env file.",
        "timeout": "Request timed out. Please try again.",
        "network": "Weather service is temporarily unavailable.",
        "unknown": "Could not retrieve weather data. Please try again later.",
    }
    return messages.get(exc.kind, "Could not retrieve weather data. Please try again later.")


def _format_timestamp(ts_utc: str) -> str:
    """Convert an ISO-8601 UTC string to 'DD Mon YYYY, HH:MM' local-time format."""
    try:
        dt = datetime.strptime(ts_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        local_dt = dt.astimezone()
        return local_dt.strftime("%d %b %Y, %H:%M")
    except (ValueError, OSError):
        return ts_utc


def _section(title: str) -> None:
    """Render a consistent section heading."""
    st.markdown(f'<div class="section-heading">{title}</div>', unsafe_allow_html=True)


def _info(msg: str) -> None:
    st.markdown(f'<div class="status-info">{msg}</div>', unsafe_allow_html=True)


def _warn(msg: str) -> None:
    st.markdown(f'<div class="status-warning">{msg}</div>', unsafe_allow_html=True)


def _err(msg: str) -> None:
    st.markdown(f'<div class="status-error">{msg}</div>', unsafe_allow_html=True)


def _style_chart(fig):
    """Apply the WeatherIQ dark visual theme to an existing Plotly figure."""
    if fig is None:
        return None
    try:
        fig.update_layout(
            paper_bgcolor="#0d1727",
            plot_bgcolor="#0d1727",
            font=dict(color="#cbd5e1", family="DM Sans, sans-serif"),
            margin=dict(l=42, r=20, t=35, b=42),
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(color="#aebbd0"),
            ),
        )
        fig.update_xaxes(
            gridcolor="#1e2d42",
            zerolinecolor="#1e2d42",
            linecolor="#2a3a52",
            tickfont=dict(color="#8291a7"),
            title_font=dict(color="#9eabc0"),
        )
        fig.update_yaxes(
            gridcolor="#1e2d42",
            zerolinecolor="#1e2d42",
            linecolor="#2a3a52",
            tickfont=dict(color="#8291a7"),
            title_font=dict(color="#9eabc0"),
        )
    except Exception:
        pass
    return fig


def _metric_card(label: str, value: str) -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value-sm">{value}</div>
    </div>"""


# ── Hero header ───────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero-container">
    <div class="hero-row">
        <div>
            <div class="hero-brand">Weather<span>IQ</span></div>
            <div class="hero-tagline">Weather analysis and intelligence dashboard</div>
        </div>
        <div class="hero-meta"><span class="live-dot"></span>Live Weather &nbsp;·&nbsp; Forecast &nbsp;·&nbsp; Analytics</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── SECTION: Search ───────────────────────────────────────────────────────────

_section("Search")

search_col, _ = st.columns([3, 0.02])
with search_col:
    with st.form("city_search_form", clear_on_submit=False):
        city_input = st.text_input(
            "City",
            placeholder="Enter a city name — e.g. London, Tokyo, New York",
            max_chars=100,
            label_visibility="collapsed",
        )
        search_submitted = st.form_submit_button("Get Weather", use_container_width=True)

if search_submitted:
    validation_error = validate_city_name(city_input)
    if validation_error:
        _err(validation_error)
    else:
        with st.spinner(f"Fetching weather data for {city_input.strip()}..."):
            try:
                cw = fetch_current_weather(city_input.strip())
                st.session_state.current_weather = cw
            except WeatherAPIError as exc:
                _err(_error_message_for(exc))
                st.session_state.current_weather = None
                st.session_state.forecast = []
                st.session_state.forecast_error = None
                st.stop()

            try:
                upsert_current_weather(cw)
            except DataStoreError as exc:
                _warn(f"Could not save weather data locally: {exc}")

            try:
                st.session_state.forecast = fetch_forecast(city_input.strip())
                st.session_state.forecast_error = None
            except WeatherAPIError as exc:
                st.session_state.forecast = []
                st.session_state.forecast_error = _error_message_for(exc)


# ── SECTION: Current Weather ──────────────────────────────────────────────────

_section("Current Weather")

cw: CurrentWeather = st.session_state.current_weather

if cw is None:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-title">No city selected</div>
        <div class="empty-state-body">Enter a city name in the search box above to view current weather conditions, forecasts, and analytics.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    # City banner
    condition_badge = f'<span class="city-condition">{cw.condition}</span>' if cw.condition else ""
    st.markdown(f"""
    <div class="city-banner">
        <span class="city-name">{cw.city}</span>
        <span class="city-timestamp">Observed {_format_timestamp(cw.timestamp_utc)}</span>
        {condition_badge}
    </div>
    """, unsafe_allow_html=True)

    # Row 1 — temperature, feels like, humidity, wind speed
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        temp_value = format_metric(cw.temperature, lambda v: f"{v:.1f} °C")
        st.markdown(
            f'<div class="primary-temp"><div class="metric-label">Temperature</div><div class="metric-value">{temp_value}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(_metric_card("Feels Like", format_metric(cw.feels_like, lambda v: f"{v:.1f} °C")), unsafe_allow_html=True)
    with c3:
        st.markdown(_metric_card("Humidity", format_metric(cw.humidity, lambda v: f"{int(round(v))} %")), unsafe_allow_html=True)
    with c4:
        st.markdown(_metric_card("Wind Speed", format_metric(cw.wind_speed, lambda v: f"{v:.1f} km/h")), unsafe_allow_html=True)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # Row 2 — pressure, visibility (condition shown in banner)
    c5, c6, _, _ = st.columns(4)
    with c5:
        st.markdown(_metric_card("Pressure", format_metric(cw.pressure, lambda v: f"{int(round(v))} hPa")), unsafe_allow_html=True)
    with c6:
        st.markdown(_metric_card("Visibility", format_metric(cw.visibility, lambda v: f"{min(v, 10.0):.1f} km")), unsafe_allow_html=True)


# ── SECTION: Forecast ─────────────────────────────────────────────────────────

_section("5-Day Forecast")

if cw is None:
    _info("Search for a city to see its forecast.")
elif st.session_state.forecast_error:
    _warn(f"Forecast unavailable: {st.session_state.forecast_error}")
elif not st.session_state.forecast:
    _info("No forecast data is available for this city.")
else:
    forecast_list = sorted(st.session_state.forecast, key=lambda d: d.date)
    n = min(len(forecast_list), 7)
    cols = st.columns(n)
    for i, fc in enumerate(forecast_list[:n]):
        try:
            date_obj = datetime.strptime(fc.date, "%Y-%m-%d")
            day_name = date_obj.strftime("%a").upper()
            date_str = date_obj.strftime("%d %b")
        except ValueError:
            day_name = fc.date
            date_str = ""
        temp_str = format_metric(fc.temperature, lambda v: f"{v:.1f} °C")
        cond_str = fc.condition or "—"
        cols[i].markdown(f"""
        <div class="forecast-card">
            <div class="forecast-day">{day_name}</div>
            <div class="forecast-date">{date_str}</div>
            <div class="forecast-temp">{temp_str}</div>
            <div class="forecast-cond">{cond_str}</div>
        </div>
        """, unsafe_allow_html=True)


# ── SECTION: Analysis & Charts ────────────────────────────────────────────────

_section("Analysis & Charts")

if cw is None:
    _info("Search for a city to see historical weather analysis.")
else:
    records = load_historical_records(cw.city)
    result = analyze(records)

    if result.error:
        _err(f"Analysis error: {result.error}")
    elif result.is_empty:
        _info("No historical data yet for this city. Search for this city again in a few minutes to start building a history.")
    else:
        # Temperature trend — full width
        st.markdown('<div class="chart-label">Temperature Trend</div>', unsafe_allow_html=True)
        temp_fig = temperature_trend_chart(result.trend_temperature)
        if temp_fig:
            st.plotly_chart(_style_chart(temp_fig), use_container_width=True, config={"displayModeBar": False})
        else:
            _info("Insufficient data to plot a temperature trend.")

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        # Humidity + Wind side by side
        col_h, col_w = st.columns(2)
        with col_h:
            st.markdown('<div class="chart-label">Humidity Trend</div>', unsafe_allow_html=True)
            hum_fig = humidity_trend_chart(result.trend_humidity)
            if hum_fig:
                st.plotly_chart(_style_chart(hum_fig), use_container_width=True, config={"displayModeBar": False})
            else:
                _info("Insufficient data to plot a humidity trend.")

        with col_w:
            st.markdown('<div class="chart-label">Wind Speed Trend</div>', unsafe_allow_html=True)
            wind_fig = wind_speed_trend_chart(result.trend_wind_speed)
            if wind_fig:
                st.plotly_chart(_style_chart(wind_fig), use_container_width=True, config={"displayModeBar": False})
            else:
                _info("Insufficient data to plot a wind speed trend.")

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        # Stats bar chart — half width
        stats_col, _ = st.columns([1, 1])
        with stats_col:
            st.markdown('<div class="chart-label">Temperature Statistics</div>', unsafe_allow_html=True)
            stats_fig = temperature_stats_chart(result.stats)
            if stats_fig:
                st.plotly_chart(_style_chart(stats_fig), use_container_width=True, config={"displayModeBar": False})
            else:
                _info("Insufficient data for temperature statistics.")


# ── SECTION: City Comparison ──────────────────────────────────────────────────

_section("City Comparison")

comp_col, _ = st.columns([3, 0.02])
with comp_col:
    with st.form("comparison_form", clear_on_submit=False):
        comparison_input = st.text_input(
            "Cities",
            placeholder="e.g. London, Paris, Tokyo, New York",
            label_visibility="collapsed",
        )
        compare_submitted = st.form_submit_button("Compare Cities", use_container_width=True)

if compare_submitted:
    cities, val_error = validate_comparison_cities(comparison_input)
    if val_error:
        _err(val_error)
        st.session_state.comparison_results = None
    else:
        with st.spinner("Fetching weather data for all cities..."):
            st.session_state.comparison_results = fetch_comparison(cities)

comp_results = st.session_state.comparison_results

if comp_results is None:
    _info("Enter 2 to 10 city names separated by commas, then click Compare Cities.")
else:
    successful = {
        city: data
        for city, data in comp_results.items()
        if isinstance(data, CurrentWeather)
    }
    failed = {
        city: data
        for city, data in comp_results.items()
        if isinstance(data, WeatherAPIError)
    }

    for city, exc in failed.items():
        _warn(f"{city}: {_error_message_for(exc)}")

    if not successful:
        _err("Could not retrieve weather data for any of the specified cities.")
    else:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        table_data = {
            "City": list(successful.keys()),
            "Temperature (°C)": [
                format_metric(d.temperature, lambda v: f"{v:.1f}") for d in successful.values()
            ],
            "Humidity (%)": [
                format_metric(d.humidity, lambda v: f"{int(round(v))}") for d in successful.values()
            ],
            "Wind Speed (km/h)": [
                format_metric(d.wind_speed, lambda v: f"{v:.1f}") for d in successful.values()
            ],
        }
        st.dataframe(table_data, use_container_width=True, hide_index=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        city_names = list(successful.keys())
        temp_values = [d.temperature for d in successful.values()]
        hum_values = [d.humidity for d in successful.values()]
        wind_values = [d.wind_speed for d in successful.values()]

        chart_col1, chart_col2, chart_col3 = st.columns(3)

        with chart_col1:
            st.markdown('<div class="chart-label">Temperature (°C)</div>', unsafe_allow_html=True)
            fig = comparison_bar_chart(city_names, temp_values, "Temperature", "°C")
            if fig:
                st.plotly_chart(_style_chart(fig), use_container_width=True, config={"displayModeBar": False})

        with chart_col2:
            st.markdown('<div class="chart-label">Humidity (%)</div>', unsafe_allow_html=True)
            fig = comparison_bar_chart(city_names, hum_values, "Humidity", "%")
            if fig:
                st.plotly_chart(_style_chart(fig), use_container_width=True, config={"displayModeBar": False})

        with chart_col3:
            st.markdown('<div class="chart-label">Wind Speed (km/h)</div>', unsafe_allow_html=True)
            fig = comparison_bar_chart(city_names, wind_values, "Wind Speed", "km/h")
            if fig:
                st.plotly_chart(_style_chart(fig), use_container_width=True, config={"displayModeBar": False})


# ── SECTION: Insights ─────────────────────────────────────────────────────────

if cw is not None:
    recent_history = load_historical_records(cw.city)
    two_most_recent = recent_history[-2:] if len(recent_history) >= 2 else recent_history
    insights = evaluate(cw, two_most_recent)

    if insights:
        _section("Weather Insights")
        for insight in insights:
            st.markdown(
                f'<div class="insight-card">{insight.message}</div>',
                unsafe_allow_html=True,
            )
    # Requirement 8.7: render nothing when no insights

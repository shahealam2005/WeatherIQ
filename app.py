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
    page_title="WeatherIQ — Dashboard",
    page_icon="🌤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');

:root {
    --bg:           #F5F9FC;
    --surface:      #FFFFFF;
    --surface-2:    #F0F5F9;
    --border:       #E2E8F0;
    --border-strong:#CBD5E1;
    --text:         #172033;
    --text-2:       #64748B;
    --text-3:       #94A3B8;
    --teal:         #0EA5A4;
    --teal-soft:    rgba(14,165,164,.10);
    --teal-mid:     rgba(14,165,164,.18);
    --blue:         #2563EB;
    --blue-soft:    rgba(37,99,235,.09);
    --violet:       #7C3AED;
    --violet-soft:  rgba(124,58,237,.09);
    --amber:        #F59E0B;
    --amber-soft:   rgba(245,158,11,.10);
    --green:        #10B981;
    --red:          #EF4444;
    --shadow-sm:    0 1px 3px rgba(23,32,51,.06), 0 1px 2px rgba(23,32,51,.04);
    --shadow-md:    0 4px 12px rgba(23,32,51,.08), 0 2px 4px rgba(23,32,51,.04);
    --shadow-lg:    0 8px 24px rgba(23,32,51,.09), 0 3px 8px rgba(23,32,51,.05);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', system-ui, -apple-system, sans-serif;
}

.stApp {
    background: var(--bg);
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
    margin: 0 0 1rem;
    padding: 1.4rem 1.75rem;
    border: 1px solid var(--border);
    border-radius: 18px;
    background: var(--surface);
    box-shadow: var(--shadow-md);
}
.hero-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}
.hero-brand {
    color: var(--text);
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -.06em;
    line-height: 1;
}
.hero-brand span { color: var(--teal); }
.hero-tagline {
    margin-top: .45rem;
    color: var(--text-2);
    font-size: .88rem;
}
.hero-meta {
    display: flex;
    align-items: center;
    gap: .5rem;
    color: var(--text-2);
    font-size: .7rem;
    font-weight: 600;
    letter-spacing: .07em;
    text-transform: uppercase;
}
.live-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 3px rgba(16,185,129,.18);
    animation: pulse 2.2s ease-in-out infinite;
}

/* ---------- Section headings ---------- */
.section-heading {
    display: flex;
    align-items: center;
    gap: .55rem;
    margin: 1.4rem 0 .7rem;
    color: var(--text-2);
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
}
.section-heading::before {
    content: "";
    width: 3px;
    height: 14px;
    border-radius: 3px;
    background: var(--teal);
}

/* ---------- Streamlit inputs ---------- */
.stTextInput > div > div > input {
    min-height: 44px !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 10px !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    font-size: .9rem !important;
    box-shadow: var(--shadow-sm) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--text-3) !important; }
.stTextInput > div > div > input:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 3px var(--teal-soft) !important;
}
.stFormSubmitButton > button, .stButton > button {
    min-height: 44px !important;
    border-radius: 10px !important;
    border: none !important;
    background: var(--teal) !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-size: .875rem !important;
    letter-spacing: .01em !important;
    transition: background .15s ease, box-shadow .15s ease, transform .15s ease !important;
    box-shadow: 0 2px 8px rgba(14,165,164,.28) !important;
}
.stFormSubmitButton > button:hover, .stButton > button:hover {
    background: #0b9090 !important;
    box-shadow: 0 4px 14px rgba(14,165,164,.36) !important;
    transform: translateY(-1px) !important;
}
label, .stMarkdown, .stCaption { color: var(--text-2) !important; }
.stTextInput label { color: var(--text-2) !important; }

div[data-testid="stForm"] {
    padding: .8rem .9rem !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    background: var(--surface) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ---------- Current weather ---------- */
.city-banner {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: .6rem 1rem;
    margin-top: .2rem;
    padding: 1rem 1.25rem;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: var(--surface);
    box-shadow: var(--shadow-sm);
    animation: rise .35s ease both;
}
.city-name {
    color: var(--text);
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -.04em;
}
.city-timestamp {
    color: var(--text-3);
    font-size: .74rem;
}
.city-condition {
    margin-left: auto;
    padding: .3rem .75rem;
    border: 1px solid var(--teal-mid);
    border-radius: 999px;
    background: var(--teal-soft);
    color: var(--teal);
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .04em;
}
.metric-card {
    min-height: 90px;
    padding: 1rem 1.1rem;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--surface);
    box-shadow: var(--shadow-sm);
    transition: box-shadow .18s ease, transform .18s ease, border-color .18s ease;
    animation: rise .4s ease both;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--border-strong);
}
.metric-label {
    margin-bottom: .38rem;
    color: var(--text-3);
    font-size: .63rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
}
.metric-value {
    color: var(--text);
    font-size: 1.7rem;
    font-weight: 700;
    letter-spacing: -.03em;
}
.metric-value-sm {
    color: var(--text);
    font-size: 1.15rem;
    font-weight: 600;
}
.primary-temp {
    min-height: 90px;
    padding: 1rem 1.1rem;
    border: 1px solid var(--teal-mid);
    border-radius: 12px;
    background: var(--teal-soft);
    box-shadow: var(--shadow-sm);
    animation: rise .4s ease both;
}
.primary-temp .metric-label { color: var(--teal); }
.primary-temp .metric-value { color: var(--teal); font-size: 1.7rem; }

/* ---------- Forecast ---------- */
.forecast-card {
    min-height: 122px;
    padding: 1rem .7rem;
    text-align: center;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--surface);
    box-shadow: var(--shadow-sm);
    transition: box-shadow .18s ease, transform .18s ease, border-color .18s ease;
    animation: rise .4s ease both;
}
.forecast-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
    border-color: var(--teal-mid);
}
.forecast-day {
    color: var(--text-2);
    font-size: .63rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
}
.forecast-date {
    margin: .25rem 0 .6rem;
    color: var(--text-3);
    font-size: .72rem;
}
.forecast-temp {
    color: var(--text);
    font-size: 1.22rem;
    font-weight: 700;
    letter-spacing: -.02em;
}
.forecast-cond {
    margin-top: .3rem;
    color: var(--text-3);
    font-size: .68rem;
}

/* ---------- Charts ---------- */
.chart-label {
    margin: .5rem 0 .2rem;
    color: var(--text-3);
    font-size: .67rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
}
.stPlotlyChart {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    background: var(--surface) !important;
    box-shadow: var(--shadow-sm) !important;
    overflow: hidden;
}

/* ---------- Motion ---------- */
.insight-card {
    margin-bottom: .55rem;
    padding: .9rem 1.1rem;
    border: 1px solid var(--border);
    border-left: 3px solid var(--teal);
    border-radius: 10px;
    background: var(--surface);
    color: var(--text-2);
    font-size: .84rem;
    line-height: 1.55;
    animation: rise .35s ease both;
}

/* ---------- Empty / status states ---------- */
.empty-state {
    margin: .2rem 0;
    padding: 2.2rem 1.5rem;
    text-align: center;
    border: 1px dashed var(--border-strong);
    border-radius: 14px;
    background: var(--surface);
}
.empty-state-title {
    margin-bottom: .35rem;
    color: var(--text);
    font-size: 1rem;
    font-weight: 600;
}
.empty-state-body {
    max-width: 460px;
    margin: 0 auto;
    color: var(--text-2);
    font-size: .82rem;
    line-height: 1.55;
}
.status-error, .status-warning, .status-info {
    border-radius: 10px;
    padding: .82rem 1rem;
    font-size: .82rem;
    margin: .3rem 0;
}
.status-error {
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-left: 3px solid var(--red);
    color: #B91C1C;
}
.status-warning {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-left: 3px solid var(--amber);
    color: #92400E;
}
.status-info {
    background: var(--teal-soft);
    border: 1px solid var(--teal-mid);
    color: #0F6B6A;
}

.stDataFrame {
    overflow: hidden;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

.stAlert { display: none !important; }

/* ---------- Insights ---------- */
.insight-card {
    margin-bottom: .55rem;
    padding: .9rem 1.1rem;
    border: 1px solid var(--border);
    border-left: 3px solid var(--teal);
    border-radius: 10px;
    background: var(--surface);
    color: var(--text-2);
    font-size: .84rem;
    line-height: 1.55;
    animation: rise .35s ease both;
}

/* ---------- AI Assistant card button ---------- */
.ai-nav-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: .9rem;
    padding: .8rem 1.1rem;
    border: 1px solid rgba(124,58,237,.22);
    border-radius: 12px;
    background: rgba(124,58,237,.04);
    cursor: pointer;
    text-decoration: none;
    transition: border-color .15s ease, background .15s ease, box-shadow .15s ease;
}
.ai-nav-card:hover {
    border-color: rgba(124,58,237,.5);
    background: rgba(124,58,237,.08);
    box-shadow: 0 4px 14px rgba(124,58,237,.10);
}
.ai-nav-left {
    display: flex;
    align-items: center;
    gap: .6rem;
}
.ai-nav-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #7C3AED;
    box-shadow: 0 0 0 3px rgba(124,58,237,.18);
    animation: pulse 2.2s ease-in-out infinite;
    flex-shrink: 0;
}
.ai-nav-text {
    color: #6D28D9;
    font-size: .84rem;
    font-weight: 600;
}
.ai-nav-cta {
    display: inline-flex;
    align-items: center;
    gap: .3rem;
    padding: .3rem .75rem;
    border: 1px solid rgba(124,58,237,.35);
    border-radius: 999px;
    background: #7C3AED;
    color: #fff;
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .03em;
    white-space: nowrap;
    transition: background .14s ease;
}
.ai-nav-card:hover .ai-nav-cta {
    background: #6D28D9;
}
@keyframes rise {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%     { opacity:.5; transform:scale(.85); }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration:.01ms !important;
        animation-iteration-count:1 !important;
        transition-duration:.01ms !important;
    }
}
@media (max-width:800px) {
    .hero-row { flex-direction:column; align-items:flex-start; }
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
    """Apply the WeatherIQ light visual theme to an existing Plotly figure."""
    if fig is None:
        return None
    try:
        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(color="#64748B", family="DM Sans, sans-serif"),
            margin=dict(l=42, r=20, t=35, b=42),
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(color="#64748B"),
            ),
        )
        fig.update_xaxes(
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
            linecolor="#E2E8F0",
            tickfont=dict(color="#94A3B8"),
            title_font=dict(color="#64748B"),
        )
        fig.update_yaxes(
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
            linecolor="#E2E8F0",
            tickfont=dict(color="#94A3B8"),
            title_font=dict(color="#64748B"),
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
        <div class="hero-meta">
            <span class="live-dot"></span>
            Live Weather &nbsp;·&nbsp; Forecast &nbsp;·&nbsp; Analytics
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# AI Assistant nav card (clickable, navigates to page 2)
st.markdown("""
<a class="ai-nav-card" href="/2_AI_Assistant" target="_self">
    <div class="ai-nav-left">
        <div class="ai-nav-dot"></div>
        <span class="ai-nav-text">AI Weather Assistant powered by Gemini</span>
    </div>
    <span class="ai-nav-cta">Open AI Assistant →</span>
</a>
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

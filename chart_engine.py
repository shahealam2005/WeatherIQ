# chart_engine.py
"""Plotly chart builders for the WeatherIQ dashboard."""

from typing import Optional
import plotly.graph_objects as go

# ── Shared theme ────────────────────────────────────────────────────────────
_FONT = dict(family="Inter, system-ui, sans-serif", color="#1e293b")
_TRANSPARENT = "rgba(0,0,0,0)"
_GRID_COLOR = "#e2e8f0"
_AXIS_STYLE = dict(
    showgrid=True,
    gridcolor=_GRID_COLOR,
    gridwidth=1,
    zeroline=False,
    linecolor="#cbd5e1",
    tickfont=dict(size=11, color="#64748b"),
)
_MARGIN = dict(l=50, r=20, t=20, b=50)


def _base_layout(**kwargs) -> dict:
    return dict(
        font=_FONT,
        paper_bgcolor=_TRANSPARENT,
        plot_bgcolor=_TRANSPARENT,
        margin=_MARGIN,
        xaxis=dict(**_AXIS_STYLE, title_font=dict(size=12, color="#475569")),
        yaxis=dict(**_AXIS_STYLE, title_font=dict(size=12, color="#475569")),
        showlegend=False,
        **kwargs,
    )


def _line_chart(series: list, y_title: str, color: str = "#2563eb") -> Optional[go.Figure]:
    """Build a styled line chart. Returns None if fewer than 2 valid points."""
    valid = [p for p in series if p.get("value") is not None]
    if len(valid) < 2:
        return None

    x = [p["timestamp"] for p in valid]
    y = [p["value"] for p in valid]

    fig = go.Figure(
        go.Scatter(
            x=x,
            y=y,
            mode="lines+markers",
            line=dict(color=color, width=2.5, shape="spline", smoothing=0.8),
            marker=dict(size=6, color=color, line=dict(width=2, color="#ffffff")),
            hovertemplate="%{y}<extra></extra>",
        )
    )
    layout = _base_layout(hovermode="x unified")
    layout["xaxis"]["title"] = "Date / Time"
    layout["yaxis"]["title"] = y_title
    fig.update_layout(**layout)
    return fig


def temperature_trend_chart(series: list) -> Optional[go.Figure]:
    """Line chart: Temperature (°C) over time."""
    return _line_chart(series, y_title="Temperature (°C)", color="#ef4444")


def humidity_trend_chart(series: list) -> Optional[go.Figure]:
    """Line chart: Humidity (%) over time."""
    return _line_chart(series, y_title="Humidity (%)", color="#3b82f6")


def wind_speed_trend_chart(series: list) -> Optional[go.Figure]:
    """Line chart: Wind Speed (km/h) over time."""
    return _line_chart(series, y_title="Wind Speed (km/h)", color="#10b981")


def temperature_stats_chart(stats: dict) -> Optional[go.Figure]:
    """Bar chart: min / max / mean temperature."""
    if not stats or "temperature" not in stats:
        return None
    t = stats["temperature"]
    if all(v is None for v in (t.get("min"), t.get("max"), t.get("mean"))):
        return None

    categories = ["Min", "Max", "Mean"]
    values = [t.get("min"), t.get("max"), t.get("mean")]
    colors = ["#64748b", "#ef4444", "#2563eb"]

    fig = go.Figure(
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            marker_line_width=0,
            text=[f"{v:.1f}" if v is not None else "N/A" for v in values],
            textposition="outside",
            textfont=dict(size=12, color="#1e293b"),
            hovertemplate="%{x}: %{y:.1f} °C<extra></extra>",
        )
    )
    layout = _base_layout(hovermode="closest")
    layout["xaxis"]["title"] = "Statistic"
    layout["yaxis"]["title"] = "Temperature (°C)"
    fig.update_layout(**layout)
    return fig


def comparison_bar_chart(
    cities: list,
    values: list,
    metric_name: str,
    unit: str,
) -> Optional[go.Figure]:
    """Bar chart: one bar per city for a single metric."""
    if not cities or not values:
        return None

    color_map = {"Temperature": "#ef4444", "Humidity": "#3b82f6", "Wind Speed": "#10b981"}
    bar_color = color_map.get(metric_name, "#2563eb")

    fig = go.Figure(
        go.Bar(
            x=cities,
            y=values,
            marker_color=bar_color,
            marker_line_width=0,
            text=[f"{v:.1f}" if v is not None else "N/A" for v in values],
            textposition="outside",
            textfont=dict(size=11, color="#1e293b"),
            hovertemplate="%{x}: %{y:.1f}<extra></extra>",
        )
    )
    layout = _base_layout(hovermode="closest")
    layout["xaxis"]["title"] = "City"
    layout["yaxis"]["title"] = f"{metric_name} ({unit})"
    fig.update_layout(**layout)
    return fig

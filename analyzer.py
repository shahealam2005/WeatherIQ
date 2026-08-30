# analyzer.py
"""Pandas-based weather data analyzer."""

import logging
from typing import Optional

import pandas as pd

from models import AnalysisResult

logger = logging.getLogger(__name__)

_NUMERIC_COLS = ["temperature", "humidity", "wind_speed"]


def analyze(records: list) -> AnalysisResult:
    """Compute statistics and trend series for a city's historical records.

    Returns:
        AnalysisResult with is_empty=True  if records is empty.
        AnalysisResult with error set       if data is malformed.
        AnalysisResult with populated stats and trend series otherwise.

    All computations use only in-memory Pandas operations.
    """
    if not records:
        return AnalysisResult(is_empty=True)

    try:
        df = pd.DataFrame(records)

        # Validate required columns are present
        missing = [c for c in ["timestamp_utc"] + _NUMERIC_COLS if c not in df.columns]
        if missing:
            raise KeyError(f"Missing required columns: {missing}")

        # Coerce numeric columns — non-numeric values become NaN
        for col in _NUMERIC_COLS:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Sort by timestamp ascending
        df = df.sort_values("timestamp_utc").reset_index(drop=True)

        # --- Statistics ---
        stats: dict = {}
        for col in _NUMERIC_COLS:
            series = df[col].dropna()
            if series.empty:
                stats[col] = {"min": None, "max": None, "mean": None}
            else:
                stats[col] = {
                    "min": round(float(series.min()), 2),
                    "max": round(float(series.max()), 2),
                    "mean": round(float(series.mean()), 2),
                }

        # --- Trend series ---
        def _build_trend(col: str) -> list:
            return [
                {"timestamp": row["timestamp_utc"], "value": row[col]}
                for _, row in df[["timestamp_utc", col]].dropna().iterrows()
            ]

        return AnalysisResult(
            stats=stats,
            trend_temperature=_build_trend("temperature"),
            trend_humidity=_build_trend("humidity"),
            trend_wind_speed=_build_trend("wind_speed"),
        )

    except Exception as exc:
        logger.error("Analyzer error: %s", exc)
        return AnalysisResult(error=str(exc))

# data_store.py
"""SQLite data store — persists and retrieves historical weather records."""

import logging
import os
import sqlite3
from datetime import datetime, timezone

import config
from models import CurrentWeather

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class DataStoreError(Exception):
    """Raised when a database operation fails."""
    pass


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS historical_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    city            TEXT    NOT NULL,
    timestamp_utc   TEXT    NOT NULL,
    temperature     REAL,
    feels_like      REAL,
    humidity        INTEGER,
    wind_speed      REAL,
    pressure        INTEGER,
    visibility      REAL,
    condition       TEXT,
    UNIQUE (city, timestamp_utc) ON CONFLICT REPLACE
);
"""

# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _get_connection() -> sqlite3.Connection:
    """Open a connection to the configured database file."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def init_db() -> None:
    """Create the database file and table if they do not already exist.

    Logs an initialisation event when a new database file is created.
    """
    db_existed = os.path.exists(config.DB_PATH) if config.DB_PATH != ":memory:" else True
    try:
        conn = _get_connection()
        conn.execute(_CREATE_TABLE_SQL)
        conn.commit()
        conn.close()
    except sqlite3.Error as exc:
        raise DataStoreError(f"Failed to initialise database: {exc}") from exc

    if not db_existed:
        logger.info(
            "Database initialised: path=%s, timestamp=%s",
            config.DB_PATH,
            datetime.now(timezone.utc).isoformat(),
        )


def upsert_current_weather(record: CurrentWeather) -> None:
    """Atomically insert or replace a weather record.

    Uses INSERT OR REPLACE so that a duplicate (city, timestamp_utc) pair
    overwrites the existing row within a single transaction.

    Raises DataStoreError on any sqlite3 error.
    """
    sql = """
    INSERT OR REPLACE INTO historical_records
        (city, timestamp_utc, temperature, feels_like, humidity,
         wind_speed, pressure, visibility, condition)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        conn = _get_connection()
        conn.execute(
            sql,
            (
                record.city,
                record.timestamp_utc,
                record.temperature,
                record.feels_like,
                record.humidity,
                record.wind_speed,
                record.pressure,
                record.visibility,
                record.condition,
            ),
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as exc:
        raise DataStoreError(f"Failed to save weather record: {exc}") from exc


def load_historical_records(city: str) -> list:
    """Return all historical records for *city* as a list of plain dicts.

    Returns an empty list if no records exist.
    """
    sql = """
    SELECT city, timestamp_utc, temperature, feels_like, humidity,
           wind_speed, pressure, visibility, condition
    FROM historical_records
    WHERE city = ?
    ORDER BY timestamp_utc ASC
    """
    try:
        conn = _get_connection()
        cursor = conn.execute(sql, (city,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
    except sqlite3.Error as exc:
        raise DataStoreError(f"Failed to load historical records: {exc}") from exc

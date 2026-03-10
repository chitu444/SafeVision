"""
database/db.py
==============
SQLite connection helpers, schema normalisation / migration, and all
incident CRUD operations.  No Streamlit imports here — keep this module
pure-Python so it can be used in background threads without issues.
"""

import json
import sqlite3
import time
from typing import Optional

import pandas as pd

from config.settings import INCIDENT_DB_PATH


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with busy-timeout pre-set."""
    conn = sqlite3.connect(INCIDENT_DB_PATH, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def _configure_wal_once() -> None:
    """Enable WAL journal mode (best-effort — tolerates short lock contention)."""
    for _ in range(5):
        conn = None
        try:
            conn = get_connection()
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.commit()
            return
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            time.sleep(0.2)
        finally:
            if conn is not None:
                conn.close()


# ---------------------------------------------------------------------------
# Schema normalisation
# ---------------------------------------------------------------------------

def _normalize_schema(conn: sqlite3.Connection) -> None:
    """
    Migrate any legacy incidents table into the canonical schema:
        id, ts, source, total_persons, safe_count, unsafe_count, details_json
    A timestamped backup of the old table is preserved.
    """
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='incidents'")
    if cur.fetchone() is None:
        cur.execute(
            """
            CREATE TABLE incidents (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ts            TEXT    NOT NULL,
                source        TEXT    NOT NULL,
                total_persons INTEGER NOT NULL DEFAULT 0,
                safe_count    INTEGER NOT NULL DEFAULT 0,
                unsafe_count  INTEGER NOT NULL DEFAULT 0,
                details_json  TEXT
            )
            """
        )
        conn.commit()
        return

    cur.execute("PRAGMA table_info(incidents)")
    table_info = cur.fetchall()
    existing_cols = [row[1] for row in table_info]
    canonical = ["id", "ts", "source", "total_persons", "safe_count", "unsafe_count", "details_json"]

    if existing_cols == canonical:
        return  # already up-to-date

    has = set(existing_cols).__contains__

    ts_expr      = "COALESCE(ts, ts_text, datetime('now','localtime'))" if has("ts_text") else "COALESCE(ts, datetime('now','localtime'))"
    source_expr  = "COALESCE(source, 'unknown')"
    total_expr   = "COALESCE(total_persons, 0)" if has("total_persons") else "0"
    unsafe_expr  = "COALESCE(unsafe_count, 0)" if has("unsafe_count") else "0"
    safe_expr    = (
        "COALESCE(safe_count, MAX(COALESCE(total_persons,0)-COALESCE(unsafe_count,0),0),0)"
        if has("safe_count") else
        "MAX(COALESCE(total_persons,0)-COALESCE(unsafe_count,0),0)"
        if (has("total_persons") and has("unsafe_count")) else "0"
    )

    if has("details_json"):
        details_expr = "details_json"
    else:
        parts = []
        for col in ("camera_id", "track_ids", "reasons", "channels", "snapshot_path"):
            if has(col):
                parts.append(f"'{col}', {col}")
        details_expr = f"json_object({', '.join(parts)})" if parts else "NULL"

    backup_name = f"incidents_legacy_{time.strftime('%Y%m%d_%H%M%S')}"
    cur.execute("BEGIN IMMEDIATE")
    cur.execute("ALTER TABLE incidents RENAME TO incidents_old")
    cur.execute(
        """
        CREATE TABLE incidents (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ts            TEXT    NOT NULL,
            source        TEXT    NOT NULL,
            total_persons INTEGER NOT NULL DEFAULT 0,
            safe_count    INTEGER NOT NULL DEFAULT 0,
            unsafe_count  INTEGER NOT NULL DEFAULT 0,
            details_json  TEXT
        )
        """
    )
    cur.execute(
        f"""
        INSERT INTO incidents (ts, source, total_persons, safe_count, unsafe_count, details_json)
        SELECT
            {ts_expr}      AS ts,
            {source_expr}  AS source,
            CAST({total_expr}  AS INTEGER) AS total_persons,
            CAST({safe_expr}   AS INTEGER) AS safe_count,
            CAST({unsafe_expr} AS INTEGER) AS unsafe_count,
            {details_expr} AS details_json
        FROM incidents_old
        """
    )
    cur.execute(f"ALTER TABLE incidents_old RENAME TO {backup_name}")
    conn.commit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Initialise WAL mode and normalise the incidents schema.  Call once at startup."""
    _configure_wal_once()
    conn = get_connection()
    try:
        _normalize_schema(conn)
    finally:
        conn.close()


def log_incident(
    source: str,
    total: int,
    safe: int,
    unsafe: int,
    details: Optional[dict] = None,
) -> None:
    """
    Insert one incident row.  Retries up to 5× on transient SQLITE_BUSY errors.
    Supports both the canonical schema and older schemas with extra NOT NULL columns.
    """
    last_err: Optional[Exception] = None
    for _ in range(5):
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()

            now_text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            detail_json = json.dumps(details or {})
            reasons_list: list = []
            if isinstance(details, dict):
                if isinstance(details.get("missing_ppe"), list):
                    reasons_list = [str(x) for x in details["missing_ppe"]]
                elif details.get("reason"):
                    reasons_list = [str(details["reason"])]

            cur.execute("PRAGMA table_info(incidents)")
            col_meta = {row[1]: {"type": (row[2] or "").upper(), "notnull": bool(row[3])} for row in cur.fetchall()}
            col_names = list(col_meta.keys())

            base: dict = {
                "ts":            now_text,
                "ts_text":       now_text,
                "source":        str(source),
                "camera_id":     "default",
                "total_persons": int(total),
                "safe_count":    int(safe),
                "unsafe_count":  int(unsafe),
                "details_json":  detail_json,
                "track_ids":     "[]",
                "reasons":       json.dumps(reasons_list),
                "channels":      json.dumps(["dashboard"]),
                "snapshot_path": (details or {}).get("snapshot_path") if isinstance(details, dict) else None,
            }

            insert_cols = [c for c in col_names if c.lower() != "id"]
            values = []
            for col in insert_cols:
                if col in base:
                    values.append(base[col])
                    continue
                meta = col_meta.get(col, {})
                if meta.get("notnull"):
                    col_type = meta.get("type", "")
                    values.append(0 if any(t in col_type for t in ("INT", "REAL", "NUM")) else "")
                else:
                    values.append(None)

            placeholders = ", ".join(["?"] * len(insert_cols))
            cur.execute(
                f"INSERT INTO incidents ({', '.join(insert_cols)}) VALUES ({placeholders})",
                values,
            )
            conn.commit()
            return
        except sqlite3.OperationalError as exc:
            last_err = exc
            if "locked" not in str(exc).lower():
                raise
            time.sleep(0.25)
        finally:
            if conn is not None:
                conn.close()

    if last_err:
        print(f"[SafeVision] Incident logging skipped due to DB lock: {last_err}")


def fetch_incidents(limit: int = 200) -> pd.DataFrame:
    """Return the most recent *limit* incidents as a DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT id, ts, source, total_persons, safe_count, unsafe_count "
            "FROM incidents ORDER BY id DESC LIMIT ?",
            conn,
            params=[int(limit)],
        )
    finally:
        conn.close()
    return df


def get_incident_count() -> int:
    """Return total number of stored incidents."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM incidents")
        return int(cur.fetchone()[0])
    finally:
        conn.close()

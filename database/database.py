"""
RAMGuard Database
SQLite-backed persistence for optimization history and settings.
"""

import sqlite3
import json
import os
import time
from typing import Optional, Any
from pathlib import Path
from utils.logger import get_logger

logger = get_logger("Database")

DB_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "data" / "ramguard.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_database() -> None:
    """Create all tables if they do not yet exist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS optimization_sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                mode            TEXT    NOT NULL,
                started_at      REAL    NOT NULL,
                finished_at     REAL    NOT NULL,
                percent_before  REAL,
                percent_after   REAL,
                memory_freed_mb REAL,
                apps_closed     INTEGER DEFAULT 0,
                apps_failed     INTEGER DEFAULT 0,
                protected_count INTEGER DEFAULT 0,
                notes           TEXT
            );

            CREATE TABLE IF NOT EXISTS closed_processes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      INTEGER NOT NULL REFERENCES optimization_sessions(id),
                name            TEXT    NOT NULL,
                pid             INTEGER,
                memory_mb       REAL,
                success         INTEGER NOT NULL,
                method_used     TEXT,
                error_message   TEXT
            );

            CREATE TABLE IF NOT EXISTS settings (
                key     TEXT PRIMARY KEY,
                value   TEXT NOT NULL
            );
        """)
        conn.commit()
        logger.info("Database initialised at %s", DB_PATH)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
#  Optimization History
# ─────────────────────────────────────────────────────────────────

def save_optimization_result(result) -> int:
    """
    Persist an OptimizationResult to the database.
    Returns the new session ID.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO optimization_sessions
                (mode, started_at, finished_at, percent_before, percent_after,
                 memory_freed_mb, apps_closed, apps_failed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.mode,
                result.started_at,
                result.finished_at,
                result.percent_before,
                result.percent_after,
                result.memory_freed_mb,
                len(result.successful_closures),
                len(result.failed_closures),
            ),
        )
        session_id = cur.lastrowid
        for closure in result.closures:
            cur.execute(
                """
                INSERT INTO closed_processes
                    (session_id, name, pid, memory_mb, success, method_used, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    closure.name,
                    closure.pid,
                    closure.memory_mb,
                    1 if closure.success else 0,
                    closure.method_used,
                    closure.error_message,
                ),
            )
        conn.commit()
        logger.info("Saved optimization session #%d", session_id)
        return session_id
    finally:
        conn.close()


def load_optimization_history(limit: int = 50) -> list[dict]:
    """Load recent optimization sessions with their closed-process details."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM optimization_sessions
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        sessions = []
        for row in rows:
            session = dict(row)
            procs = conn.execute(
                "SELECT * FROM closed_processes WHERE session_id = ?",
                (session["id"],),
            ).fetchall()
            session["processes"] = [dict(p) for p in procs]
            sessions.append(session)
        return sessions
    finally:
        conn.close()


def clear_optimization_history() -> None:
    """Delete all optimization history records."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM closed_processes")
        conn.execute("DELETE FROM optimization_sessions")
        conn.commit()
        logger.info("Optimization history cleared")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
#  Settings
# ─────────────────────────────────────────────────────────────────

def get_setting(key: str, default: Any = None) -> Any:
    conn = get_connection()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row:
            try:
                return json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                return row["value"]
        return default
    finally:
        conn.close()


def set_setting(key: str, value: Any) -> None:
    serialized = json.dumps(value)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, serialized),
        )
        conn.commit()
    finally:
        conn.close()

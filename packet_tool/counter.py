from __future__ import annotations

import sqlite3
from pathlib import Path


def initialize_db(db_path: str | Path) -> None:
    connection = sqlite3.connect(str(db_path), timeout=30)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS packet_counters (
                date_key TEXT PRIMARY KEY,
                seq INTEGER NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def next_sequence(db_path: str | Path, date_key: str) -> int:
    """Atomically increment and return the next sequence for a specific date."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path), timeout=30, isolation_level=None)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS packet_counters (
                date_key TEXT PRIMARY KEY,
                seq INTEGER NOT NULL
            )
            """
        )
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "INSERT OR IGNORE INTO packet_counters (date_key, seq) VALUES (?, 0)",
            (date_key,),
        )
        connection.execute(
            "UPDATE packet_counters SET seq = seq + 1 WHERE date_key = ?",
            (date_key,),
        )
        cursor = connection.execute(
            "SELECT seq FROM packet_counters WHERE date_key = ?",
            (date_key,),
        )
        row = cursor.fetchone()
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()

    if row is None:
        raise RuntimeError("Failed to allocate packet sequence")

    return int(row[0])

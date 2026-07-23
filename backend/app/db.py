"""
db.py — SQLite persistence layer.

Owns: database connection, schema creation, and functions to save/
retrieve analysis history. Kept separate from main.py so route logic
doesn't get tangled with raw SQL.
"""

import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = "codelens.db"


def get_connection():
    """
    Open a connection to the SQLite database file. SQLite creates the
    file automatically on first connection if it doesn't exist yet.
    """
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    Create the analysis_history table if it doesn't already exist.
    Called once at server startup (wired in Step 19).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            function_name TEXT NOT NULL,
            complexity TEXT NOT NULL,
            loop_depth INTEGER NOT NULL,
            is_recursive INTEGER NOT NULL,
            pattern_findings_json TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_analysis(functions: list[dict]):
    """
    Save one analysis run's results (one row per function) into the
    history table. pattern_findings is stored as a JSON string since
    SQLite doesn't have a native nested-object column type.
    """
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now(timezone.utc).isoformat()

    for func in functions:
        cursor.execute("""
            INSERT INTO analysis_history
            (timestamp, function_name, complexity, loop_depth, is_recursive, pattern_findings_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            func["name"],
            func["complexity"],
            func["loop_depth"],
            int(func["is_recursive"]),  # SQLite has no native boolean, store as 0/1
            json.dumps(func["pattern_findings"]),
        ))

    conn.commit()
    conn.close()


def get_history(function_name: str = None) -> list[dict]:
    """
    Retrieve past analysis records, optionally filtered by function
    name. Returns newest-first.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if function_name:
        cursor.execute(
            "SELECT * FROM analysis_history WHERE function_name = ? ORDER BY timestamp DESC",
            (function_name,)
        )
    else:
        cursor.execute("SELECT * FROM analysis_history ORDER BY timestamp DESC")

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "timestamp": row[1],
            "function_name": row[2],
            "complexity": row[3],
            "loop_depth": row[4],
            "is_recursive": bool(row[5]),
            "pattern_findings": json.loads(row[6]),
        })
    return results
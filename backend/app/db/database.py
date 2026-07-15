"""
Database setup - SQLite with SQLAlchemy optional, but keep lightweight.

For simplicity, we use sqlite3 directly for checkpoint and memory persistence.
"""

import sqlite3
import os
from pathlib import Path


def get_db_path() -> str:
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    return str(data_dir / "rios.db")


def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Generations table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generation INTEGER,
            genome_id TEXT,
            parent_id TEXT,
            fitness REAL,
            token_usage INTEGER,
            problem TEXT,
            solution TEXT,
            reasoning_summary TEXT,
            timestamp REAL
        )
        """
    )
    # Benchmarks table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family TEXT,
            difficulty REAL,
            seed INTEGER,
            correctness INTEGER,
            score REAL,
            genome_id TEXT,
            generation INTEGER,
            timestamp REAL
        )
        """
    )
    # Checkpoints table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generation INTEGER,
            path TEXT,
            timestamp REAL,
            fitness REAL
        )
        """
    )
    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect(get_db_path())

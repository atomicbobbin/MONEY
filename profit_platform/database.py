"""SQLite helpers for the Profit Platform service."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_PATH = Path("profit_platform.db")


def get_connection(database_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(database_path or DEFAULT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            base_price REAL NOT NULL,
            target_margin REAL NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS price_observation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
            price REAL NOT NULL,
            units_sold INTEGER NOT NULL,
            visitors INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS price_experiment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
            hypothesis TEXT NOT NULL,
            control_price REAL NOT NULL,
            variant_price REAL NOT NULL,
            start_date TEXT DEFAULT CURRENT_TIMESTAMP,
            completed INTEGER DEFAULT 0
        );
        """
    )
    connection.commit()


@contextmanager
def session_scope(database_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    connection = get_connection(database_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

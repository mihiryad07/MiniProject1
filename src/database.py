"""Beginner-friendly SQLite database helpers for the wardrobe application."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.config import DATABASE_PATH


def connect_database(db_path: Union[str, Path] = DATABASE_PATH) -> sqlite3.Connection:
    """Open a SQLite connection and enable named column access."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path: Union[str, Path] = DATABASE_PATH) -> None:
    """Create the users and wardrobe_items tables if they do not exist."""
    connection = connect_database(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS wardrobe_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                image_path TEXT NOT NULL,
                dominant_color TEXT,
                fabric TEXT,
                season TEXT,
                occasion TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def get_or_create_default_user(db_path: Union[str, Path] = DATABASE_PATH) -> int:
    """Get or create the local Streamlit user's default account."""
    connection = connect_database(db_path)
    try:
        row = connection.execute(
            "SELECT id FROM users WHERE email = ?", ("local@wardrobe.app",)
        ).fetchone()
        if row:
            return int(row["id"])

        cursor = connection.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            ("Local User", "local@wardrobe.app"),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def add_wardrobe_item(db_path: Union[str, Path], item: Dict[str, Any]) -> int:
    """Insert one clothing item and return its database id."""
    connection = connect_database(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO wardrobe_items
                (user_id, name, category, image_path, dominant_color, fabric, season, occasion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["user_id"], item["name"], item["category"], item["image_path"],
                item.get("dominant_color"), item.get("fabric"), item.get("season"),
                item.get("occasion"),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_wardrobe_items(db_path: Union[str, Path], user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return wardrobe items, optionally for one user."""
    connection = connect_database(db_path)
    try:
        if user_id is None:
            cursor = connection.execute(
                "SELECT * FROM wardrobe_items ORDER BY created_at DESC, id DESC"
            )
        else:
            cursor = connection.execute(
                "SELECT * FROM wardrobe_items WHERE user_id = ? ORDER BY created_at DESC, id DESC",
                (user_id,),
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_wardrobe_item(db_path: Union[str, Path], item_id: int) -> Optional[Dict[str, Any]]:
    """Return one wardrobe item by id."""
    connection = connect_database(db_path)
    try:
        row = connection.execute(
            "SELECT * FROM wardrobe_items WHERE id = ?", (item_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def update_wardrobe_item(db_path: Union[str, Path], item_id: int, changes: Dict[str, Any]) -> bool:
    """Update allowed clothing fields for one item."""
    allowed = {"name", "category", "dominant_color", "fabric", "season", "occasion", "image_path"}
    updates = {key: value for key, value in changes.items() if key in allowed}
    if not updates:
        return False

    set_sql = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [item_id]

    connection = connect_database(db_path)
    try:
        cursor = connection.execute(
            f"UPDATE wardrobe_items SET {set_sql}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_wardrobe_item(db_path: Union[str, Path], item_id: int) -> bool:
    """Delete one wardrobe item by id."""
    connection = connect_database(db_path)
    try:
        cursor = connection.execute("DELETE FROM wardrobe_items WHERE id = ?", (item_id,))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()

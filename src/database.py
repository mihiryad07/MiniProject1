"""Beginner-friendly SQLite database helpers for the wardrobe application."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

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
                password_hash TEXT,
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
                embedding_json TEXT,
                texture_features_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS outfit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_ids TEXT NOT NULL,
                worn_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS outfit_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_ids TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, item_ids)
            )
            """
        )

        existing_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(wardrobe_items)").fetchall()
        }
        if "embedding_json" not in existing_columns:
            connection.execute("ALTER TABLE wardrobe_items ADD COLUMN embedding_json TEXT")
        if "texture_features_json" not in existing_columns:
            connection.execute("ALTER TABLE wardrobe_items ADD COLUMN texture_features_json TEXT")

        user_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "password_hash" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

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
                (user_id, name, category, image_path, dominant_color, fabric, season, occasion,
                 embedding_json, texture_features_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["user_id"], item["name"], item["category"], item["image_path"],
                item.get("dominant_color"), item.get("fabric"), item.get("season"),
                item.get("occasion"), item.get("embedding_json"),
                item.get("texture_features_json"),
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
    allowed = {
        "name", "category", "dominant_color", "fabric", "season", "occasion",
        "image_path", "embedding_json", "texture_features_json",
    }
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


def record_outfit_history(db_path: Union[str, Path], user_id: int, item_ids: List[int]) -> None:
    """Record that an outfit was worn, by user and item IDs."""
    connection = connect_database(db_path)
    try:
        connection.execute(
            """
            INSERT INTO outfit_history (user_id, item_ids)
            VALUES (?, ?)
            """,
            (user_id, json.dumps(item_ids)),
        )
        connection.commit()
    finally:
        connection.close()


def get_outfit_history(db_path: Union[str, Path], user_id: int) -> List[Dict[str, Any]]:
    """Get the wear history for one user, with stored item names when available."""
    connection = connect_database(db_path)
    try:
        cursor = connection.execute(
            """
            SELECT oh.*
            FROM outfit_history oh
            WHERE oh.user_id = ?
            ORDER BY oh.worn_at DESC, oh.id DESC
            """,
            (user_id,),
        )
        history = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            row_dict["item_ids"] = json.loads(row_dict["item_ids"])
            names = []
            for item_id in row_dict["item_ids"]:
                item = connection.execute(
                    "SELECT name FROM wardrobe_items WHERE id = ?", (item_id,)
                ).fetchone()
                if item:
                    names.append(item["name"])
            row_dict["item_names"] = ", ".join(names) if names else "Outfit"
            history.append(row_dict)
        return history
    finally:
        connection.close()


def record_outfit_worn(db_path: Union[str, Path], user_id: int, item_ids: List[int]) -> int:
    """Record an outfit as worn and return its history row id."""
    connection = connect_database(db_path)
    try:
        cursor = connection.execute(
            "INSERT INTO outfit_history (user_id, item_ids) VALUES (?, ?)",
            (user_id, json.dumps(sorted(set(int(item_id) for item_id in item_ids)))),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_recently_worn_item_ids(
    db_path: Union[str, Path],
    user_id: int,
    limit: int = 10,
) -> List[int]:
    """Return item ids from the most recently recorded outfits."""
    connection = connect_database(db_path)
    try:
        rows = connection.execute(
            """
            SELECT item_ids FROM outfit_history
            WHERE user_id = ?
            ORDER BY worn_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, max(limit, 0)),
        ).fetchall()
        ids: Set[int] = set()
        for row in rows:
            try:
                ids.update(int(item_id) for item_id in json.loads(row["item_ids"]))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        return list(ids)
    finally:
        connection.close()


def record_outfit_feedback(
    db_path: Union[str, Path],
    user_id: int,
    item_ids: List[int],
    rating: int,
    comment: Optional[str] = None,
) -> int:
    """Create or update an outfit rating and optional comment."""
    normalized_rating = int(rating)
    if not 1 <= normalized_rating <= 5:
        raise ValueError("Rating must be between 1 and 5.")

    normalized_ids = json.dumps(sorted(set(int(item_id) for item_id in item_ids)))
    connection = connect_database(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO outfit_feedback (user_id, item_ids, rating, comment)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, item_ids)
            DO UPDATE SET rating = excluded.rating,
                          comment = excluded.comment,
                          created_at = CURRENT_TIMESTAMP
            """,
            (user_id, normalized_ids, normalized_rating, comment.strip() if comment else None),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id FROM outfit_feedback WHERE user_id = ? AND item_ids = ?",
            (user_id, normalized_ids),
        ).fetchone()
        return int(row["id"])
    finally:
        connection.close()


def get_outfit_feedback(db_path: Union[str, Path], user_id: int) -> List[Dict[str, Any]]:
    """Return outfit ratings for one user."""
    connection = connect_database(db_path)
    try:
        rows = connection.execute(
            "SELECT * FROM outfit_feedback WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        feedback = []
        for row in rows:
            value = dict(row)
            value["item_ids"] = json.loads(value["item_ids"])
            feedback.append(value)
        return feedback
    finally:
        connection.close()

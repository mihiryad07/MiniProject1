"""Local account registration and login helpers."""

from __future__ import annotations

import hashlib
import secrets
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.config import DATABASE_PATH
from src.database import connect_database, initialize_database


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_value.encode("utf-8"), 200_000)
    return f"pbkdf2_sha256$200000${salt_value}${digest.hex()}"


def register_user(
    name: str,
    email: str,
    password: str,
    db_path: Union[str, Path] = DATABASE_PATH,
) -> Dict[str, Any]:
    """Register a local user and return a safe user dictionary."""
    name = name.strip()
    email = email.strip().lower()
    if len(name) < 2:
        raise ValueError("Name must contain at least 2 characters.")
    if "@" not in email or "." not in email:
        raise ValueError("Enter a valid email address.")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    initialize_database(db_path)
    connection = connect_database(db_path)
    try:
        existing = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise ValueError("An account with this email already exists.")
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, _hash_password(password)),
        )
        connection.commit()
        return {"id": int(cursor.lastrowid), "name": name, "email": email}
    finally:
        connection.close()


def authenticate_user(
    email: str,
    password: str,
    db_path: Union[str, Path] = DATABASE_PATH,
) -> Optional[Dict[str, Any]]:
    """Authenticate a user by email and password."""
    initialize_database(db_path)
    connection = connect_database(db_path)
    try:
        row = connection.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
        if not row or not row["password_hash"]:
            return None
        try:
            algorithm, rounds, salt, expected = str(row["password_hash"]).split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return None
            digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(rounds)).hex()
        except (TypeError, ValueError):
            return None
        if not secrets.compare_digest(digest, expected):
            return None
        return {"id": int(row["id"]), "name": row["name"], "email": row["email"]}
    finally:
        connection.close()

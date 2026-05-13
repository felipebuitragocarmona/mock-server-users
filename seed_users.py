#!/usr/bin/env python3
"""Seed script: crea la tabla `users` si hace falta y añade 20 usuarios de prueba.

Ahora inserta también `password` (hasheada) y `refresh_token` (NULL).
"""
import sqlite3
from werkzeug.security import generate_password_hash

DB = "users.db"

SAMPLE_USERS = [
    (
        f"User {i}",
        f"user{i}",
        f"user{i}@example.com",
        f"+34-600-000-{i:02d}",
        f"example{i}.com",
        generate_password_hash("secret")
    )
    for i in range(1, 21)
]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    username TEXT,
    email TEXT,
    phone TEXT,
    website TEXT,
    password TEXT,
    refresh_token TEXT
)
"""


def main():
    conn = sqlite3.connect(DB)
    try:
        conn.execute(CREATE_TABLE_SQL)
        # Insert only if table empty to avoid duplicates
        cur = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()
        if cur and cur[0] > 0:
            print("Users table already seeded; skipping insertion.")
            return

        conn.executemany(
            "INSERT INTO users (name, username, email, phone, website, password) VALUES (?, ?, ?, ?, ?, ?)",
            SAMPLE_USERS,
        )
        conn.commit()
        print(f"Inserted {len(SAMPLE_USERS)} users into {DB}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Seed script: crea la tabla `users` si hace falta y añade 20 usuarios de prueba."""
import sqlite3

DB = "users.db"

SAMPLE_USERS = [
    (
        f"User {i}",
        f"user{i}",
        f"user{i}@example.com",
        f"+34-600-000-{i:02d}",
        f"example{i}.com",
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
    website TEXT
)
"""

def main():
    conn = sqlite3.connect(DB)
    try:
        conn.execute(CREATE_TABLE_SQL)
        conn.executemany(
            "INSERT INTO users (name, username, email, phone, website) VALUES (?, ?, ?, ?, ?)",
            SAMPLE_USERS,
        )
        conn.commit()
        print(f"Inserted {len(SAMPLE_USERS)} users into {DB}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

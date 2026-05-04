from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_NAME = "users.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            username TEXT,
            email TEXT,
            phone TEXT,
            website TEXT
        )
    """)
    conn.commit()
    conn.close()

def row_to_dict(row):
    return dict(row) if row else None


if hasattr(app, "before_first_request"):
    @app.before_first_request
    def initialize_db():
        init_db()
else:
    # Fallback for environments where the decorator isn't available
    init_db()

@app.route("/users", methods=["GET"])
def list_users():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 10))

    offset = (page - 1) * page_size

    conn = get_db()
    total_items = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]

    rows = conn.execute(
        "SELECT * FROM users LIMIT ? OFFSET ?",
        (page_size, offset)
    ).fetchall()

    conn.close()

    return jsonify({
        "data": [row_to_dict(r) for r in rows],
        "page": page,
        "pageSize": page_size,
        "totalItems": total_items,
        "totalPages": (total_items + page_size - 1) // page_size
    })

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    return jsonify(row_to_dict(row))

@app.route("/users", methods=["POST"])
def create_user():
    data = request.json

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, username, email, phone, website) VALUES (?, ?, ?, ?, ?)",
        (
            data.get("name"),
            data.get("username"),
            data.get("email"),
            data.get("phone"),
            data.get("website"),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": new_id}), 201

@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json

    conn = get_db()
    conn.execute(
        """UPDATE users
        SET name=?, username=?, email=?, phone=?, website=?
        WHERE id=?""",
        (
            data.get("name"),
            data.get("username"),
            data.get("email"),
            data.get("phone"),
            data.get("website"),
            user_id,
        ),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "User updated"})

@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "User deleted"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os

app = Flask(__name__)
# Allow credentials so the browser can send/receive HttpOnly cookies
# ✅ Correcto
CORS(app, supports_credentials=True, origins=["http://localhost:4200"])

DB_NAME = "users.db"
SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key")
ACCESS_TOKEN_EXPIRES_MINUTES = 15
REFRESH_TOKEN_EXPIRES_DAYS = 7
COOKIE_SECURE = False

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
            website TEXT,
            password TEXT,
            refresh_token TEXT
        )
    """)
    # Ensure columns exist for older DBs
    cur = conn.execute("PRAGMA table_info(users)").fetchall()
    columns = [r[1] for r in cur]
    if 'password' not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN password TEXT")
    if 'refresh_token' not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN refresh_token TEXT")
    conn.commit()
    conn.close()

def row_to_dict(row):
    return dict(row) if row else None


def create_access_token(user_id, email):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'sub': str(user_id),  # ← convertir a string
        'email': email,
        'iat': now,
        'exp': now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def create_refresh_token(user_id):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'sub': str(user_id),  # ← convertir a string
        'iat': now,
        'exp': now + datetime.timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def get_user_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def store_refresh_token(user_id, token):
    conn = get_db()
    conn.execute("UPDATE users SET refresh_token = ? WHERE id = ?", (token, user_id))
    conn.commit()
    conn.close()


def clear_refresh_token(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET refresh_token = NULL WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


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
    password = data.get("password")
    hashed = generate_password_hash(password) if password else None

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, username, email, phone, website, password) VALUES (?, ?, ?, ?, ?, ?)",
        (
            data.get("name"),
            data.get("username"),
            data.get("email"),
            data.get("phone"),
            data.get("website"),
            hashed,
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": new_id}), 201



@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    stored_hash = user['password']
    if not stored_hash or not check_password_hash(stored_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(user['id'], user['email'])
    refresh_token = create_refresh_token(user['id'])
    store_refresh_token(user['id'], refresh_token)

    resp = make_response(jsonify({'message': 'Logged in'}))
    resp.set_cookie('accessToken', access_token,
        httponly=True,
        samesite='Lax',
        secure=False,
        max_age=ACCESS_TOKEN_EXPIRES_MINUTES * 60,
        path='/')
    resp.set_cookie('refreshToken', refresh_token,
        httponly=True,
        samesite='Lax',
        secure=False,
        max_age=REFRESH_TOKEN_EXPIRES_DAYS * 24 * 3600,
        path='/')
    return resp


@app.route('/api/auth/refresh', methods=['POST'])
def refresh():
    rt = request.cookies.get('refreshToken')
    if not rt:
        return jsonify({'error': 'Missing refresh token'}), 401
    try:
        payload = jwt.decode(rt, SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('sub')
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Refresh token expired'}), 401
    except Exception:
        return jsonify({'error': 'Invalid refresh token'}), 401

    user = get_user_by_id(user_id)
    if not user or not user['refresh_token']:
        return jsonify({'error': 'Invalid refresh token'}), 401
    if user['refresh_token'] != rt:
        return jsonify({'error': 'Token mismatch'}), 401

    access_token = create_access_token(user['id'], user['email'])
    new_rt = create_refresh_token(user['id'])
    store_refresh_token(user['id'], new_rt)

    resp = make_response(jsonify({'message': 'Token refreshed'}))
    resp.set_cookie('accessToken', access_token,
        httponly=True,
        samesite='Lax',
        secure=False,
        max_age=ACCESS_TOKEN_EXPIRES_MINUTES * 60,
        path='/')
    resp.set_cookie('refreshToken', new_rt,
        httponly=True,
        samesite='Lax',
        secure=False,
        max_age=REFRESH_TOKEN_EXPIRES_DAYS * 24 * 3600,
        path='/')
    return resp


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    rt = request.cookies.get('refreshToken')
    if rt:
        try:
            payload = jwt.decode(rt, SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('sub')
            clear_refresh_token(user_id)
        except Exception:
            pass
    else:
        at = request.cookies.get('accessToken')
        if at:
            try:
                payload = jwt.decode(at, SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('sub')
                clear_refresh_token(user_id)
            except Exception:
                pass

    resp = make_response(jsonify({'message': 'Logged out'}))
    resp.set_cookie('accessToken', '', expires=0,
        samesite='Lax', secure=False, path='/')
    resp.set_cookie('refreshToken', '', expires=0,
        samesite='Lax', secure=False, path='/')
    return resp


@app.route('/api/auth/me', methods=['GET'])
def me():
    at = request.cookies.get('accessToken')
    if not at:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        payload = jwt.decode(at, SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('sub')
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Access token expired'}), 401
    except Exception as e:
        print("Error decodificando:", e)
        return jsonify({'error': 'Invalid access token'}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = dict(user)
    data.pop('password', None)
    data.pop('refresh_token', None)

    return jsonify(data)

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
    app.run(debug=True,host='localhost')

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def register_user(username, password, email=None, phone=None):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, email, phone) VALUES (?, ?, ?, ?)",
            (username, password_hash, email, phone)
        )
        conn.commit()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "This username is already taken."
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row and check_password_hash(row[0], password):
        return True, "Login successful!"
    else:
        return False, "Incorrect username or password."

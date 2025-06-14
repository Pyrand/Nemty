import sqlite3

def print_error(e):
    print(f"\u274c Error: {e}")
    
def load_user_history(username, for_model=True):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM user_messages WHERE username = ? ORDER BY created_at", (username,))
    history = []
    for role, content in cursor.fetchall():
        if for_model and role not in ("system", "user", "assistant", "function"):
            continue
        if role == "function":
            history.append({"role": role, "name": "get_recommended_places", "content": content})
        else:
            history.append({"role": role, "content": content})
    conn.close()
    return history

def save_message(username, role, content, name=None):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_messages (username, role, content) VALUES (?, ?, ?)", (username, role, content))
    conn.commit()
    conn.close()

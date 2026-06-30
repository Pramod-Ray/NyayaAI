import sqlite3

def create_database():

    conn = sqlite3.connect("nyayaai.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

create_database()

def save_message(session_id, role, message):

    conn = sqlite3.connect("nyayaai.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO chat_history(session_id, role, message)
    VALUES (?, ?, ?)
    """, (session_id, role, message))

    conn.commit()
    conn.close()
    
def get_chat_history(session_id, limit=10):

    conn = sqlite3.connect("nyayaai.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT role, message
    FROM chat_history
    WHERE session_id = ?
    ORDER BY id DESC
    LIMIT ?
    """, (session_id, limit))

    rows = cursor.fetchall()

    conn.close()

    return rows[::-1]
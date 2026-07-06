"""
Lightweight long-term memory: logs every Q&A with retrieved sources, and lets
the analyst agent pull recent history back in as context (so follow-up
questions like "what about last month" resolve against prior turns).
Also doubles as the evaluation/observability log.
"""
import sqlite3, json, os, time

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "memory.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            question TEXT,
            plan TEXT,
            retrieved_ids TEXT,
            answer TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()

def log_interaction(session_id, question, plan, retrieved_ids, answer):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO interactions (session_id, question, plan, retrieved_ids, answer, timestamp) VALUES (?,?,?,?,?,?)",
        (session_id, question, json.dumps(plan), json.dumps(retrieved_ids), answer, time.time())
    )
    conn.commit()
    conn.close()

def get_recent_history(session_id, limit=5):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT question, answer FROM interactions WHERE session_id=? ORDER BY id DESC LIMIT ?",
        (session_id, limit)
    ).fetchall()
    conn.close()
    return [{"question": q, "answer": a} for q, a in reversed(rows)]

def get_all_logs():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT session_id, question, answer, timestamp FROM interactions ORDER BY id DESC").fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    log_interaction("test", "What are common complaints?", {"sources": ["support_ticket"]}, ["ticket_0", "ticket_2"], "Dark mode and slow reports are most common.")
    print(get_recent_history("test"))

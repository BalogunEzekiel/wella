import sqlite3

conn = sqlite3.connect("wella.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    symptoms TEXT,
    temp REAL,
    heart_rate INTEGER,
    resp_rate INTEGER,
    priority TEXT,
    recommendation TEXT
)
""")

conn.commit()
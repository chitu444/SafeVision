import sqlite3
from config.settings import INCIDENT_DB_PATH

def get_connection():
    return sqlite3.connect(INCIDENT_DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS incidents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            source TEXT,
            total_persons INTEGER,
            safe_count INTEGER,
            unsafe_count INTEGER
        )
        '''
    )

    conn.commit()
    conn.close()
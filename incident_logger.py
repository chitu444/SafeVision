import time
from database.db_manager import get_connection

def log_incident(source, total, safe, unsafe):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO incidents(ts,source,total_persons,safe_count,unsafe_count) VALUES(?,?,?,?,?)",
        (time.strftime("%Y-%m-%d %H:%M:%S"), source, total, safe, unsafe)
    )

    conn.commit()
    conn.close()
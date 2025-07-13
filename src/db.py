
import sqlite3
import os

def get_base_dir():
    import sys
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

DB_LEARN = os.path.join(get_base_dir(), 'data', 'learn.db')
DB_REVIEW = os.path.join(get_base_dir(), 'data', 'review.db')

def init_db():
    data_dir = os.path.dirname(DB_LEARN)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    for dbfile in [DB_LEARN, DB_REVIEW]:
        if not os.path.exists(dbfile):
            conn = sqlite3.connect(dbfile)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE record (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT,
                    date TEXT,
                    start INTEGER,
                    end INTEGER
                )
            """)
            conn.commit()
            conn.close()

def add_record(dbfile, node_id, date, start, end):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    c.execute("INSERT INTO record (node_id, date, start, end) VALUES (?, ?, ?, ?)", (node_id, date, start, end))
    conn.commit()
    conn.close()

def get_records(dbfile, node_id=None, date=None):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    sql = "SELECT node_id, date, start, end FROM record WHERE 1=1"
    params = []
    if node_id:
        sql += " AND node_id=?"
        params.append(node_id)
    if date:
        sql += " AND date=?"
        params.append(date)
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_records(dbfile):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    c.execute("SELECT node_id, date, start, end FROM record")
    rows = c.fetchall()
    conn.close()
    return rows
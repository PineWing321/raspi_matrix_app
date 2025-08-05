import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'matrixapp_v2.db')

def init_sqlite_schema():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password_hash TEXT,
        timezone TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planned_shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auth_id TEXT,
        planned_start TIMESTAMP,
        planned_end TIMESTAMP,
        break1_start TIMESTAMP,
        break1_end TIMESTAMP,
        shift_id TEXT,
        is_completed BOOLEAN,
        lunch_start TIMESTAMP,
        lunch_end TIMESTAMP,
        break2_start TIMESTAMP,
        break2_end TIMESTAMP,
        target_cycle_time INTEGER,
        total_parts INTEGER,
        total_rejects INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auth_id TEXT,
        planned_shift_id INTEGER,
        start_time TEXT,
        stop_time TEXT,
        reason TEXT,
        comments TEXT,
        part_count INTEGER,
        created_at TIMESTAMP,
        cause TEXT,
        rejected_parts INTEGER,
        expected_parts INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shift_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auth_id TEXT,
        shift_id INTEGER,
        planned_start TEXT,
        planned_end TEXT,
        planned_runtime REAL,
        scheduled_runtime REAL,
        engaged_runtime REAL,
        total_runtime REAL,
        machine_uptime REAL,
        total_downtime REAL,
        available_downtime REAL,
        unavailable_downtime REAL,
        non_engaged_time REAL,
        total_stops INTEGER,
        machine_error_stops INTEGER,
        planned_stops INTEGER,
        break_stops INTEGER,
        machine_efficiency REAL,
        total_efficiency REAL,
        timestamp_submitted TIMESTAMP,
        break1_start TEXT,
        break1_end TEXT,
        lunch_start TIMESTAMP,
        lunch_end TIMESTAMP,
        break2_start TIMESTAMP,
        break2_end TIMESTAMP,
        total_parts INTEGER,
        total_rejects INTEGER,
        expected_parts INTEGER,
        quality INTEGER,
        performance INTEGER,
        final_oee INTEGER,
        final_mr_oee INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mock_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auth_id TEXT,
        value BOOLEAN,
        timestamp TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        next_path TEXT,
        updated_at TIMESTAMP,
        message TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        planned_start TIME,
        planned_end TIME,
        break1_start TIME,
        break1_end TIME,
        lunch_start TIME,
        lunch_end TIME,
        break2_start TIME,
        break2_end TIME,
        target_cycle_time INTEGER,
        auth_id TEXT,
        created_at TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shift_runtime (
        auth_id TEXT,
        state INTEGER,
        last_updated TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS state_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state INTEGER,
        timestamp_utc TIMESTAMP,
        auth_id TEXT
    );
    """)

    conn.commit()
    conn.close()
    print("✅ SQLite schema initialized.")

if __name__ == "__main__":
    init_sqlite_schema()

import os
import sqlite3
from src.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create planned_shifts table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS planned_shifts (
        auth_id TEXT,
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        planned_start TEXT,
        planned_end TEXT,
        break_start TEXT,
        break_end TEXT,
        shift_id TEXT
    )
""")

# Create shifts table with FK to planned_shifts
cursor.execute("""
    CREATE TABLE IF NOT EXISTS shifts (
        auth_id TEXT,
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        planned_shift_id INTEGER,
        start_time TEXT,
        stop_time TEXT,
        cause TEXT,
        details TEXT,
        part_count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (planned_shift_id) REFERENCES planned_shifts(id)
    )
""")

# Create shift_summary table with analytics
cursor.execute("""
    CREATE TABLE IF NOT EXISTS shift_summary (
        auth_id TEXT,
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_id INTEGER NOT NULL,
        planned_runtime REAL,
        total_runtime REAL,
        machine_uptime REAL,
        total_downtime REAL,
        available_downtime REAL,
        unavailable_downtime REAL,
        total_stops INTEGER,
        machine_error_stops INTEGER,
        machine_efficiency REAL,
        total_efficiency REAL,
        timestamp_submitted TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shift_id) REFERENCES planned_shifts(id)
    )
""")

conn.commit()
conn.close()

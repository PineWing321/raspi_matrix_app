from flask import Blueprint
from src.db import get_connection

bp = Blueprint("init_db_routes", __name__)

@bp.route("/init-db")
def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT
            )
        """)

        # Planned shifts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS planned_shifts (
                id SERIAL PRIMARY KEY,
                auth_id TEXT,
                planned_start TEXT,
                planned_end TEXT,
                break_start TEXT,
                break_end TEXT,
                shift_id TEXT
            )
        """)

        # Shifts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id SERIAL PRIMARY KEY,
                auth_id TEXT,
                planned_shift_id INTEGER REFERENCES planned_shifts(id),
                start_time TEXT,
                stop_time TEXT,
                cause TEXT,
                details TEXT,
                part_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Shift summary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shift_summary (
                id SERIAL PRIMARY KEY,
                auth_id TEXT NOT NULL,
                shift_id INTEGER NOT NULL REFERENCES planned_shifts(id),
                planned_start TEXT NOT NULL,
                planned_end TEXT NOT NULL,

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
                timestamp_submitted TEXT DEFAULT CURRENT_TIMESTAMP,

                break_start TEXT,
                break_end TEXT
            )
        """)

        conn.commit()
    return "✅ PostgreSQL schema initialized"

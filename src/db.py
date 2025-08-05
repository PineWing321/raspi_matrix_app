import os
import sqlite3
from datetime import datetime, timezone
from dotenv import load_dotenv
# SQLite3 connection
load_dotenv()
DB_FILE = os.path.join(os.path.dirname(__file__), 'matrixapp_v2.db')  # ✅ Correct path
def get_connection():
    if os.getenv("SKIP_DB") == "true":
        raise RuntimeError("Database access skipped (SKIP_DB=true)")

    db_path = os.getenv("SQLITE_PATH", "matrixapp_v2.db")
   
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
print("🔍 SKIP_DB:", os.getenv("SKIP_DB"))
print("🔍 SQLITE_PATH:", os.getenv("SQLITE_PATH"))

def clean_timestamp(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '')[:19])
    except Exception:
        return None

def format_datetime_for_db(dt):
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return None
    elif not isinstance(dt, datetime):
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Helper for parsing SQLite datetime strings
def parse_to_datetime(dt_string):
    return datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S") if dt_string else None

# All DB functions now use SQLite3

def insert_planned_shift(auth_id, shift_id, start, end,
                         break1_start, break1_end,
                         lunch_start, lunch_end,
                         break2_start, break2_end, cycle_time):
    # Format all datetime values for DB
    start = format_datetime_for_db(start)
    end = format_datetime_for_db(end)
    break1_start = format_datetime_for_db(break1_start)
    break1_end = format_datetime_for_db(break1_end)
    lunch_start = format_datetime_for_db(lunch_start)
    lunch_end = format_datetime_for_db(lunch_end)
    break2_start = format_datetime_for_db(break2_start)
    break2_end = format_datetime_for_db(break2_end)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO planned_shifts (
                auth_id, shift_id, planned_start, planned_end,
                break1_start, break1_end,
                lunch_start, lunch_end,
                break2_start, break2_end, target_cycle_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            auth_id, shift_id, start, end,
            break1_start, break1_end,
            lunch_start, lunch_end,
            break2_start, break2_end, cycle_time
        ))
        conn.commit()


def insert_shift_start(auth_id, start_time, planned_shift_id):
    start_time = format_datetime_for_db(start_time)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO shifts (auth_id, start_time, planned_shift_id)
            VALUES (?, ?, ?)
        """, (auth_id, start_time, planned_shift_id))
        conn.commit()

from datetime import datetime

def insert_final_analytics(analytics):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO shift_summary (
                auth_id, shift_id, planned_start, planned_end,
                scheduled_runtime, engaged_runtime, total_runtime,
                machine_uptime, machine_efficiency, total_efficiency,
                total_downtime, available_downtime, unavailable_downtime,
                non_engaged_time, total_stops, machine_error_stops,
                planned_stops, break_stops,
                break1_start, break1_end,
                lunch_start, lunch_end,
                break2_start, break2_end,
                total_parts, total_rejects, expected_parts,
                quality, performance, final_oee, final_mr_oee,
                timestamp_submitted
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?
            )
        """, (
            analytics["auth_id"], analytics["shift_id"], analytics["planned_start"], analytics["planned_end"],
            analytics["scheduled_runtime"], analytics["engaged_runtime"], analytics["total_runtime"],
            analytics["machine_uptime"], analytics["machine_efficiency"], analytics["total_efficiency"],
            analytics["total_downtime"], analytics["available_downtime"], analytics["unavailable_downtime"],
            analytics["non_engaged_time"], analytics["total_stops"], analytics["machine_error_stops"],
            analytics["planned_stops"], analytics["break_stops"],
            analytics["break1_start"], analytics["break1_end"],
            analytics["lunch_start"], analytics["lunch_end"],
            analytics["break2_start"], analytics["break2_end"],
            analytics["total_parts"], analytics["total_rejects"], analytics["expected_parts"],
            round(analytics["quality"]), round(analytics["performance"]),
            round(analytics["final_oee"]), round(analytics["final_mr_oee"]),
            datetime.now().isoformat()
        ))
        conn.commit()


def update_planned_end(auth_id, planned_shift_id, new_end):
    new_end = format_datetime_for_db(new_end)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE planned_shifts
            SET planned_end = ?
            WHERE auth_id = ? AND id = ?
        """, (new_end, auth_id, planned_shift_id))
        conn.commit()

def get_latest_planned_shift(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT planned_start, planned_end, break_start, break_end
            FROM planned_shifts
            WHERE auth_id = ?
            ORDER BY id DESC LIMIT 1
        """, (auth_id,))
        return cursor.fetchone()

def delete_all_planned_shifts(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM planned_shifts WHERE auth_id = ?", (auth_id,))
        conn.commit()

def delete_planned_shift_by_id(auth_id, planned_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM planned_shifts WHERE auth_id = ? AND id = ?", (auth_id, planned_id))
        conn.commit()

def get_all_uncompleted_planned_shifts(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, planned_start, planned_end, break_start, break_end
            FROM planned_shifts
            WHERE auth_id = ? AND is_completed = FALSE
            ORDER BY id DESC
        """, (auth_id,))
        return cursor.fetchall()


def get_all_shift_rows(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT start_time, stop_time, cause
            FROM shifts
            WHERE auth_id = ?
            ORDER BY id DESC
        """, (auth_id,))
        return cursor.fetchall()

def get_planned_shift_id(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM planned_shifts WHERE auth_id = ? ORDER BY id DESC LIMIT 1", (auth_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_latest_unstopped_shift_id(auth_id, planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM shifts
            WHERE auth_id = ?
              AND planned_shift_id = ?
              AND reason is 'unconfirmed'
              AND cause is 'unconfirmed'
            ORDER BY id DESC
            LIMIT 1
        """, (auth_id, planned_shift_id))
        result = cursor.fetchone()
        return result[0] if result else None

def update_shift_stop(shift_id, auth_id, stop_time,reason, cause, comments, multiple_causes ):
    stop_time = format_datetime_for_db(stop_time)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
    UPDATE shifts
    SET stop_time = ?, reason = ?, cause = ?, comments = ?, multiple_causes = ?
       
    WHERE id = ? AND auth_id = ?
""", (stop_time, reason, cause, comments, multiple_causes,  shift_id, auth_id))
        conn.commit()

def get_shift_logs_by_planned_id(auth_id, planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, start_time, stop_time, reason,cause, comments, part_count, rejected_parts
            FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ?
            ORDER BY start_time
        """, (auth_id, planned_shift_id))
        return cursor.fetchall()

def get_planned_start_by_id(auth_id, planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT planned_start
            FROM planned_shifts
            WHERE auth_id = ? AND id = ?
        """, (auth_id, planned_shift_id))
        result = cursor.fetchone()
        return result["planned_start"] if result else None


def get_last_stop_time(auth_id, planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT stop_time FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ? AND stop_time IS NOT NULL
            ORDER BY stop_time DESC LIMIT 1
        """, (auth_id, planned_shift_id))
        result = cursor.fetchone()
        return result[0] if result else None

def is_clock_running(auth_id, planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ? AND stop_time IS NULL
            ORDER BY start_time DESC LIMIT 1
        """, (auth_id, planned_shift_id))
        return cursor.fetchone() is not None

def get_planned_shift_by_id(auth_id, planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id,shift_id, planned_start, planned_end,
                   break1_start, break1_end,
                   lunch_start, lunch_end,
                   break2_start, break2_end
            FROM planned_shifts
            WHERE auth_id = ? AND id = ?
        """, (auth_id, planned_shift_id))
        return cursor.fetchone()


def get_active_shift(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, planned_shift_id, start_time
            FROM shifts
            WHERE auth_id = ? AND stop_time IS NULL
            ORDER BY start_time DESC LIMIT 1
        """, (auth_id,))
        row = cursor.fetchone()
        if row:
            return {"shift_id": row[0], "planned_shift_id": row[1], "start_time": row[2]}
        return None

def get_shift_summaries(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shift_summary WHERE auth_id = ? ORDER BY planned_start DESC", (auth_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_summaries_by_date(auth_id, date_str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM shift_summary
            WHERE auth_id = ?
              AND DATE(planned_end) = ?
            ORDER BY planned_end
        """, (auth_id, date_str))
        return cursor.fetchall()


def get_shift_summary_by_id(auth_id, shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shift_summary WHERE auth_id = ? AND shift_id = ?", (auth_id, shift_id))
        return cursor.fetchone()

def get_latest_stop_cause(auth_id, planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT reason FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ? AND reason IS NOT NULL
            ORDER BY created_at DESC LIMIT 1
        """, (auth_id, planned_shift_id))
        row = cursor.fetchone()
        return row["reason"] if row else None

def get_latest_stop_time(auth_id, planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT stop_time FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ? AND stop_time IS NOT NULL
            ORDER BY created_at DESC LIMIT 1
        """, (auth_id, planned_shift_id))
        row = cursor.fetchone()
        return row[0] if row else None



def get_summary_analytics_for_date(date_str, auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                DATE(timestamp_submitted) AS date,
                ROUND(SUM(machine_uptime) * 100.0 / NULLIF(SUM(engaged_runtime), 0), 1) AS availability_percentage,
                ROUND(SUM(total_runtime) * 100.0 / NULLIF(SUM(engaged_runtime), 0), 1) AS OEE
            FROM shift_summary
            WHERE DATE(timestamp_submitted) = ? AND auth_id = ?
            GROUP BY DATE(timestamp_submitted)
            ORDER BY DATE(timestamp_submitted) DESC
        """, (date_str, auth_id))
        row = cursor.fetchone()
        return dict(row) if row else None



def seed_auth_id(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username) VALUES (?)", (auth_id,))
        conn.commit()

def get_all_usernames():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users")
        rows = cursor.fetchall()
        return [row["username"] for row in rows]

def get_password_by_username(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (auth_id,))
        row = cursor.fetchone()
        return row["password_hash"] if row else None

def change_shift_completion( planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE planned_shifts
            SET is_completed = TRUE
            WHERE  id = ?
        """, ( planned_shift_id,))

def get_active_shift(auth_id):
    """
    Returns the shift that is currently running for the user.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM planned_shifts
            WHERE auth_id = ?
              AND is_completed = FALSE
              AND DATETIME(planned_start) <= DATETIME('now', '+1 second')
              AND DATETIME(planned_end) > DATETIME('now')
            ORDER BY planned_start ASC
            LIMIT 1
        """, (auth_id,))
        return cursor.fetchone()

def get_future_shifts(auth_id):
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM planned_shifts
            WHERE auth_id = ?
              AND is_completed = FALSE
              AND DATETIME(planned_start) > DATETIME('now')
            ORDER BY planned_start ASC
            LIMIT 1
        """, (auth_id,))
        return cursor.fetchone()




def get_all_uncompleted_shifts(auth_id):
    """
    Returns all planned shifts for the user that have not been marked as completed.
    Includes past, running, and future shifts.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM planned_shifts
            WHERE auth_id = ?
              AND is_completed = FALSE
            ORDER BY planned_start ASC
        """, (auth_id,))
        return cursor.fetchall()

def delete_all_uncompleted_except(auth_id, keep_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM planned_shifts
            WHERE auth_id = ? AND is_completed = FALSE AND id != ?
        """, (auth_id, keep_id))
        conn.commit()
def delete_planned_shift_by_id(auth_id, shift_id):
      # adjust if your import is different

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM planned_shifts
            WHERE id = ? AND auth_id = ?
        """, (shift_id, auth_id))
        conn.commit()

def get_user_timezone(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timezone FROM users WHERE username = ?", (auth_id,))
        row = cursor.fetchone()
        return row[0] if row else "UTC"
def get_7_day_summary_analytics(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                DATE(timestamp_submitted) AS date,
                ROUND(SUM(machine_uptime) * 100.0 / NULLIF(SUM(engaged_runtime), 0), 1) AS availability_percentage,
                ROUND(SUM(total_runtime) * 100.0 / NULLIF(SUM(engaged_runtime), 0), 1) AS OEE
            FROM shift_summary
            WHERE DATE(timestamp_submitted) >= DATE('now', '-7 days')
              AND auth_id = ?
            GROUP BY DATE(timestamp_submitted)
            ORDER BY DATE(timestamp_submitted) DESC
        """, (auth_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_latest_start(auth_id, planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT start_time
            FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ? AND start_time IS NOT NULL
            ORDER BY start_time DESC
            LIMIT 1
        """, (auth_id, planned_shift_id))
        result = cursor.fetchone()
        return result[0] if result else None

def get_log_for_shift(auth_id, planned_shift_id, shift_id):
    with get_connection() as conn:
          cursor = conn.cursor()
          cursor.execute("""
            SELECT *
            FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ? AND id = ?

            """,(auth_id, planned_shift_id, shift_id))
          log = cursor.fetchone()
          return log

def edit_log_by_shift_id(auth_id, planned_shift_id, shift_id, start_time, stop_time, reason, cause, comments, part_count):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE shifts
            SET 
                start_time = ?,
                stop_time = ?,
                reason = ?,
                cause = ?,
                comments = ?,
                part_count = ?
                
            WHERE
                auth_id = ? AND
                planned_shift_id = ? AND
                id = ?;
        """, (
            start_time,
            stop_time,
            reason,
            cause,
            comments,
            part_count,
            auth_id,
            planned_shift_id,
            shift_id
        ))
        conn.commit()
def get_first_start(auth_id, planned_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM shifts
            WHERE auth_id = ?
              AND planned_shift_id = ?
              AND start_time IS NOT NULL
            ORDER BY stop_time ASC
            LIMIT 1;
        """, (auth_id, planned_id))
        result = cursor.fetchone()
        return result

def get_shift_logs_id(auth_id, planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, start_time, stop_time, cause, comments, part_count
            FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ?
            ORDER BY id
        """, (auth_id, planned_shift_id))
        return cursor.fetchall()

def insert_shift_start_by_id(auth_id, planned_id, shift_id, start_time):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE shifts
            SET start_time = ?
            WHERE id = ? AND planned_shift_id = ? AND auth_id = ?
        """, (start_time, shift_id, planned_id, auth_id))
        conn.commit()

def get_summary_analytics_by_date_range(auth_id, start_date, end_date):
    """
    Fetches summary analytics from shift_summary within a date range (UTC-based),
    ordered from oldest to newest.

    Parameters:
        auth_id (str): The user's ID.
        start_date (str): Start date in 'YYYY-MM-DD' format (UTC).
        end_date (str): End date in 'YYYY-MM-DD' format (UTC).

    Returns:
        List[Dict]: List of dicts containing date, availability_percentage, and OEE.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                DATE(timestamp_submitted) AS date,
                ROUND(SUM(machine_uptime) * 100.0 / NULLIF(SUM(engaged_runtime), 0), 1) AS availability_percentage,
                ROUND(SUM(total_runtime) * 100.0 / NULLIF(SUM(engaged_runtime), 0), 1) AS OEE
            FROM shift_summary
            WHERE DATE(timestamp_submitted) BETWEEN ? AND ?
              AND auth_id = ?
            GROUP BY DATE(timestamp_submitted)
            ORDER BY DATE(timestamp_submitted) ASC
        """, (start_date, end_date, auth_id))
        return [dict(row) for row in cursor.fetchall()]

def get_summary_analytics_by_date_range_2(auth_id, start_date, end_date):
    """
    Returns a single averaged row for availability and OEE across a date range (UTC-based).
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ROUND(SUM(machine_uptime) * 100.0 / NULLIF(SUM(engaged_runtime), 0), 1) AS availability_percentage,
                ROUND(SUM(total_runtime) * 100.0 / NULLIF(SUM(engaged_runtime), 0), 1) AS OEE
            FROM shift_summary
            WHERE DATE(timestamp_submitted) BETWEEN ? AND ?
              AND auth_id = ?
        """, (start_date, end_date, auth_id))

        row = cursor.fetchone()
        return dict(row) if row else None

def get_target_cycle_time(auth_id, planned_shift_id):
    """
    Returns the target_cycle_time for a given auth_id and planned_shift_id.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT target_cycle_time
            FROM planned_shifts
            WHERE auth_id = ? AND id = ?
        """, (auth_id, planned_shift_id))

        row = cursor.fetchone()
        return row["target_cycle_time"] if row else None









def update_expected_parts(auth_id, shift_id, expected_parts):
    """
    Stores the expected_parts value into the shifts table.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE shifts
            SET expected_parts = ?
            WHERE auth_id = ? AND id = ?
        """, (expected_parts, auth_id, shift_id))
        conn.commit()

def get_expected_parts(auth_id):
    """
    Fetches the most recent non-zero expected_parts value for the user from the shifts table.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT expected_parts
            FROM shifts
            WHERE auth_id = ? AND expected_parts IS NOT NULL AND expected_parts > 0
            ORDER BY id DESC
            LIMIT 1
        """, (auth_id,))
        row = cursor.fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0
def get_latest_shift_row_id(auth_id, planned_shift_id):
    """
    Retrieves the latest shift row ID for a given user and planned shift.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id
            FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (auth_id, planned_shift_id))
        row = cursor.fetchone()
        return row[0] if row else None
def update_total_parts(planned_shift_id, auth_id, parts):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE planned_shifts
            SET total_parts = ?
            WHERE id = ? AND auth_id = ?
        """, (parts, planned_shift_id, auth_id))
        conn.commit()
def update_total_rejects(planned_shift_id, auth_id, rejects):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE planned_shifts
            SET total_rejects = ?
            WHERE id = ? AND auth_id = ?
        """, (rejects, planned_shift_id, auth_id))
        conn.commit()
def get_total_parts_for_shift(auth_id, planned_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT total_parts
            FROM planned_shifts
            WHERE auth_id = ? AND id = ?
        """, (auth_id, planned_id))
        result = cursor.fetchone()
        return result[0] if result else 0

def get_total_rejected_parts(auth_id, planned_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT total_rejects
            FROM planned_shifts
            WHERE auth_id = ? AND id = ?
        """, (auth_id, planned_id))
        result = cursor.fetchone()
        return result[0] if result else 0

def get_bit_from_mock_tags():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT value
            FROM mock_tags
            LIMIT 1
        """)
        result = cursor.fetchone()
        return result[0] if result else False

def set_mock_bit(auth_id, value):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE mock_tags
            SET value = ?, timestamp = ?
            WHERE auth_id = ?
        """, (value, datetime.utcnow(), auth_id))

def set_mock_auth_id(auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mock_tags (auth_id, value, timestamp)
            VALUES (?, ?, ?)
            
            DO UPDATE SET
                value = EXCLUDED.value,
                timestamp = EXCLUDED.timestamp;
        """, (auth_id, False, datetime.utcnow()))

def create_runtime_entry(auth_id, planned_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO shift_runtime (auth_id, planned_id, clock_state, last_updated)
            VALUES (?, ?, FALSE, ?)
            ON CONFLICT (auth_id, planned_id) DO NOTHING
            """, (auth_id, planned_id, datetime.utcnow()))
def get_runtime_state(auth_id, planned_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT clock_state FROM shift_runtime
            WHERE auth_id = ? AND planned_id = ?
        """, (auth_id, planned_id))
        result = cursor.fetchone()
        return result[0] if result else False
def set_runtime_state(auth_id, planned_id, new_state):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE shift_runtime
            SET clock_state = ?,
                last_updated = ?
            WHERE auth_id = ? AND planned_id = ?
        """, (new_state, datetime.utcnow(), auth_id, planned_id))
def get_all_runtime_states():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT auth_id, planned_id, clock_state, last_updated
            FROM shift_runtime
            ORDER BY last_updated DESC
        """)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]



def get_active_planned_shift():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM planned_shifts
            WHERE is_completed = FALSE
            ORDER BY planned_start ASC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

def get_current_active_shift():
    now = datetime.now(timezone.utc)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM planned_shifts
            WHERE is_completed = FALSE
              AND planned_start <= ?
              AND planned_end >= ?
            ORDER BY planned_start ASC
            LIMIT 1
        """, (now, now))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
def get_timezone():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timezone
            FROM users
            ORDER BY id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return row[0] if row else "UTC"

def get_current_state():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT overall_state
            FROM runtime_state
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        return result[0] if result else None
def set_next_transition(path):
    with get_connection() as conn:
        cursor = conn.cursor()
        # Clear existing row first (if any)
        cursor.execute("DELETE FROM app_state;")
        # Insert new transition path
        cursor.execute("""
            UPDATE runtime_state
            SET next_transition = ?,
            WHERE auth_id = 1,

            
        """, (path,))
        conn.commit()
def set_next_transition_and_message(path, message):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runtime_state
            SET next_transition = ?,
                message = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE auth_id = 1
        """, (path, message))
        conn.commit()
def get_next_transition():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT next_transition, message
            FROM runtime_state
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        return result if result else None

def pop_latest_path():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runtime_state
            SET next_transition = NULL,
                updated_at = NULL,
                message = NULL
            WHERE auth_id = 1
        """)
        conn.commit()
def update_current_state(new_state):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE shift_runtime
            SET state = ?
           
              
        """, (new_state,))
        conn.commit()

def update_planned_shift_by_id(
    auth_id,
    planned_id,
    planned_start,
    planned_end,
    break1_start,
    break1_end,
    lunch_start,
    lunch_end,
    break2_start,
    break2_end,
    cycle_time
):
    # Format all datetime values before updating
    planned_start = format_datetime_for_db(planned_start)
    planned_end = format_datetime_for_db(planned_end)
    break1_start = format_datetime_for_db(break1_start)
    break1_end = format_datetime_for_db(break1_end)
    lunch_start = format_datetime_for_db(lunch_start)
    lunch_end = format_datetime_for_db(lunch_end)
    break2_start = format_datetime_for_db(break2_start)
    break2_end = format_datetime_for_db(break2_end)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE planned_shifts
            SET
                planned_start = ?,
                planned_end = ?,
                break1_start = ?,
                break1_end = ?,
                lunch_start = ?,
                lunch_end = ?,
                break2_start = ?,
                break2_end = ?,
                target_cycle_time = ?
            WHERE auth_id = ? AND id = ?
        """, (
            planned_start,
            planned_end,
            break1_start,
            break1_end,
            lunch_start,
            lunch_end,
            break2_start,
            break2_end,
            cycle_time,
            auth_id,
            planned_id
        ))
        conn.commit()
def store_past_state(state, auth_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO state_events (state, auth_id)
            VALUES (?, ?)
        """, (state, auth_id))
        conn.commit()

def get_all_planned_shifts():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, planned_start, planned_end,
                       break1_start, break1_end,
                       lunch_start, lunch_end,
                       break2_start, break2_end,
                       target_cycle_time
                FROM planned_shifts
                WHERE is_completed = False
            """)
            rows = cursor.fetchall()

            
        def iso_format_or_none(value):
                     if not value:
                          return None
                     if isinstance(value, str):
                        try:
                         value = datetime.fromisoformat(value)
                        except ValueError:
                             return None  # or raise/log an error
                     return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

        return [
                {
                    "id": row[0],
                    "start_time": iso_format_or_none(row[1]),
                    "end_time": iso_format_or_none(row[2]),
                    "break1_start": iso_format_or_none(row[3]),
                    "break1_end": iso_format_or_none(row[4]),
                    "lunch_start": iso_format_or_none(row[5]),
                    "lunch_end": iso_format_or_none(row[6]),
                    "break2_start": iso_format_or_none(row[7]),
                    "break2_end": iso_format_or_none(row[8]),
                    "target_cycle_time": row[9]
                }
                for row in rows
            ]
    except Exception as e:
        print("❌ DB error in get_all_planned_shifts:", e)
        return []




def update_shift(shift_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE planned_shifts
            SET planned_start = ?,
                planned_end = ?,
                break1_start = ?,
                break1_end = ?,
                lunch_start = ?,
                lunch_end = ?,
                break2_start = ?,
                break2_end = ?,
                target_cycle_time = ?
            WHERE id = ?
        """, (
            clean_timestamp(data.get("start")),
            clean_timestamp(data.get("end")),
            clean_timestamp(data.get("break1_start")),
            clean_timestamp(data.get("break1_end")),
            clean_timestamp(data.get("lunch_start")),
            clean_timestamp(data.get("lunch_end")),
            clean_timestamp(data.get("break2_start")),
            clean_timestamp(data.get("break2_end")),
            data.get("target_cycle_time"),
            shift_id
        ))


def does_shift_overlap(start, end, exclude_id=None):
    # Ensure datetime inputs
    if isinstance(start, str):
        start = clean_timestamp(start)
    if isinstance(end, str):
        end = clean_timestamp(end)

    query = """
        SELECT id FROM planned_shifts
        WHERE is_completed = FALSE
          AND planned_end > ?
          AND planned_start < ?
    """
    params = [start, end]

    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone() is not None
def create_shift(data):
    auth_id = 1  # Hardcoded for now

    with get_connection() as conn:
        cursor = conn.cursor()

        # Get the highest existing shift_id
        cursor.execute("SELECT MAX(shift_id) FROM planned_shifts WHERE auth_id = ?", (auth_id,))
        max_id_raw = cursor.fetchone()[0]
        max_id = int(max_id_raw) if max_id_raw is not None else 0
        new_shift_id = max_id + 1

        cursor.execute("""
            INSERT INTO planned_shifts (
                auth_id, shift_id,
                planned_start, planned_end,
                break1_start, break1_end,
                lunch_start, lunch_end,
                break2_start, break2_end,
                target_cycle_time,
                is_completed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE)
        """, (
            auth_id, new_shift_id,
            clean_timestamp(data.get("start")),
            clean_timestamp(data.get("end")),
            clean_timestamp(data.get("break1_start")),
            clean_timestamp(data.get("break1_end")),
            clean_timestamp(data.get("lunch_start")),
            clean_timestamp(data.get("lunch_end")),
            clean_timestamp(data.get("break2_start")),
            clean_timestamp(data.get("break2_end")),
            data.get("target_cycle_time"),
        ))

        conn.commit()
def delete_shift(shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM planned_shifts WHERE id = ?", (shift_id,))

def insert_saved_shift_template( title, planned_start, planned_end,
                                 break1_start=None, break1_end=None,
                                 lunch_start=None, lunch_end=None,
                                 break2_start=None, break2_end=None,
                                 target_cycle_time=None,auth_id=1):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO saved_shifts (
                    title, planned_start, planned_end,
                    break1_start, break1_end,
                    lunch_start, lunch_end,
                    break2_start, break2_end,
                    target_cycle_time, auth_id
                ) VALUES (
                    ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?,?
                )
            """, (
                title, planned_start, planned_end,
                break1_start, break1_end,
                lunch_start, lunch_end,
                break2_start, break2_end,
                target_cycle_time,auth_id
            ))
    except Exception as e:
        print("❌ DB error in insert_saved_shift_template:", e)
        raise

def get_all_saved_shifts(auth_id = 1):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, planned_start, planned_end,
                       break1_start, break1_end,
                       lunch_start, lunch_end,
                       break2_start, break2_end,
                       target_cycle_time
                FROM saved_shifts
                WHERE auth_id = ?
                ORDER BY created_at DESC
            """, (auth_id,))
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "planned_start": row[2],
                    "planned_end": row[3],
                    "break1_start": row[4],
                    "break1_end": row[5],
                    "lunch_start": row[6],
                    "lunch_end": row[7],
                    "break2_start": row[8],
                    "break2_end": row[9],
                    "target_cycle_time": row[10]
                }
                for row in rows
            ]
    except Exception as e:
        print("❌ DB error in get_all_saved_shifts:", e)
        return []

def is_transition_locked():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT lock_transition FROM app_state LIMIT 1")
        row = cursor.fetchone()
        return row and row["lock_transition"]


def set_transition_lock(value: bool):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE app_state
            SET lock_transition = ?
            WHERE id = 1
        """, (value,))
        conn.commit()

def check_null_stops(planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) AS null_stop_count
            FROM shifts
            WHERE planned_shift_id = ? AND reason IS NULL
        """, (planned_shift_id,))
        result = cursor.fetchone()
        
        return  result["null_stop_count"] or 0
        



def pop_unfinished_shift(planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM unfinished_shifts
            WHERE id = (
                SELECT id FROM unfinished_shifts
                WHERE planned_shift_id = ?
                ORDER BY id DESC
                LIMIT 1
            )
        """, (planned_shift_id,))
        conn.commit()

def insert_unfinished_shift(planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO unfinished_shifts (planned_shift_id)
            VALUES (?)
        """, (planned_shift_id,))
        conn.commit()

def get_all_unfinished_shift_ids():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT planned_shift_id FROM unfinished_shifts
        """)
        rows = cursor.fetchall()
        return [row["planned_shift_id"] for row in rows]

def set_planned_id(planned_id):
    auth_id = 1
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runtime_state
            SET planned_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE auth_id = ?
        """, (planned_id, auth_id))
        conn.commit()

def clear_planned_id():
    auth_id = 1
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runtime_state
            SET planned_id = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE auth_id = ?
        """, (auth_id,))
        conn.commit()

def get_planned_id():
    auth_id = 1
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT planned_id
            FROM runtime_state
            WHERE auth_id = ?
        """, (auth_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_latest_stop_reason():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fence_fault, e_stop, missed_pick, missed_placement,
                   quality_stop, collision, sensor_audit_flag,
                   stopped_by_operator, other
            FROM stop_reasons
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        row = cursor.fetchone()

    if not row:
        return "Other"

    # Map column names to their values
    fields = [
        "Fence Fault", "E-Stop", "Missed Pick", "Missed Placement",
        "Quality Stop", "Collision", "Sensor Audit Flag",
        "Stopped By Operator", "Other"
    ]
    active = [fields[i] for i, val in enumerate(row) if val == 1]

    if len(active) == 1:
        return active[0]
    else:
        return "Other"
def get_latest_shift_by_auth_and_planned(auth_id, planned_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT start_time
            FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ?
            ORDER BY start_time DESC
            LIMIT 1
        """, (auth_id, planned_id))
        row = cursor.fetchone()
        return row[0] if row else None

def grab_clock_state():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT clock_state
        FROM runtime_state
        LIMIT 1
        """,
            )
        row = cursor.fetchone()
        return row[0] if row else None


def change_end_shift_function(value):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runtime_state
            SET end_shift_function = ?
        """, (value,))
        conn.commit()  # Don’t forget this!

def grab_total_parts_and_reject_parts():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT total_parts, rejects
            FROM parts
            ORDER BY id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row and row[0] is not None and row[1] is not None:
            return {"total_parts": row[0], "rejects": row[1]}
        else:
            return None


def set_end_shift_reason(shift_id, auth_id):
    # assuming you're using a get_connection() helper

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE shifts
            SET reason = ?
            WHERE id = ? AND auth_id = ?
        """, ('end_shift', shift_id, auth_id))
        conn.commit()

def insert_stop_unconfirmed(auth_id, planned_shift_id):
    stop_time = datetime.now(timezone.utc).replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE shifts
            SET stop_time = ?, 
                reason = 'unconfirmed', 
                cause = 'unconfirmed',
                comments = NULL,
                part_count = NULL,
                created_at = ?
            WHERE id = (
                SELECT id FROM shifts
                WHERE auth_id = ? 
                  AND planned_shift_id = ? 
                  AND start_time IS NOT NULL 
                  AND stop_time IS NULL
                ORDER BY start_time DESC, id DESC
                LIMIT 1
            )
        """, (
            stop_time,
            stop_time,
            auth_id,
            planned_shift_id
        ))

        conn.commit()

def get_stop_cause_label(row_id):
  

    # List all reason columns except 'id' and 'timestamp'
    reason_columns = [
        "fence_fault", "e_stop", "missed_pick", "missed_placement",
        "quality_stop", "collision", "sensor_audit_flag", "stopped_by_operator", "other"
    ]

    with get_connection() as conn:
        cursor = conn.cursor()

        # Select the entire row by ID
        cursor.execute(f"""
            SELECT {', '.join(reason_columns)}
            FROM stop_reasons
            WHERE id = ?
        """, (row_id,))
        
        row = cursor.fetchone()
        if not row:
            return "other"  # If row doesn't exist

        # Count how many values are 1
        one_count = sum(1 for val in row if val == 1)

        if one_count == 1:
            # Return the name of the column that is 1
            return reason_columns[row.index(1)]
        else:
            return "other"

def insert_comment_needed(shift_id, auth_id):
    """
    Updates the 'comments' column of a specific shift to say 'required'.
    """
   

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE shifts
            SET comments = ?
            WHERE id = ? AND auth_id = ?
        """, ('unconfirmed', shift_id, auth_id))

        conn.commit()
def insert_cause_for_shift(shift_id, auth_id, cause):
    """
    Updates the 'cause' column for the given shift ID and auth ID.
    """
    

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE shifts
            SET cause = ?
            WHERE id = ? AND auth_id = ?
        """, (cause, shift_id, auth_id))

        conn.commit()
def get_latest_unconfirmed_data(shift_id):
    """
    Returns two booleans:
    - reason_unconfirmed: True if reason == 'unconfirmed'
    - comment_unconfirmed: True if comments == 'unconfirmed'
    Scopes directly by shift_id.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT reason, comments
            FROM shifts
            WHERE id = ?
        """, (shift_id,))
        
        row = cursor.fetchone()
        if not row:
            return False, False  # No such shift

        reason_unconfirmed = (row[0] == 'unconfirmed')
        comment_unconfirmed = (row[1] == 'unconfirmed')

        return reason_unconfirmed, comment_unconfirmed

def insert_reason_and_comment_to_unconfirmed(shift_id, reason, comment):
    """
    Updates the 'reason' and 'comments' fields for a given shift ID.
    """


    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE shifts
            SET reason = ?, comments = ?
            WHERE id = ?
        """, (reason, comment, shift_id))

        conn.commit()

def get_last_stop_cause(shift_id):
    """
    Returns the cause of the stop for the given shift ID.
    """
  

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cause
            FROM shifts
            WHERE id = ?
        """, (shift_id,))

        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        else:
            return "Unknown"
def get_incomplete_data(planned_id):
    """
    Returns True if any shift for the given planned_id has reason or comments marked as 'unconfirmed'.
    Returns False otherwise.
    """
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1
            FROM shifts
            WHERE planned_shift_id = ?
              AND (reason = 'unconfirmed' OR comments = 'unconfirmed' OR cause = 'unconfirmed')
            LIMIT 1
        """, (planned_id,))

        result = cursor.fetchone()
        return result is not None

def insert_unfinished_shift(planned_id):
    """
    Inserts a new entry into the unfinished_shifts table with the given planned_shift_id.
    """
   

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO unfinished_shifts (planned_shift_id)
            VALUES (?)
        """, (planned_id,))
        conn.commit()


def get_latest_unfinished_shift():
    """
    Returns the most recent planned_shift_id from the unfinished_shifts table.
    """
  

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT planned_shift_id
            FROM unfinished_shifts
            ORDER BY id DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        return row[0] if row else None

def get_unconfirmed_shift_rows(planned_shift_id):
    """
    Returns a list of shift rows (id, start_time, stop_time)
    for a given planned_shift_id where reason or comments are 'unconfirmed'.
    """


    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, start_time, stop_time
            FROM shifts
            WHERE planned_shift_id = ?
              AND (reason = 'unconfirmed' OR comments = 'unconfirmed' OR cause = 'unconfirmed')
        """, (planned_shift_id,))
        
        rows = cursor.fetchall()
        return [
            {"id": row[0], "start_time": row[1], "stop_time": row[2]}
            for row in rows
        ]

def get_last_shift_row_by_planned_id(planned_id):
    """
    Returns the most recent shift row (as a dict) for a given planned_shift_id.
    """
    

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM shifts
            WHERE planned_shift_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (planned_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None

def update_unfinished_parts(planned_shift_id, total_parts, rejected_parts):
    """
    Updates total_parts and rejected_parts for a given planned_shift_id in unfinished_shifts.
    """


    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE unfinished_shifts
            SET total_parts = ?, rejected_parts = ?
            WHERE planned_shift_id = ?
        """, (total_parts, rejected_parts, planned_shift_id))
        conn.commit()
def get_unfinished_parts(planned_shift_id):
    """
    Returns total_parts and rejected_parts from unfinished_shifts
    for the given planned_shift_id. Returns None if either is NULL.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT total_parts, rejected_parts
            FROM unfinished_shifts
            WHERE planned_shift_id = ?
        """, (planned_shift_id,))

        row = cursor.fetchone()
        if row and row[0] is not None and row[1] is not None:
            return {"total_parts": row[0], "rejected_parts": row[1]}
        else:
            return None

def pop_unfinished_shift(planned_id):
    """
    Deletes a row from unfinished_shifts for the given planned_shift_id.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM unfinished_shifts
            WHERE planned_shift_id = ?
        """, (planned_id,))
        conn.commit()
def get_end_shift_function():
    """
    Returns the current value of end_shift_function from the runtime_state table.
    """


    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT end_shift_function
            FROM runtime_state
            LIMIT 1
        """)
        row = cursor.fetchone()
        return row[0] if row else None


def get_unconfirmed_shift_by_id(shift_id):
    """
    Returns the shift row as a dict if either reason or comments is 'unconfirmed'.
    Returns None otherwise.
    """
   

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM shifts
            WHERE id = ?
              AND (reason = 'unconfirmed' OR comments = 'unconfirmed')
        """, (shift_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None


def get_last_stop_reason(auth_id, planned_shift_id):
    """
    Returns the reason for the most recent stop in shift_logs for a given planned shift.
    """
  

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT reason
            FROM shifts
            WHERE auth_id = ? AND planned_shift_id = ? AND stop_time IS NOT NULL
            ORDER BY stop_time DESC
            LIMIT 1
        """, (auth_id, planned_shift_id))

        row = cursor.fetchone()
        return row["reason"] if row else None

def set_message(message):
    """
    Inserts a new message into the runtime_state table's 'message' column.
    """
  


    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO runtime_state (message)
            VALUES (?)
        """, (message,))

        conn.commit()


def update_runtime_state(auth_id, overall_state, clock_state, shift_state):
  

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runtime_state
            SET overall_state = ?,
                clock_state = ?,
                shift_state = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE auth_id = ?
        """, (overall_state, clock_state, shift_state, auth_id))
        conn.commit()
def shift_start_already_exists(planned_id):
    """
    Returns True if there's already a shift started for this planned_id
    that hasn't been stopped yet.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1
            FROM shifts
            WHERE planned_shift_id = ?
              AND start_time IS NOT NULL
              AND stop_time IS NULL
            LIMIT 1
        """, (planned_id,))
        return cursor.fetchone() is not None

def update_runtime_state_shift_id(auth_id, shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runtime_state
            SET shift_id = ?
            WHERE auth_id = ?
        """, (shift_id, auth_id))
        conn.commit()

def get_runtime_shift_id(auth_id):
    """
    Returns the current shift_id from runtime_state for a given auth_id.
    Returns None if not set.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT shift_id
            FROM runtime_state
            WHERE auth_id = ?
            LIMIT 1
        """, (auth_id,))
        
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else None

def clear_runtime_shift_id(auth_id):
    """
    Sets shift_id to NULL in runtime_state for the given auth_id.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runtime_state
            SET shift_id = NULL
            WHERE auth_id = ?
        """, (auth_id,))
        conn.commit()


def get_unconfirmed_comments(planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM shifts
            WHERE planned_shift_id = ?
              AND (TRIM(comments) = 'unconfirmed')
        """, (planned_shift_id,))
        result = cursor.fetchone()
        return result[0]

def get_unconfirmed_reasons(planned_shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM shifts
            WHERE planned_shift_id = ?
              AND (TRIM(reason) = 'unconfirmed')
        """, (planned_shift_id,))
        result = cursor.fetchone()
        return result[0]
        
def set_first_parts_and_rejects(parts, rejects):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE parts
            SET first_parts = ?, first_rejects = ?, created_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (parts, rejects)
        )
        conn.commit()

def grab_first_parts():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT first_parts FROM parts WHERE id = 1""")
        result = cursor.fetchone()
        return result[0] if result else 0

def grab_first_rejects():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT first_rejects FROM parts WHERE id = 1""")
        result = cursor.fetchone()
        return result[0] if result else 0

def pop_first_parts_and_rejects():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT first_parts, first_rejects FROM parts WHERE id = 1""")
        result = cursor.fetchone()

        if not result:
            return (0, 0)

        parts, rejects = result

        cursor.execute("""
            UPDATE parts
            SET total_parts = 0, rejects = 0, created_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """)
        conn.commit()

 

       
        
def update_current_parts_and_rejects(parts, rejects):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE parts
            SET total_parts = ?, rejects = ?, created_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (parts, rejects))
        conn.commit()
        
def get_total_parts():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT total_parts
            FROM parts
            WHERE id = 1
        """)
        result = cursor.fetchone()
        return result[0] if result else 0

def get_total_rejects():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rejects
            FROM parts
            WHERE id = 1
        """)
        result = cursor.fetchone()
        return result[0] if result else 0

def get_multiple_causes(shift_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT multiple_causes 
        FROM shifts
        WHERE id = ? 
        """, (shift_id,))
        result = cursor.fetchone()
        return result[0] if result else 0 
        
        
def update_shift_cause_reason_comment(shift_id, cause, reason, comment):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE shifts
            SET cause = ?, reason = ?, comments = ?
            WHERE id = ?
        """, (cause, reason, comment, shift_id))
        conn.commit()

# -------------------------
# STARVED TABLE FUNCTIONS
# -------------------------

def insert_start_starved(shift_id, start_time):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO starved (shift_id, start)
            VALUES (?, ?)
        """, (shift_id, start_time))

def insert_stop_starved(shift_id, stop_time):
    with get_connection() as conn:
        cur = conn.cursor()

        # Step 1: Get the latest matching row's ID
        cur.execute("""
            SELECT id FROM starved
            WHERE shift_id = ? AND stop IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (shift_id,))
        row = cur.fetchone()

        if row is not None:
            target_id = row[0]

            # Step 2: Update only that row
            cur.execute("""
                UPDATE starved
                SET stop = ?
                WHERE id = ?
            """, (stop_time, target_id))


def get_status_starved(shift_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT stop FROM starved
            WHERE shift_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (shift_id,))
        row = cur.fetchone()
        if row is None:
            return False  # no rows for this shift = no active event
        return row[0] is None  # True if the event is still active (no stop time)



# -------------------------
# BLOCK TABLE FUNCTIONS
# -------------------------

def insert_start_block(shift_id, start_time):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO blocked (shift_id, start)
            VALUES (?, ?)
        """, (shift_id, start_time))
        
def insert_stop_block(shift_id, stop_time):
    with get_connection() as conn:
        cur = conn.cursor()

        # Step 1: Get the latest matching row's ID
        cur.execute("""
            SELECT id FROM blocked
            WHERE shift_id = ? AND stop IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (shift_id,))
        row = cur.fetchone()
        print("is it none", row)
        print("what is the shift_id", shift_id)
        if row is not None:
            target_id = row[0]
            print("target_id",targer_id)
            # Step 2: Update only that row
            cur.execute("""
                UPDATE blocked
                SET stop = ?
                WHERE id = ?
            """, (stop_time, target_id))

            


def get_status_block(shift_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT stop FROM blocked
            WHERE shift_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (shift_id,))
        row = cur.fetchone()
        if row is None:
            return False  # no rows for this shift = no active event
        return row[0] is None  # True if the event is still active (no stop time)

        
def get_all_blocked_rows(planned_id):
    with get_connection() as conn:
        cursor = conn.cursor() 
        cursor.execute("""
            SELECT * FROM blocked
            WHERE shift_id = ?
        """, (planned_id,))
        return cursor.fetchall()

def get_all_starved_rows(planned_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM starved
            WHERE shift_id = ?
        """, (planned_id,))
        return cursor.fetchall()

        

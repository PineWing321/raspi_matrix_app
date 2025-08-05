import os
import psycopg2
import psycopg2.extras
from datetime import datetime

# PostgreSQL connection

def get_connection():
    if os.getenv("SKIP_DB") == "true":
        raise RuntimeError("Database access skipped (SKIP_DB=true)")
    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", 5432)
    )

def format_datetime_for_db(dt):
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return None
    elif not isinstance(dt, datetime):
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# All DB functions now use PostgreSQL

def insert_planned_shift(auth_id, shift_id, start, end, break_start, break_end):
    start, end = format_datetime_for_db(start), format_datetime_for_db(end)
    break_start, break_end = format_datetime_for_db(break_start), format_datetime_for_db(break_end)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO planned_shifts (auth_id, shift_id, planned_start, planned_end, break_start, break_end)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (auth_id, shift_id, start, end, break_start, break_end))
            conn.commit()

def insert_shift_start(auth_id, start_time, planned_shift_id):
    start_time = format_datetime_for_db(start_time)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO shifts (auth_id, start_time, planned_shift_id)
                VALUES (%s, %s, %s)
            """, (auth_id, start_time, planned_shift_id))
            conn.commit()

def insert_final_analytics(analytics):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO shift_summary (
                    auth_id, shift_id, planned_start, planned_end,
                    scheduled_runtime, engaged_runtime, total_runtime,
                    machine_uptime, machine_efficiency, total_efficiency,
                    total_downtime, available_downtime, unavailable_downtime,
                    non_engaged_time, total_stops, machine_error_stops,
                    planned_stops, break_stops, break_start, break_end, timestamp_submitted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                analytics["auth_id"], analytics["shift_id"], analytics["planned_start"], analytics["planned_end"],
                analytics["scheduled_runtime"], analytics["engaged_runtime"], analytics["total_runtime"],
                analytics["machine_uptime"], analytics["machine_efficiency"], analytics["total_efficiency"],
                analytics["total_downtime"], analytics["available_downtime"], analytics["unavailable_downtime"],
                analytics["non_engaged_time"], analytics["total_stops"], analytics["machine_error_stops"],
                analytics["planned_stops"], analytics["break_stops"], analytics["break_start"], analytics["break_end"],
                datetime.now().isoformat()
            ))
            conn.commit()

def update_planned_end(auth_id, planned_shift_id, new_end):
    new_end = format_datetime_for_db(new_end)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE planned_shifts
                SET planned_end = %s
                WHERE auth_id = %s AND id = %s
            """, (new_end, auth_id, planned_shift_id))
            conn.commit()

def get_latest_planned_shift(auth_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT planned_start, planned_end, break_start, break_end
                FROM planned_shifts
                WHERE auth_id = %s
                ORDER BY id DESC LIMIT 1
            """, (auth_id,))
            return cursor.fetchone()

def delete_all_planned_shifts(auth_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM planned_shifts WHERE auth_id = %s", (auth_id,))
            conn.commit()

def delete_planned_shift_by_id(auth_id, planned_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM planned_shifts WHERE auth_id = %s AND id = %s", (auth_id, planned_id))
            conn.commit()

def get_all_uncompleted_planned_shifts(auth_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, planned_start, planned_end, break_start, break_end
                FROM planned_shifts
                WHERE auth_id = %s AND is_completed = FALSE
                ORDER BY id DESC
            """, (auth_id,))
            return cursor.fetchall()


def get_all_shift_rows(auth_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT start_time, stop_time, cause
                FROM shifts
                WHERE auth_id = %s
                ORDER BY id DESC
            """, (auth_id,))
            return cursor.fetchall()

def get_planned_shift_id(auth_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM planned_shifts WHERE auth_id = %s ORDER BY id DESC LIMIT 1", (auth_id,))
            result = cursor.fetchone()
            return result[0] if result else None

def get_latest_unstopped_shift_id(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM shifts
                WHERE auth_id = %s
                  AND planned_shift_id = %s
                  AND stop_time IS NULL
                ORDER BY id DESC
                LIMIT 1
            """, (auth_id, planned_shift_id))
            result = cursor.fetchone()
            return result[0] if result else None

def update_shift_stop(shift_id, auth_id, stop_time,reason, cause, details, part_count):
    stop_time = format_datetime_for_db(stop_time)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE shifts
                SET stop_time = %s, reason = %s ,cause = %s, comments = %s, part_count = %s
                WHERE id = %s AND auth_id = %s
            """, (stop_time, reason, cause, details, part_count, shift_id, auth_id))
            conn.commit()

def get_shift_logs_by_planned_id(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, start_time, stop_time, reason,cause, comments, part_count
                FROM shifts
                WHERE auth_id = %s AND planned_shift_id = %s
                ORDER BY start_time
            """, (auth_id, planned_shift_id))
            return cursor.fetchall()

def get_planned_start_by_id(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT planned_start
                FROM planned_shifts
                WHERE auth_id = %s AND id = %s
            """, (auth_id, planned_shift_id))
            result = cursor.fetchone()
            return result["planned_start"] if result else None


def get_last_stop_time(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT stop_time FROM shifts
                WHERE auth_id = %s AND planned_shift_id = %s AND stop_time IS NOT NULL
                ORDER BY stop_time DESC LIMIT 1
            """, (auth_id, planned_shift_id))
            result = cursor.fetchone()
            return result[0] if result else None

def is_clock_running(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM shifts
                WHERE auth_id = %s AND planned_shift_id = %s AND stop_time IS NULL
                ORDER BY start_time DESC LIMIT 1
            """, (auth_id, planned_shift_id))
            return cursor.fetchone() is not None

def get_planned_shift_by_id(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT shift_id, planned_start, planned_end, break_start, break_end
                FROM planned_shifts
                WHERE auth_id = %s AND id = %s
            """, (auth_id, planned_shift_id))
            return cursor.fetchone()

def get_active_shift(auth_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, planned_shift_id, start_time
                FROM shifts
                WHERE auth_id = %s AND stop_time IS NULL
                ORDER BY start_time DESC LIMIT 1
            """, (auth_id,))
            row = cursor.fetchone()
            if row:
                return {"shift_id": row[0], "planned_shift_id": row[1], "start_time": row[2]}
            return None

def get_shift_summaries(auth_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM shift_summary WHERE auth_id = %s ORDER BY planned_start DESC", (auth_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

def get_summaries_by_date(auth_id, date_str):
    timezone = get_user_timezone(auth_id)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM shift_summary
                WHERE auth_id = %s
                  AND DATE(timestamp_submitted AT TIME ZONE 'UTC' AT TIME ZONE %s) = %s
                ORDER BY timestamp_submitted 
            """, (auth_id, timezone, date_str))
            return cursor.fetchall()


def get_shift_summary_by_id(auth_id, shift_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM shift_summary WHERE auth_id = %s AND shift_id = %s", (auth_id, shift_id))
            return cursor.fetchone()

def get_latest_stop_cause(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT reason FROM shifts
                WHERE auth_id = %s AND planned_shift_id = %s AND cause IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (auth_id, planned_shift_id))
            row = cursor.fetchone()
            return row["reason"] if row else None

def get_latest_stop_time(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT stop_time FROM shifts
                WHERE auth_id = %s AND planned_shift_id = %s AND stop_time IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """, (auth_id, planned_shift_id))
            row = cursor.fetchone()
            return row[0] if row else None



def get_summary_analytics_for_date(date_str, auth_id):
    timezone = get_user_timezone(auth_id)

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(f"""
                SELECT 
                    DATE(timestamp_submitted AT TIME ZONE 'UTC' AT TIME ZONE %s) AS date,
                    ROUND((SUM(machine_uptime) * 100.0 / NULLIF(SUM(engaged_runtime), 0))::numeric, 1) AS availability_percentage,
                    ROUND((SUM(total_runtime) * 100.0 / NULLIF(SUM(engaged_runtime), 0))::numeric, 1) AS OEE
                FROM shift_summary
                WHERE DATE(timestamp_submitted AT TIME ZONE 'UTC' AT TIME ZONE %s) = %s AND auth_id = %s
                GROUP BY DATE(timestamp_submitted AT TIME ZONE 'UTC' AT TIME ZONE %s)
                ORDER BY DATE(timestamp_submitted AT TIME ZONE 'UTC' AT TIME ZONE %s) DESC
            """, (timezone, timezone, date_str, auth_id, timezone, timezone))
            row = cursor.fetchone()
            return dict(row) if row else None



def seed_auth_id(auth_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (username) VALUES (%s)", (auth_id,))
            conn.commit()

def get_all_usernames():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT username FROM users")
            rows = cursor.fetchall()
            return [row["username"] for row in rows]

def get_password_by_username(auth_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT password_hash FROM users WHERE username = %s", (auth_id,))
            row = cursor.fetchone()
            return row["password_hash"] if row else None

def change_shift_completion(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                UPDATE planned_shifts
                SET is_completed = TRUE
                WHERE auth_id = %s AND id = %s
            """, (auth_id, planned_shift_id))
        conn.commit()

def get_active_shift(auth_id):
    """
    Returns the shift that is currently running for the user.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT *
                FROM planned_shifts
                WHERE auth_id = %s
                  AND is_completed = FALSE
                  AND planned_start::timestamp <= NOW() + INTERVAL '1 second'
                  AND planned_end::timestamp > NOW()
                ORDER BY planned_start::timestamp ASC
                LIMIT 1
            """, (auth_id,))
            return cursor.fetchone()


def get_future_shifts(auth_id):
    """
    Returns the next future shift for the user that hasn't started yet.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT *
                FROM planned_shifts
                WHERE auth_id = %s
                  AND is_completed = FALSE
                  AND planned_start::timestamp > NOW()
                ORDER BY planned_start::timestamp ASC
                LIMIT 1
            """, (auth_id,))
            return cursor.fetchone()



def get_all_uncompleted_shifts(auth_id):
    """
    Returns all planned shifts for the user that have not been marked as completed.
    Includes past, running, and future shifts.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT *
                FROM planned_shifts
                WHERE auth_id = %s
                  AND is_completed = FALSE
                ORDER BY planned_start ASC
            """, (auth_id,))
            return cursor.fetchall()

def delete_all_uncompleted_except(auth_id, keep_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM planned_shifts
                WHERE auth_id = %s AND is_completed = FALSE AND id != %s
            """, (auth_id, keep_id))
            conn.commit()
def delete_planned_shift_by_id(auth_id, shift_id):
      # adjust if your import is different

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM planned_shifts
                WHERE id = %s AND auth_id = %s
            """, (shift_id, auth_id))
            conn.commit()

def get_user_timezone(auth_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT timezone FROM users WHERE username = %s", (auth_id,))
            row = cursor.fetchone()
            return row[0] if row else "UTC"
def get_7_day_summary_analytics(auth_id):
    timezone = get_user_timezone(auth_id)
    
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(f"""
                SELECT 
                    DATE(timestamp_submitted AT TIME ZONE 'UTC' AT TIME ZONE %s) AS date,
                    ROUND((SUM(machine_uptime) * 100.0 / NULLIF(SUM(engaged_runtime), 0))::numeric, 1) AS availability_percentage,
                    ROUND((SUM(total_runtime) * 100.0 / NULLIF(SUM(engaged_runtime), 0))::numeric, 1) AS OEE
                FROM shift_summary
                WHERE DATE(timestamp_submitted AT TIME ZONE 'UTC' AT TIME ZONE %s) >= CURRENT_DATE - INTERVAL '7 days'
                  AND auth_id = %s
                GROUP BY DATE(timestamp_submitted AT TIME ZONE 'UTC' AT TIME ZONE %s)
                ORDER BY DATE(timestamp_submitted AT TIME ZONE 'UTC' AT TIME ZONE %s) DESC
            """, (timezone, timezone, auth_id, timezone, timezone))
            return [dict(row) for row in cursor.fetchall()]

def get_latest_start(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT start_time
                FROM shifts
                WHERE auth_id = %s AND planned_shift_id = %s AND start_time IS NOT NULL
                ORDER BY start_time DESC
                LIMIT 1
            """, (auth_id, planned_shift_id))
            result = cursor.fetchone()
            return result[0] if result else None

def get_log_for_shift(auth_id, planned_shift_id, shift_id):
    with get_connection() as conn:
          with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
            SELECT *
            FROM shifts
            WHERE auth_id = %s AND planned_shift_id = %s AND id = %s

            """,(auth_id, planned_shift_id, shift_id))
            log = cursor.fetchone()
            return log

def edit_log_by_shift_id(auth_id, planned_shift_id, shift_id, start_time, stop_time, reason, cause, comments, part_count):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                UPDATE shifts
                SET 
                    start_time = %s,
                    stop_time = %s,
                    reason = %s,
                    cause = %s,
                    comments = %s,
                    part_count = %s
                    
                WHERE
                    auth_id = %s AND
                    planned_shift_id = %s AND
                    id = %s;
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
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT *
                FROM shifts
                WHERE auth_id = %s
                  AND planned_shift_id = %s
                  AND start_time IS NOT NULL
                ORDER BY stop_time ASC
                LIMIT 1;
            """, (auth_id, planned_id))
            result = cursor.fetchone()
            return result

def get_shift_logs_id(auth_id, planned_shift_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, start_time, stop_time, cause, comments, part_count
                FROM shifts
                WHERE auth_id = %s AND planned_shift_id = %s
                ORDER BY id
            """, (auth_id, planned_shift_id))
            return cursor.fetchall()

def insert_shift_start_by_id(auth_id, planned_id, shift_id, start_time):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE shifts
                SET start_time = %s
                WHERE id = %s AND planned_shift_id = %s AND auth_id = %s
            """, (start_time, shift_id, planned_id, auth_id))
            conn.commit()

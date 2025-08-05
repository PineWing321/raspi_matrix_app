from src.db import get_planned_start_by_id, get_shift_logs_by_planned_id, get_planned_shift_by_id,  get_latest_stop_time, get_latest_stop_cause
from datetime import datetime, timedelta, timezone
from flask import session
from dateutil import parser

def format_seconds(seconds):
    return str(timedelta(seconds=int(seconds)))

def parse_time_field(value):
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        try:
            dt = parser.isoparse(value)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError):
            return None
    return None

def parse_hhmmss_to_seconds(time_str):
    try:
        h, m, s = map(int, time_str.split(":"))
        return h * 3600 + m * 60 + s
    except (ValueError, AttributeError):
        return 0

def calculate_uptime_downtime(planned_shift_id):
    auth_id = session["auth_id"]
    planned_start = get_planned_start_by_id(auth_id, planned_shift_id)
    rows = get_shift_logs_by_planned_id(auth_id, planned_shift_id)

    machine_uptime = 0
    total_runtime = 0
    planned_runtime = 0
    downtime = 0
    downtime_due_to_machine = 0
    if not rows or not planned_start:
        return {
            "machine_uptime": "00:00:00",
            "total_runtime": "00:00:00",
            "planned_runtime": "00:00:00",
            "machine_efficiency": 0.0,
            "OEE": 0.0
        }

    planned_start = parse_time_field(planned_start)
    first_start = parse_time_field(rows[0]["start_time"])

    if not planned_start or not first_start:
        return {
            "machine_uptime": "00:00:00",
            "total_runtime": "00:00:00",
            "planned_runtime": "00:00:00",
            "machine_efficiency": 0.0,
            "OEE": 0.0
        }

    planned_runtime += (first_start - planned_start).total_seconds()
    print(first_start)
    print(planned_start)
    if planned_runtime < 0:
        print("what the")
    for i in range(len(rows) - 1):
        current = rows[i]
        nxt = rows[i + 1]
        reason = current["reason"]

        start_time = parse_time_field(current["start_time"])
        stop_time = parse_time_field(current["stop_time"])
        next_start = parse_time_field(nxt["start_time"])

        if not start_time or not stop_time or not next_start:
            continue

        uptime = (stop_time - start_time).total_seconds()
        downtime = (next_start - stop_time).total_seconds()

        if reason == "Machine Related":
            planned_runtime += uptime + downtime
            machine_uptime += uptime
            total_runtime += uptime
 
        elif reason == "Planned Stop" or reason == "Break":
            planned_runtime += uptime
            machine_uptime += uptime
            total_runtime += uptime
        elif reason == "Non-Machine Related":
            planned_runtime += uptime + downtime
            machine_uptime += uptime + downtime
            total_runtime += uptime

    last = rows[-1]
    last_start = parse_time_field(last["start_time"])
    last_stop = parse_time_field(last["stop_time"])

    if last_start and last_stop:
        final_uptime = (last_stop - last_start).total_seconds()
        machine_uptime += final_uptime
        planned_runtime += final_uptime
        total_runtime += final_uptime

    machine_efficiency = (machine_uptime / planned_runtime * 100) if planned_runtime else 0
    OEE = (total_runtime / planned_runtime * 100) if planned_runtime else 0

    is_clock_running = last["stop_time"] is None
    live_start_time = last["start_time"] if is_clock_running else None
    adjust =  (first_start - planned_start).total_seconds()
    downtime_due_to_machine = (planned_runtime - machine_uptime) - adjust
    downtime_1 = (planned_runtime - total_runtime)
    non_mr_downtime = downtime_1 - downtime_due_to_machine
    print(downtime_1)
    print(downtime_due_to_machine)
    return {
        "machine_uptime": str(timedelta(seconds=round(machine_uptime))),
        "total_runtime": str(timedelta(seconds=round(total_runtime))),
        "planned_runtime": str(timedelta(seconds=round(planned_runtime))),
        "machine_efficiency": round(machine_efficiency, 2),
        "downtime": str(timedelta(seconds=round(downtime_1))),
        "non_downtime": str(timedelta(seconds=round(non_mr_downtime))),
        "machine_downtime": str(timedelta(seconds=round(downtime_due_to_machine))),
        "OEE": round(OEE, 2),
        "is_clock_running": is_clock_running,
        "live_start_time": live_start_time
    }

def final_analytics(planned_shift_id, shift_end):
    auth_id = session["auth_id"]
    analytics = calculate_uptime_downtime(planned_shift_id)
    planned_shift = get_planned_shift_by_id(auth_id, planned_shift_id)
    planned_runtime = planned_time(planned_shift)
    planned_start = planned_shift["planned_start"]
    planned_end = planned_shift["planned_end"]
    break_end = planned_shift["break_end"]
    break_start = planned_shift["break_start"]
    last_stop = get_latest_stop_time(auth_id, planned_shift_id)
    cause = get_latest_stop_cause(auth_id, planned_shift_id)

    shift_end = parse_time_field(shift_end)
    last_stop = parse_time_field(last_stop)

    rows = get_shift_logs_by_planned_id(auth_id, planned_shift_id)
    total_stops = len(rows)
    machine_stops = sum(1 for row in rows if row["reason"] == "Machine Related")
    planned_stops = sum(1 for row in rows if row["reason"] == "Planned Stop")
    break_stops = sum(1 for row in rows if row["reason"] == "Break")

    machine_uptime = parse_hhmmss_to_seconds(analytics["machine_uptime"])
    total_runtime = parse_hhmmss_to_seconds(analytics["total_runtime"])
    engaged_runtime = parse_hhmmss_to_seconds(analytics["planned_runtime"])

    if shift_end and last_stop and last_stop < shift_end:
        difference = (shift_end - last_stop).total_seconds()
        if cause == "Planned Stop" or cause == "Break":
            pass
        elif cause == "Non-Machine Related":
            engaged_runtime += difference 
            machine_uptime += difference
        elif cause == "Machine Related":
            engaged_runtime += difference
        else:
            print(f"[WARN] Unrecognized cause '{cause}', assuming idle.")
            engaged_runtime += difference

    total_downtime = max(0, engaged_runtime - total_runtime)
    unavailable_downtime = max(0, engaged_runtime - machine_uptime)
    available_downtime = max(0, total_downtime - unavailable_downtime)
    machine_efficiency = (machine_uptime / engaged_runtime) * 100 if engaged_runtime > 0 else 0
    total_efficiency = (total_runtime / engaged_runtime) * 100 if engaged_runtime > 0 else 0
    non_engaged_time = max(0, planned_runtime - engaged_runtime)

    return {
        "auth_id": auth_id,
        "shift_id": planned_shift_id,
        "planned_start": planned_start,
        "planned_end": planned_end,
        "scheduled_runtime": planned_runtime,
        "engaged_runtime": engaged_runtime,
        "total_runtime": total_runtime,
        "machine_uptime": machine_uptime,
        "machine_efficiency": machine_efficiency,
        "total_efficiency": total_efficiency,
        "total_downtime": total_downtime,
        "unavailable_downtime": unavailable_downtime,
        "available_downtime": available_downtime,
        "non_engaged_time": non_engaged_time,
        "total_stops": total_stops,
        "machine_error_stops": machine_stops,
        "planned_stops": planned_stops,
        "break_stops": break_stops,
        "break_start": break_start,
        "break_end": break_end,
    }

def planned_time(planned_shift):
    start = parse_time_field(planned_shift["planned_start"])
    end = parse_time_field(planned_shift["planned_end"])
    break_start = parse_time_field(planned_shift["break_start"])
    break_end = parse_time_field(planned_shift["break_end"])

    if not start or not end:
        return 0
    total_time = (end - start).total_seconds()

    if break_start and break_end:
        break_time = (break_end - break_start).total_seconds()
        total_time -= break_time

    return total_time

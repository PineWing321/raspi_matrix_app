from src.db import get_planned_start_by_id, get_shift_logs_by_planned_id, get_planned_shift_by_id,  get_latest_stop_time, get_latest_stop_cause, get_total_parts_for_shift, get_total_rejected_parts, get_target_cycle_time, get_last_stop_reason, get_all_blocked_rows, get_all_starved_rows
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
    auth_id = 1
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
    machine_uptime += (first_start - planned_start).total_seconds()
    print("hello22",first_start)
    print("hello2", planned_start)
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
        elif reason == "unconfirmed":
            print("reason unconfirmed no addition to analytics")
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
    
    downtime_due_to_machine = (planned_runtime - machine_uptime) 
    downtime_1 = (planned_runtime - total_runtime)
    non_mr_downtime = downtime_1 - downtime_due_to_machine
    print("help1", downtime_1)
    print("what is the non_mr_downtime", non_mr_downtime)
    print("downtime due to machine" , downtime_due_to_machine)
    
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

def final_analytics(cycle_status, planned_shift_id,total_parts, total_rejects):
    auth_id = 1
    analytics = calculate_uptime_downtime(planned_shift_id) 
    planned_shift = get_planned_shift_by_id(auth_id, planned_shift_id)
    if not planned_shift:
        return 0
    planned_shift = dict(planned_shift)
    planned_runtime = planned_time(planned_shift)
    planned_start = planned_shift.get("planned_start")
    planned_end = planned_shift.get("planned_end")
   
    # Updated: new breaks
    break1_start = planned_shift.get("break1_start")
    break1_end = planned_shift.get("break1_end")
    lunch_start = planned_shift.get("lunch_start")
    lunch_end = planned_shift.get("lunch_end")
    break2_start = planned_shift.get("break2_start")
    break2_end = planned_shift.get("break2_end")

    last_stop = get_latest_stop_time(auth_id, planned_shift_id)
    

    last_stop = parse_time_field(last_stop)
  
    rows = get_shift_logs_by_planned_id(auth_id, planned_shift_id)
    total_stops = len(rows)
    machine_stops = sum(1 for row in rows if row["reason"] == "Machine Related")
    planned_stops = sum(1 for row in rows if row["reason"] == "Planned Stop")
    break_stops = sum(1 for row in rows if row["reason"] == "Break")

    machine_uptime = parse_hhmmss_to_seconds(analytics["machine_uptime"])
    total_runtime = parse_hhmmss_to_seconds(analytics["total_runtime"])
    engaged_runtime = parse_hhmmss_to_seconds(analytics["planned_runtime"])
    if not cycle_status:
        last_reason = get_last_stop_reason(auth_id, planned_shift_id)
        planned_end_str= parse_time_field(planned_end)
        difference = (planned_end_str - last_stop).total_seconds()
        print("hopefulyl my difference is not wack", difference) 
        if last_reason == "Non-Machine Related":
            machine_uptime += difference
            engaged_runtime += difference
        elif last_reason == "Machine Related":
            engaged_runtime += difference
        elif last_reason == "Planned Stop" or "Break":
            print("nothing added")
   
    total_downtime = max(0, engaged_runtime - total_runtime)
    unavailable_downtime = max(0, engaged_runtime - machine_uptime)
    available_downtime = max(0, total_downtime - unavailable_downtime)
    machine_efficiency = (machine_uptime / engaged_runtime) * 100 if engaged_runtime > 0 else 0
    total_efficiency = (total_runtime / engaged_runtime) * 100 if engaged_runtime > 0 else 0
    non_engaged_time = max(0, planned_runtime - engaged_runtime)
    print("total_parts", total_parts)
    oee_data = oee_calculation(
        planned_time=engaged_runtime,
        OEE=total_efficiency,
        Machine_efficiency=machine_efficiency,
        planned_id=planned_shift_id,
        auth_id=auth_id,
        total_parts=int(total_parts),
        total_rejects=int(total_rejects)
    )
    print(oee_data["total_parts"])
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
        "break1_start": break1_start,
        "break1_end": break1_end,
        "lunch_start": lunch_start,
        "lunch_end": lunch_end,
        "break2_start": break2_start,
        "break2_end": break2_end,

        "total_parts": oee_data["total_parts"],
        "total_rejects": oee_data["total_rejects"],
        "expected_parts": oee_data["expected_parts"],
        "quality": oee_data["quality"],
        "performance": oee_data["performance"],
        "final_oee": oee_data["oee"],
        "final_mr_oee": oee_data["mr_oee"]
    }

def planned_time(planned_shift):

    planned_shift = dict(planned_shift)
    start = parse_time_field(planned_shift["planned_start"])
    end = parse_time_field(planned_shift["planned_end"])

    # Parse all breaks
    break1_start = parse_time_field(planned_shift.get("break1_start"))
    break1_end = parse_time_field(planned_shift.get("break1_end"))
    lunch_start = parse_time_field(planned_shift.get("lunch_start"))
    lunch_end = parse_time_field(planned_shift.get("lunch_end"))
    break2_start = parse_time_field(planned_shift.get("break2_start"))
    break2_end = parse_time_field(planned_shift.get("break2_end"))

    if not start or not end:
        return 0

    total_time = (end - start).total_seconds()

    def subtract_if_valid(start_time, end_time):
        if start_time and end_time and start_time < end_time:
            return (end_time - start_time).total_seconds()
        return 0

    total_time -= subtract_if_valid(break1_start, break1_end)
    total_time -= subtract_if_valid(lunch_start, lunch_end)
    total_time -= subtract_if_valid(break2_start, break2_end)

    return total_time

def oee_calculation(planned_time, OEE, Machine_efficiency, planned_id, auth_id, total_parts, total_rejects):
   
    cycle_time = get_target_cycle_time(auth_id, planned_id)
    
    expected_parts = planned_time / cycle_time if cycle_time else 0
    total_actual = total_parts + total_rejects

    quality = (total_parts / total_actual) * 100 if total_actual > 0 else 100.0
    performance = (total_parts / expected_parts) * 100 if expected_parts > 0 else 0.0
    oee = (performance * quality * OEE) / 10000
    mr_oee = (performance * quality * Machine_efficiency) / 10000

    return {
        "total_parts": total_parts,
        "total_rejects": total_rejects,
        "expected_parts": expected_parts,
        "quality": quality,
        "performance": performance,
        "oee": oee,
        "mr_oee": mr_oee
    }
    


def _calc_total_duration(rows):
    total = 0
    for row in rows:
        start = row["start"]
        stop = row["stop"]

        try:
            start_sec = int(datetime.fromisoformat(start).timestamp()) if start else 0
            stop_sec = int(datetime.fromisoformat(stop).timestamp()) if stop else 0
            if stop_sec == 0:
                continue
            total += (stop_sec - start_sec)
        except Exception as e:
            print(f"Skipping row due to error: {e}")
            continue

    return total

def get_starved_time(planned_id):
    return _calc_total_duration(get_all_starved_rows(planned_id))

def get_blocked_time(planned_id):
    return _calc_total_duration(get_all_blocked_rows(planned_id))

        

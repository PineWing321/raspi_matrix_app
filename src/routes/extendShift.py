#endshift.py
from flask import Blueprint, render_template, request, redirect, session
from datetime import datetime
from src.db import update_planned_end, get_planned_shift_by_id, get_planned_shift_id, delete_planned_shift_by_id,update_planned_shift_by_id
from zoneinfo import ZoneInfo
bp = Blueprint("extend_shift", __name__)

@bp.route("/extend_shift", methods=["GET", "POST"])
def extend_shift():
    auth_id = session["auth_id"]
    planned_id = session["planned_id"]
    planned_shift = get_planned_shift_by_id(auth_id, planned_id)

    if request.method == "POST":
        new_end_str = request.form.get("planned_end")
        try:
            # Parse DB UTC time
            old_end = datetime.fromisoformat(planned_shift["planned_end"]).replace(tzinfo=ZoneInfo("UTC"))

            # Parse user input as local time and convert to UTC
            new_end_local = datetime.strptime(new_end_str, "%Y-%m-%dT%H:%M").replace(tzinfo=ZoneInfo("America/Chicago"))
            new_end_utc = new_end_local.astimezone(ZoneInfo("UTC"))

            if new_end_utc < old_end:
                error = "New planned end must be later than the current planned end."
                return render_template("extendShift.html", planned_shift=planned_shift, error=error, end_for_input=new_end_str)

            # Store in UTC with space format
            new_end_iso = new_end_utc.strftime("%Y-%m-%d %H:%M:%S")
            update_planned_end(auth_id, planned_id, new_end_iso)

            return redirect("/")

        except Exception as e:
            error = "Invalid datetime format."
            fallback = planned_shift["planned_end"][:16].replace(" ", "T")
            return render_template("extendShift.html", planned_shift=planned_shift, error=error, end_for_input=fallback)

    # On GET — send original end in local time
    end_utc = datetime.fromisoformat(planned_shift["planned_end"]).replace(tzinfo=ZoneInfo("UTC"))
    end_local = end_utc.astimezone(ZoneInfo("America/Chicago"))
    end_for_input = end_local.strftime("%Y-%m-%dT%H:%M")

    return render_template("extendShift.html", planned_shift=planned_shift, end_for_input=end_for_input)

@bp.route("/adjust_shift", methods=["GET", "POST"])
def adjust_shift():
    auth_id = session.get("auth_id")
    planned_id = session.get("planned_id")
    planned_id = int(planned_id)
    if not auth_id or not planned_id:
        return redirect("/")

    if request.method == "POST":
        # Grab new values from the form
        planned_start_raw = request.form.get("planned_start")
        planned_end_raw = request.form.get("planned_end")
        break1_start_raw = request.form.get("break1_start") or None
        break1_end_raw = request.form.get("break1_end") or None
        lunch_start_raw = request.form.get("lunch_start") or None
        lunch_end_raw = request.form.get("lunch_end") or None
        break2_start_raw = request.form.get("break2_start") or None
        break2_end_raw = request.form.get("break2_end") or None
        cycle_time = request.form.get("target_cycle_time")

        session["cycle_time"] = cycle_time

        # Validate
        error = validate_shift_times(
            planned_start_raw,
            planned_end_raw,
            break1_start_raw,
            break1_end_raw,
            lunch_start_raw,
            lunch_end_raw,
            break2_start_raw,
            break2_end_raw
        )
        if error:
            return render_template("planned_shift.html", error=error)

        try:
            # Update the existing row instead of inserting a new one
            update_planned_shift_by_id(
                auth_id,
                int(planned_id),
                planned_start_raw,
                planned_end_raw,
                break1_start_raw,
                break1_end_raw,
                lunch_start_raw,
                lunch_end_raw,
                break2_start_raw,
                break2_end_raw,
                cycle_time
            )

            return redirect("/")

        except Exception as e:
            print(f"[ERROR] Failed to update planned shift: {e}")
            return render_template("planned_shift.html", error="Something went wrong while updating the shift.")

    # GET request — show form
    return render_template("planned_shift.html", error=None)


def validate_shift_times(start_str, end_str,
                         break1_start_str, break1_end_str,
                         lunch_start_str, lunch_end_str,
                         break2_start_str, break2_end_str):
    try:
        start = datetime.fromisoformat(start_str) if start_str else None
        end = datetime.fromisoformat(end_str) if end_str else None
        break1_start = datetime.fromisoformat(break1_start_str) if break1_start_str else None
        break1_end = datetime.fromisoformat(break1_end_str) if break1_end_str else None
        lunch_start = datetime.fromisoformat(lunch_start_str) if lunch_start_str else None
        lunch_end = datetime.fromisoformat(lunch_end_str) if lunch_end_str else None
        break2_start = datetime.fromisoformat(break2_start_str) if break2_start_str else None
        break2_end = datetime.fromisoformat(break2_end_str) if break2_end_str else None
    except ValueError:
        return "Invalid date or time format."

    if not start or not end:
        return "Shift start and end times are required."
    if start >= end:
        return "Shift start time must be before end time."

    # Helper to check break pair logic
    def check_break_pair(b_start, b_end, name):
        if b_start and not b_end:
            return f"{name} start time is set but end time is missing."
        if b_end and not b_start:
            return f"{name} end time is set but start time is missing."
        if b_start and b_end:
            if b_start >= b_end:
                return f"{name} start time must be before end time."
            if b_start < start or b_end > end:
                return f"{name} must be fully within the shift window."
        return None

    for b_start, b_end, name in [
        (break1_start, break1_end, "Break 1"),
        (lunch_start, lunch_end, "Lunch"),
        (break2_start, break2_end, "Break 2"),
    ]:
        msg = check_break_pair(b_start, b_end, name)
        if msg:
            return msg

    # Collect all fully-formed breaks for overlap checking
    breaks = []
    if break1_start and break1_end:
        breaks.append((break1_start, break1_end, "Break 1"))
    if lunch_start and lunch_end:
        breaks.append((lunch_start, lunch_end, "Lunch"))
    if break2_start and break2_end:
        breaks.append((break2_start, break2_end, "Break 2"))

    # Check for overlaps between breaks
    for i in range(len(breaks)):
        for j in range(i + 1, len(breaks)):
            b1_start, b1_end, b1_name = breaks[i]
            b2_start, b2_end, b2_name = breaks[j]
            if b1_end > b2_start and b1_start < b2_end:
                return f"{b1_name} overlaps with {b2_name}."

    return None

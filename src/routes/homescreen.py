from flask import Blueprint, render_template, request, redirect, session
from src.db import ( ## suspect db, might need some cleaning up
    get_latest_planned_shift,
    get_future_shifts,
    get_active_shift,
    get_all_uncompleted_shifts,
    delete_all_uncompleted_except,
    get_user_timezone,
    get_all_unfinished_shift_ids,
    get_current_active_shift,
    get_current_state,
    get_planned_shift_by_id,
    get_active_planned_shift,
    get_planned_id,
    get_end_shift_function
   
)
from datetime import datetime
from zoneinfo import ZoneInfo  # Requires Python 3.9+

bp = Blueprint("homescreen", __name__)

# Utility: Convert UTC ISO string to local time string
def utc_to_local(utc_str, tz_str):
    try:
        utc_dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        local_dt = utc_dt.astimezone(ZoneInfo(tz_str))
        return local_dt.strftime("%Y-%m-%d %I:%M %p")  # Example: 2025-06-10 03:15 PM
    except Exception as e:
        print(f"[ERROR] Failed to convert {utc_str} to local: {e}")
        return utc_str  # Fallback: return original UTC string

@bp.route("/", methods=["GET", "POST"])
def home_screen():
    auth_id = session.get("auth_id")
    if not auth_id:
        print("🔒 auth_id missing")
        return redirect("/login")
    current_state = get_current_state()
    end_shift = get_end_shift_function()
    if end_shift:
        print("is we ended???", end_shift)
        return redirect("/end_shift")
    # Grab overall state (as text) and planned_id from DB
    current_state = get_current_state()  # returns text like "idle", "waiting", etc.
    planned_id = get_planned_id()

    print("📌 overall_state:", current_state)
    print("📌 planned_id:", planned_id)

    # 🟢 Case: Planned_shift but not running
    if not planned_id:
        if current_state in {"waiting", "cycle_running"}:
            planned_shift = get_active_planned_shift()
            if not planned_shift: 
                 return render_template(
                "homescreen.html",
                auth_id=auth_id,
                is_shift_in_window=False,
                display_planned_shift=False
                )
            return render_template(
                "homescreen.html",
                auth_id=auth_id,
                is_shift_in_window=False,
                display_planned_shift=True,
                planned_start=planned_shift["planned_start"],
                planned_end=planned_shift["planned_end"]
            )
        else:  # idle, unplanned_running, etc.
            return render_template(
                "homescreen.html",
                auth_id=auth_id,
                is_shift_in_window=False,
                display_planned_shift=False
            )

    # 🔄 Case: shift is active
    elif current_state in {"machine_off", "machine_on"}:
        planned_shift = get_planned_shift_by_id(auth_id, planned_id)
        return render_template(
            "homescreen.html",
            auth_id=auth_id,
            is_shift_in_window=True,
            display_planned_shift=True,
            planned_start=planned_shift["planned_start"],
            planned_end=planned_shift["planned_end"]
        )

    # 🔚 Catch: planned_id exists but shift is not active anymore
    else:
        print("🧹 popping stale planned_id from session")
        session.pop("planned_id", None)
        return render_template(
            "homescreen.html",
            auth_id=auth_id,
            is_shift_in_window=False,
            display_planned_shift=False
        )

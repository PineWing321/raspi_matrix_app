from flask import Blueprint, render_template, request, redirect, session
from src.services.time_utils import get_current_html_time
from src.db import (
    get_planned_shift_id,
    insert_shift_start,
    get_latest_unstopped_shift_id,
    update_shift_stop,
    is_clock_running,
    get_latest_stop_time,
    get_latest_start
)
from dateutil import parser
from datetime import timezone
import pytz

bp = Blueprint("record", __name__)

@bp.route("/record_start", methods=["GET", "POST"])
def record_start():
    auth_id = session.get("auth_id")
    if not auth_id:
        return redirect("/")

    planned_shift_id = session.get("planned_id")
    if not planned_shift_id:
        return render_template(
            "record_start.html",
            time_val=get_current_html_time(),
            error="You must plan a shift before starting."
        )

    if is_clock_running(auth_id, planned_shift_id):
        return render_template(
            "record_start.html",
            time_val=get_current_html_time(),
            error="Clock is already running — you cannot start again."
        )

    if request.method == "POST":
        raw_time = request.form.get("start_time")

        latest_stop = get_latest_stop_time(auth_id, planned_shift_id)
        if latest_stop:
            latest_stop = parser.isoparse(latest_stop)
            if latest_stop.tzinfo is None:
                latest_stop = latest_stop.replace(tzinfo=timezone.utc)
        print("🛑 RAW latest_stop from DB:", latest_stop, type(latest_stop))

        if not raw_time:
            return redirect("/record_start")

        try:
            user_tz = pytz.timezone(session.get("timezone", "UTC"))
            naive_dt = parser.isoparse(raw_time)
            local_dt = user_tz.localize(naive_dt)
            start_time_utc = local_dt.astimezone(timezone.utc).isoformat()
            start_dt_utc = parser.isoparse(start_time_utc)
            if latest_stop and start_dt_utc < latest_stop:
                return render_template(
                    "record_start.html",
                    time_val=get_current_html_time(),
                    error="cannot start before last stop"
                )
            print(f"[UTC Converted] Start time: {start_time_utc}")
            insert_shift_start(auth_id, start_time_utc, planned_shift_id)
        except Exception as e:
            print(f"[ERROR] Failed to insert shift start: {e}")
            return render_template(
                "record_start.html",
                time_val=get_current_html_time(),
                error="Failed to record shift start. Please try again."
            )

        return redirect(f"/record_start_success?shift_id={start_time_utc}")

    return render_template("record_start.html", time_val=get_current_html_time(), error=None)


@bp.route("/record_stop", methods=["GET", "POST"])
def record_stop():
    auth_id = session.get("auth_id")
    if not auth_id:
        return redirect("/")

    planned_shift_id = session.get("planned_id")
    if not is_clock_running(auth_id, planned_shift_id):
        return render_template(
            "record_stop.html",
            time_val=get_current_html_time(),
            error="Clock is not running — nothing to stop."
        )

    if request.method == "POST":
        raw_time = request.form.get("stop_time")
        if not raw_time:
            return redirect("/record_stop")

        reason = request.form.get("reason")
        details = request.form.get("details")
        part_count = request.form.get("part_count", "").strip()
        cause = request.form.get("cause")
        start_time = get_latest_start(auth_id, planned_shift_id)
        if start_time:
            start_time = parser.isoparse(start_time)
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
        try:
            part_count = int(part_count)
        except (TypeError, ValueError):
            part_count = 0

        try:
            user_tz = pytz.timezone(session.get("timezone", "UTC"))
            naive_dt = parser.isoparse(raw_time)
            local_dt = user_tz.localize(naive_dt)
            stop_time_utc = local_dt.astimezone(timezone.utc).isoformat()
            stop_dt_utc = parser.isoparse(stop_time_utc)
            print("⏰ raw_time:", raw_time)
            print("🌍 user_tz:", user_tz)
            print("🧠 naive_dt:", naive_dt.isoformat())
            print("📍 localized:", local_dt.isoformat())
            if start_time and stop_dt_utc < start_time:
                return render_template(
                    "record_stop.html",
                    time_val=get_current_html_time(),
                    error="cannot stop before last start"
                )
            print("🛑 Stop submission:", stop_time_utc, cause, details, part_count)
            shift_id = get_latest_unstopped_shift_id(auth_id, planned_shift_id)
            if shift_id:
                update_shift_stop(shift_id, auth_id, stop_time_utc, reason, cause, details, part_count)
        except Exception as e:
            print(f"[ERROR] Failed to update shift stop: {e}")
            return render_template(
                "record_stop.html",
                time_val=get_current_html_time(),
                error="Failed to stop shift. Please try again."
            )

        return redirect("/record_stop_success")

    return render_template("record_stop.html", time_val=get_current_html_time(), error=None)


@bp.route("/record_start_success")
def record_start_success():
    shift_id = request.args.get("shift_id")
    return render_template("record_start_success.html", shift_id=shift_id)


@bp.route("/record_stop_success")
def record_stop_success():
    return render_template("record_stop_success.html")

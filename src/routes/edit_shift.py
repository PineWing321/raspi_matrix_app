from flask import Blueprint, render_template, session, redirect, request
from src.db import get_log_for_shift, edit_log_by_shift_id, get_first_start, get_shift_logs_by_planned_id, get_shift_logs_id, get_planned_start_by_id, insert_shift_start_by_id, get_planned_id, get_multiple_causes, update_shift_cause_reason_comment
from datetime import datetime, timezone
from dateutil import parser
from zoneinfo import ZoneInfo

bp = Blueprint("/edit_shift", __name__)

@bp.route("/edit_shift", methods=["POST", "GET"])
def end_shift():
    auth_id = 1
    planned_id = get_planned_id()

    if not auth_id:
        return redirect("/login")
    if not planned_id:
        return redirect("/")

    shift_id_raw = request.args.get("shift_id", "").strip()
    if not shift_id_raw.isdigit():
        return redirect("/", code=302)
    
    shift_id = int(shift_id_raw)
    multiple_causes = get_multiple_causes(shift_id)
    if multiple_causes:
        return redirect(f"/edit_multiple_causes?shift_id={shift_id}&planned_id={planned_id}&multiple_causes={multiple_causes}")

    log = get_log_for_shift(auth_id, planned_id, shift_id)
    cause = log["cause"]
    need_comment = cause in {"other", "quality_stop"}

    if request.method == "POST":
        reason = request.form.get("reason")
        cause = request.form.get("cause")
        comment = request.form.get("comments")
        part_count = request.form.get("part_count")

        try:
            edit_log_by_shift_id(
                auth_id, planned_id, shift_id,
                log["start_time"],
                log["stop_time"],
                reason, cause, comment, part_count
            )
            return redirect("/index")
        except Exception as e:
            print(f"[ERROR] Failed to update shift: {e}")
            return render_template("edit_shift.html", log=log, error="Could not save changes.", need_comment=need_comment)

    return render_template("edit_shift.html", log=log, need_comment=need_comment)
    
    
@bp.route("/edit_multiple_causes", methods=["POST", "GET"])
def edit_multiple_causes():
    shift_id = request.args.get("shift_id") 
    planned_id = request.args.get("planned_id")
    auth_id = 1
    if not planned_id:
        planned_id = get_planned_id()
    if request.method == "POST": 
        shift_id = request.form.get("shift_id") 
        comment = request.form.get("comment") 
        reason = request.form.get("reason") 
        cause = request.form.get("cause")
        
        update_shift_cause_reason_comment(shift_id, cause, reason, comment)
        return redirect("/index")
    multiple_causes = request.args.get("multiple_causes") 
    
    log = get_log_for_shift(auth_id, planned_id, shift_id) 
    
    return render_template("edit_multiple_causes.html", log=log, multiple_causes=multiple_causes, shift_id = shift_id) 

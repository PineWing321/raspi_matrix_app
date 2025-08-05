#details.py
from flask import Blueprint, render_template,session, redirect, request
from src.db import get_planned_shift_id, get_shift_logs_by_planned_id, get_planned_id

bp = Blueprint("details", __name__)

@bp.route("/details", methods=["POST", "GET"])
def shift_details():
    auth_id = session["auth_id"]
    planned_id = get_planned_id()
    shift_logs = None

    if request.method == "POST":
        shift_id = request.form.get("shift_id", "").strip()
        print(f"hello '{shift_id}'")
        return redirect(f"/edit_shift?shift_id={shift_id}")
    if not planned_id:
        return render_template("shift_details.html",shift_logs=[], go_to_home = True)
    shift_logs = get_shift_logs_by_planned_id(auth_id, planned_id)
    print("🟡 Shift logs:", shift_logs)  # Add this line
  
    return render_template("shift_details.html", shift_logs=shift_logs, go_to_home = False)

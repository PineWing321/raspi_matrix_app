from flask import Blueprint, render_template, session, request, redirect
from src.db import get_summaries_by_date, get_shift_summary_by_id, get_shift_logs_by_planned_id, get_7_day_summary_analytics, get_summary_analytics_for_date,get_summary_analytics_by_date_range,get_summary_analytics_by_date_range_2
from datetime import datetime
bp = Blueprint("history", __name__)

@bp.route("/history", methods=["GET", "POST"])
def history():
    auth_id = session.get("auth_id")
    if not auth_id:
        return redirect("/")  # Ensure user is authenticated

    # Always pull fresh analytics from DB
    seven_days = get_7_day_summary_analytics(auth_id)

    if request.method == "POST":
        date = request.form.get("date")
        if not date:
            return redirect("/history")
        return redirect(f"/shifts_for_date?date={date}")

    seven_days = sorted(seven_days, key=lambda x: x['date'])

    return render_template("history.html", seven_days=seven_days)


@bp.route("/shifts_for_date", methods=["GET", "POST"])
def shifts_for_date():
    auth_id = session.get("auth_id")
    if not auth_id:
        return redirect("/")

    date = request.args.get("date") or request.form.get("date")
    if not date:
        print("We aint getting the date on the back")
        return redirect("/history")

    if request.method == "POST":
        shift_id = request.form.get("shift_id")
        return redirect(f"/one_shift_history?shift_id={shift_id}&date={date}")

    summaries = get_summaries_by_date(auth_id, date)
    daily_summary = get_summary_analytics_for_date(date, auth_id)
    if not summaries:
        summaries = None
    return render_template("shifts_for_date.html", summaries=summaries, date=date, daily_summary=daily_summary)

@bp.route("/one_shift_history", methods=["GET", "POST"])
def one_shift_history():
    auth_id = session.get("auth_id")
    if not auth_id:
        return redirect("/")

    shift_id = request.args.get("shift_id") or request.form.get("shift_id")
    date = request.args.get("date") or request.form.get("date")

    if not shift_id or not date:
        return redirect("/history")

    shift_data = get_shift_summary_by_id(auth_id, shift_id)

    # Build breaks list
    breaks = []

    if shift_data["break1_start"] and shift_data["break1_end"]:
        breaks.append({
            "label": "Break 1",
            "start": shift_data["break1_start"],
            "end": shift_data["break1_end"]
        })
    if shift_data["lunch_start"] and shift_data["lunch_end"]:
        breaks.append({
            "label": "Lunch",
            "start": shift_data["lunch_start"],
            "end": shift_data["lunch_end"]
        })
    if shift_data["break2_start"] and shift_data["break2_end"]:
        breaks.append({
            "label": "Break 2",
            "start": shift_data["break2_start"],
            "end": shift_data["break2_end"]
        })

    if request.method == "POST":
        return redirect(f"/shift_logs?shift_id={shift_id}&date={date}")

    return render_template("one_shift_history.html", shift_data=shift_data, breaks=breaks, date=date, shift_id=shift_id)


@bp.route("/shift_logs", methods=["GET", "POST"])
def shift_log():
    auth_id = session.get("auth_id")
    if not auth_id:
        return redirect("/")

    shift_id = request.args.get("shift_id")
    date = request.args.get("date")

    if not shift_id or not date:
        return redirect("/history")

    shift_logs = get_shift_logs_by_planned_id(auth_id, shift_id)

    return render_template("shift_log.html", shift_logs=shift_logs, shift_id=shift_id, date=date)

@bp.route("/shift_range_summary", methods=["POST","GET"])
def shift_range_summary():
    auth_id = session["auth_id"]
    if not auth_id:
        return redirect("/login")
    start = request.form.get("start_date")
    end = request.form.get("end_date")
    start = datetime.strptime(start, "%Y-%m-%d").date()
    end= datetime.strptime(end, "%Y-%m-%d").date()
    print(end)
    print(start)
    analytics = get_summary_analytics_by_date_range(auth_id,start,end)
    print(analytics)
    if not analytics:
        analytics = None
        return render_template("range_of_days.html", analytics = analytics)
    one_analytics =  get_summary_analytics_by_date_range_2(auth_id, start, end)
    print(one_analytics)
    if not one_analytics:
        one_analytics = None
    return render_template("range_of_days.html", analytics=analytics, one_analytics=one_analytics)

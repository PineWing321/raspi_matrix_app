#plan.py
from flask import Blueprint, render_template, request, redirect, session, jsonify
from datetime import datetime, timedelta

from src.services.time_utils import parse_time, time_to_str
from src.services.validation import validate_shift_times, validate_shift
from src.db import insert_planned_shift, get_latest_planned_shift, get_planned_shift_id, is_clock_running,get_latest_stop_cause, get_active_shift, get_planned_shift_by_id, get_target_cycle_time, get_expected_parts, update_expected_parts, get_latest_shift_row_id, update_total_parts, update_total_rejects, get_total_parts_for_shift, get_total_rejected_parts, get_current_state, get_all_planned_shifts, create_shift, update_shift, delete_shift, insert_saved_shift_template, get_all_saved_shifts, check_null_stops, get_planned_id,  get_end_shift_function, get_unconfirmed_comments, get_unconfirmed_reasons, grab_first_parts, grab_first_rejects, get_total_parts, get_total_rejects, get_status_starved, get_status_block
from src.services.analytics import calculate_uptime_downtime, get_starved_time, get_blocked_time
from src.globals import grab_total_parts, grab_total_rejects
bp = Blueprint("plan", __name__)


@bp.route("/api/planned_shifts")
def api_get_planned_shifts():
    data = get_all_planned_shifts()
    print("what is the data", data)
    return jsonify(data)


@bp.route("/api/create_shift", methods=["POST"])
def api_create_shift():
    data = request.get_json()
    is_valid, error = validate_shift(data)
    if not is_valid:
        return jsonify({"error": error}), 400
    create_shift(data)
    return jsonify({"status": "success"}), 201

@bp.route("/api/update_shift/<int:shift_id>", methods=["POST"])
def api_update_shift(shift_id):
    data = request.get_json()
    data["id"] = shift_id  # needed for overlap exclusion
    is_valid, error = validate_shift(data, editing=True)
    if not is_valid:
        return jsonify({"error": error}), 400
    update_shift(shift_id, data)
    return jsonify({"status": "success"}), 200


@bp.route("/api/delete_shift/<int:shift_id>", methods=["DELETE"])
def api_delete_shift(shift_id):
    try:
        delete_shift(shift_id)
        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        print("❌ Error in delete_shift:", e)
        return jsonify({"error": "Failed to delete shift"}), 500


@bp.route("/api/save_template", methods=["POST"])
def save_template():


    try:
        data = request.get_json()
        print("📥 Incoming template data:", data)

        # Optionally: validate required fields
        if not data.get("title") or not data.get("planned_start") or not data.get("planned_end"):
            return jsonify({"error": "Missing required fields"}), 400

        insert_saved_shift_template(
         
            title=data.get("title"),
            planned_start=data.get("planned_start"),
            planned_end=data.get("planned_end"),
            break1_start=data.get("break1_start"),
            break1_end=data.get("break1_end"),
            lunch_start=data.get("lunch_start"),
            lunch_end=data.get("lunch_end"),
            break2_start=data.get("break2_start"),
            break2_end=data.get("break2_end"),
            target_cycle_time=data.get("target_cycle_time"),
        )

        return jsonify({"status": "success"}), 201

    except Exception as e:
        print("❌ Error saving template:", e)
        return jsonify({"error": "Internal server error"}), 500

@bp.route("/api/saved_shifts", methods=["GET"])
def get_saved_shifts():
    try:
        raw = get_all_saved_shifts()

        def format_time(t):
         if not t:
          return None
         if isinstance(t, str):
          try:
            # Parse string assuming it's in HH:MM or HH:MM:SS format
            parsed = datetime.strptime(t, "%H:%M:%S" if len(t.split(":")) == 3 else "%H:%M")
            return parsed.strftime("%I:%M %p")
          except Exception as e:
            print("⚠️ Failed to parse time string:", t, e)
            return t  # fallback to raw string
         try:
           return t.strftime("%I:%M %p")
         except Exception as e:
          print("⚠️ format_time failed on:", t, e)
          return t

        serialized = []
        for row in raw:
            serialized.append({
                "id": row["id"],
                "title": row["title"],
                "planned_start": format_time(row["planned_start"]),
                "planned_end": format_time(row["planned_end"]),
                "break1_start": format_time(row["break1_start"]),
                "break1_end": format_time(row["break1_end"]),
                "lunch_start": format_time(row["lunch_start"]),
                "lunch_end": format_time(row["lunch_end"]),
                "break2_start": format_time(row["break2_start"]),
                "break2_end": format_time(row["break2_end"]),
                "target_cycle_time": row["target_cycle_time"]
            })

        return jsonify(serialized), 200

    except Exception as e:
        print("❌ Error fetching saved shifts:", e)
        return jsonify({"error": "Failed to fetch saved shifts"}), 500


@bp.route("/plan", methods=["GET", "POST"]) # potentially clear out soon. 
def plan_shift():
    auth_id = session.get("auth_id")
    if not auth_id:
        return redirect("/")  # Redirect to login if not authenticated
    
    existing = get_active_shift(auth_id)
    if existing:
        return render_template("planned_shift.html", error="A shift is already planned. End it before planning another.")
    
    if request.method == "POST":
        # Required shift times
        planned_start_raw = request.form.get("planned_start")
        planned_end_raw = request.form.get("planned_end")
         
        # Optional breaks
        break1_start_raw = request.form.get("break1_start") or None
        break1_end_raw = request.form.get("break1_end") or None
        lunch_start_raw = request.form.get("lunch_start") or None
        lunch_end_raw = request.form.get("lunch_end") or None
        break2_start_raw = request.form.get("break2_start") or None
        break2_end_raw = request.form.get("break2_end") or None
        cycle_time = request.form.get("target_cycle_time")

        session["cycle_time"] = cycle_time
        print("🟡 Raw input:", planned_start_raw, planned_end_raw,
              break1_start_raw, break1_end_raw,
              lunch_start_raw, lunch_end_raw,
              break2_start_raw, break2_end_raw)

        # Validate all times
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

        shift_id = datetime.now().strftime("%Y-%m-%d")

        try:
            insert_planned_shift(
                auth_id,
                shift_id,
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
        except Exception as db_err:
            print(f"[ERROR] Failed to insert planned shift: {db_err}")
            return render_template("planned_shift.html", error="Something went wrong while saving the shift.")

    return render_template("planned_shift.html", error=None)

# Route for displaying home screen with current or planned shift
# Route for displaying home screen with current or planned shift

# adding new auto ping feature for parts, do we ping for it every second? i dont see why not. We can just start every 30 seconds. 
# first we have to go and clean up this route, not exactly the best thing im seeing here, lots of clumping, lots of grouping up. 
# figure out and rewire the parts stuff, remove and properly clean up the enter totalparts% and oee% performance etc. 
@bp.route("/index")
def index():
    auth_id = session.get("auth_id")
    if not auth_id:
        return redirect("/")
    end_shift = get_end_shift_function()

    if end_shift:
        return redirect("/end_shift")

    planned_shift_id = get_planned_id()
    if not planned_shift_id:
        return redirect("/login")

    #probs not good 
    

    cycle_time = session.get("cycle_time")
    if not cycle_time:
        cycle_time = get_target_cycle_time(auth_id, planned_shift_id)
        if not cycle_time:
            return redirect("/login", error="Failed to grab cycle time. Try again later.")
        session["cycle_time"] = cycle_time  # Cache it
    cycle_time = float(cycle_time)  # ✅ ensure it's a number
    # Try to fetch planned shift
    print(cycle_time)
    planned_shift = get_planned_shift_by_id(auth_id, planned_shift_id)
    if not planned_shift:
        session.pop("planned_id", None)
        return redirect("/plan")

    shift_is_planned = True
    shift_analytics = {}
    planned_start_iso = None
    planned_end_iso = None
    breaks = []
    expected_time = 0
    expected_parts = 0
    total_parts = 0
    total_reject = 0
    # Runtime analytics
    try:
        shift_analytics = calculate_uptime_downtime(planned_shift_id)
    except Exception as analytics_err:
        print(f"[WARN] Analytics error: {analytics_err}")
   
    state = get_current_state()
    clock_running = None
    if state == "cycle_running" or state == "machine_on":
       clock_running = True
    else: 
        clock_running = False


    # checking for the editting if user leaves the stop screen before they should
    unconfirmed_comments = get_unconfirmed_comments(planned_shift_id)
    unconfirmed_reasons = get_unconfirmed_reasons(planned_shift_id)

    if not unconfirmed_reasons:
        unconfirmed_reasons = None
    if not unconfirmed_comments:
        unconfirmed_comments = None

   #grabbing the starved and blocked status plus their times tracked in the db
    is_starved= get_status_starved(planned_shift_id)
    is_blocked = get_status_block(planned_shift_id)
    
    starved_time = get_starved_time(planned_shift_id) # function called in analytics.py
    blocked_time = get_blocked_time(planned_shift_id) # function called in analytics
    print("what is my starvedTime", starved_time)
    
    if shift_analytics:
        expected_time_raw = shift_analytics["planned_runtime"] 
        expected_seconds = parse_hmm_to_seconds(expected_time_raw)
        expected_parts = int(expected_seconds) / cycle_time if cycle_time else 0.0
        
         
    else:
        expected_parts = 0

    # okay this is fine, we can grab the totla_parts here from the db, i have  
    #put the total expteced and rejected parts in the planned_shift table 
    first_parts = grab_first_parts() 
    first_rejects = grab_first_rejects() 
    parts = grab_total_parts()

    rejects = grab_total_rejects() 
    total_parts = parts - first_parts 
    total_rejects = rejects - first_rejects 
    
    
    
    
    total_parts = int(total_parts) if total_parts is not None else 0
    total_reject = int(total_reject) if total_reject is not None else 0
    if total_parts < 0:
        total_parts = 0
    if total_reject < 0:
        total_reject = 0
   
    # Parse breaks
   
    try:
        if planned_shift["planned_start"]:
            start_dt = datetime.fromisoformat(planned_shift["planned_start"])
            end_dt = datetime.fromisoformat(planned_shift["planned_end"])

            if datetime.utcnow() < start_dt:
                return redirect(f"/waiting?planned_start={start_dt}")

            planned_start_iso = start_dt.isoformat()
            planned_end_iso = end_dt.isoformat()

            def append_break(label, start_key, end_key):
                try:
                    start = planned_shift[start_key]
                    end = planned_shift[end_key]
                    if start and end:
                        start_str = start.isoformat() if hasattr(start, "isoformat") else str(start)
                        end_str = end.isoformat() if hasattr(end, "isoformat") else str(end)
                        breaks.append({"label": label, "start": start_str, "end": end_str})
                except Exception as dt_err:
                    print(f"[WARN] Could not parse {label} break: {dt_err}")

            append_break("Break 1", "break1_start", "break1_end")
            append_break("Lunch", "lunch_start", "lunch_end")
            append_break("Break 2", "break2_start", "break2_end")

    except Exception as parse_err:
        print(f"[WARN] Failed to parse shift/break times: {parse_err}")

    cause = None
    if shift_is_planned and not clock_running:
        try:
            print("is this section being activated")
            cause = get_latest_stop_cause(auth_id, planned_shift_id)
        except Exception as cause_err:
            print(f"[WARN] Could not fetch stop cause: {cause_err}")

    oee = MR_oee = performance = quality = 0
    if shift_analytics:
        availability = shift_analytics["OEE"]
        MR_availability = shift_analytics["machine_efficiency"]
        availability = float(shift_analytics.get("OEE", 0.0))
        MR_availability = float(shift_analytics.get("machine_efficiency", 0.0))
    print("availability", availability)
    if total_parts is not None:
            print("expected_parts before oee:", expected_parts, type(expected_parts))
            data = oee_calculation(total_parts, total_reject, expected_parts, availability, MR_availability)
            oee = data["OEE"]
            MR_oee = data["MR_OEE"]
            performance = data["performance"]
            quality = data["quality"]
   
    print("what is my cause", cause)
    shift_analytics["machine_uptime"] = safe_time_string(shift_analytics.get("machine_uptime"))
    shift_analytics["total_runtime"] = safe_time_string(shift_analytics.get("total_runtime"))
    shift_analytics["planned_runtime"] = safe_time_string(shift_analytics.get("planned_runtime"))
    shift_analytics["machine_downtime"] = safe_time_string(shift_analytics.get("machine_downtime"))
    shift_analytics["non_downtime"] = safe_time_string(shift_analytics.get("non_downtime"))
    print("planned_runtime.", shift_analytics["planned_runtime"])
    print("total_runtime" , shift_analytics["total_runtime"])
    print("machne_downtime", shift_analytics["machine_downtime"])
    print("planned_end", planned_end_iso)
    return render_template(
        "index.html",
        planned_shift=planned_shift,
        shift_is_planned=shift_is_planned,
        shift_analytics=shift_analytics,
        clock_running=clock_running,
        shift_blocked=False,
        planned_start=planned_start_iso,
        planned_end=planned_end_iso,
        breaks=breaks,
        reason=cause,
        auth_id=auth_id,
        expected_parts=expected_parts,
        total_parts=parts,
        total_rejects=rejects,
        MR_oee=MR_oee,
        quality=quality,
        oee=oee,
        planned_shift_id=planned_shift_id,
        unconfirmed_reasons = unconfirmed_reasons,
        unconfirmed_comments = unconfirmed_comments,
        is_starved=is_starved,
        is_blocked=is_blocked,
        starved_seconds=starved_time,
        blocked_seconds = blocked_time,
        cycle_time = cycle_time,
    )




def convert_timedelta_to_minutes(tdelta):
    if isinstance(tdelta, str):
        try:
            h, m, s = map(int, tdelta.split(":"))
            tdelta = timedelta(hours=h, minutes=m, seconds=s)
        except ValueError:
            return 0.0  # Fallback for bad strings
    elif not isinstance(tdelta, timedelta):
        return 0.0  # Invalid type fallback

    return tdelta.total_seconds() / 60.0

def oee_calculation(total_parts, total_reject, expected_parts, availability, MR_availability):
    try:
        total_parts = float(total_parts)
    except (ValueError, TypeError):
        print("total_parts failed")
        total_parts = 0

    try:
        total_reject = float(total_reject) if total_reject is not None else 0
    except (ValueError, TypeError):
        print("reject failed")
        total_reject = 0

    try:
        expected_parts = float(expected_parts)
    except (ValueError, TypeError):
        print("expected_parts_failed")
        expected_parts = 0

    try:
        availability = float(availability)
    except (ValueError, TypeError):
        print("availability failed")
        availability = 0.0

    try:
        MR_availability = float(MR_availability)
    except (ValueError, TypeError):
        print("MR failed")
        MR_availability = 0.0

    print("expected_parts =", expected_parts)

    total_actual = total_parts + total_reject
    quality = (total_parts / total_actual) * 100 if total_actual > 0 else 100.0
    performance = (total_parts / expected_parts) * 100 if expected_parts > 0 else 0.0

    MR_OEE = (MR_availability * quality * performance) / 10000
    OEE = (availability * quality * performance) / 10000

    return {
        "OEE": OEE,
        "MR_OEE": MR_OEE,
        "performance": performance,
        "quality": quality
    }


def parse_hmm_to_seconds(hmm_str):
    parts = hmm_str.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        total_seconds = timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()
        return int(total_seconds)
    return 0  # fallback if format is unexpected
def safe_time_string(value):
    if not value or not isinstance(value, str):
        return "00:00:00"
    parts = value.split(":")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return "00:00:00"
    return ":".join(part.zfill(2) for part in parts)

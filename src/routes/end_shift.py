#endshift.py
from flask import Blueprint, render_template, request, redirect, session
from src.db import is_clock_running, get_planned_shift_id,get_latest_planned_shift, get_shift_logs_by_planned_id, insert_final_analytics, delete_planned_shift_by_id, change_shift_completion, set_mock_bit, set_transition_lock, insert_unfinished_shift, pop_unfinished_shift,  get_all_unfinished_shift_ids, get_planned_shift_by_id, get_latest_unfinished_shift,  get_unconfirmed_shift_rows, get_incomplete_data, get_planned_id,  get_end_shift_function,  get_unconfirmed_shift_by_id, insert_reason_and_comment_to_unconfirmed, get_multiple_causes, update_shift_cause_reason_comment
from src.services.analytics import calculate_uptime_downtime, final_analytics
from.route_manager import end_shift
from datetime import datetime, timezone
bp = Blueprint("end_shift", __name__)

#end shift route 
#if unfinished shift 
#   pull and grab each individual data, need shift id, need whats incomplete for the given shift 
#   render the needed reasons during each stop, provide the time for each,
#   the post on this route will be to render an individual shift, so two route shere, on epage showing all the shifts needed entering and one actually entering 
#else
#redirect to clear local and clear the shift blah blah all the completion done in end_shift 
# NOTE! the end_shift function cannot be called unless and yes unless there is no incomplete data or the shift will be mared off twice as unfinished.
@bp.route("/end_shift", methods=["GET", "POST"])
def end_shift_route():
    planned_id = get_planned_id()
    if not planned_id:
        #when incomplete data that means the end_Shift route did its thing and we popped so we go and render the clear local storage route
        return redirect("/clear_local")

    unfinished = get_incomplete_data(planned_id)
    if unfinished:
        if request.method == "POST":
            shift_id = request.form.get("shift_id")
            return redirect(f"/incomplete_data?shift_id={shift_id}")

        shift_rows = get_unconfirmed_shift_rows(planned_id)
        return render_template("end_shift.html", shift_rows=shift_rows)
        
    else:
        end_shift_fn = get_end_shift_function()  # Call the function properly
        if end_shift_fn:
            end_shift()  # This is your internal logic function

        return redirect("/clear_local")
    

@bp.route("/incomplete_data", methods=["GET", "POST"])
def incomplete_data():
    shift_id = request.args.get("shift_id")

    # Get the one unconfirmed log row for this shift
    log = get_unconfirmed_shift_by_id(shift_id)  # correct function name

    if request.method == "POST":
        shift_id = request.form.get("shift_id")
        reason = request.form.get("reason")
        comment = request.form.get("comment") or None
        insert_reason_and_comment_to_unconfirmed(shift_id, reason, comment)
        return redirect("/end_shift")

    # Default flags
    reason_flag = False
    comment_flag = False
    cause_flag = False
        # Guarded check (you say log is guaranteed to exist, but we protect anyway)
    if log:
        if log.get("reason") == "unconfirmed":
            reason_flag = True
        if log.get("comments") == "unconfirmed":
            comment_flag = True
        if log.get("cause") == "unconfirmed":
            cause_flag = True
    if cause_flag:
        return redirect(f"incomplete_cause?shift_id={shift_id}")
    return render_template(
        "incomplete_shift.html",
        reason_flag=reason_flag,
        comment_flag=comment_flag,
        cause_flag=cause_flag,
        shift_id=shift_id
    )
    
@bp.route("/incomplete_cause", methods = ["GET", "POST"])
def record_multiple_causes():
    auth_id = 1
    planned_id = get_planned_id() 
    if request.method == "POST":
        shift_id = request.form.get("shift_id")
        cause = request.form.get("cause")
        reason = request.form.get("reason")
        comment = request.form.get("comment") 
        if not comment:
            comment = None
        update_shift_cause_reason_comment(shift_id, cause, reason, comment)
        return redirect("/end_shift")
        
    shift_id = request.args.get("shift_id") 
    print("shift_id" ,shift_id) 
    multiple_causes = []
    multiple_causes = get_multiple_causes(shift_id) #grabbing the multiple causes from the db
    if not multiple_causes:
        causes = [ "fence_fault",
    "missed_pick",
    "missed_placement",
    "quality_stop",
    "collision",
    "sensor_audit_flag",
    "operator_stop",
    "e_stop",
    "other" ]
    else:
        causes = multiple_causes.split(",")
    return render_template("record_multiple_causes.html",causes=causes, shift_id =shift_id, block_back_button = True )
       

@bp.route("/clear_local")
def clear_local():
    

    return render_template("clear_local.html", clear_shift_storage=True, auth_id=session["auth_id"])

@bp.route("/change_bit", methods = ["GET", "POST"])
def change_bit():
    auth_id = session.get("auth_id")
    if not auth_id:
        return redirect ("/login")
    
    if request.method == "POST":
        value = request.form.get("bit_value")
        value = int(value)
        return_value = value
        if value == 1:
            return_value = True
        else:
            return_value = False
        print("am i ever rendering")
        set_mock_bit(auth_id, return_value)
        return redirect("/")
    return render_template("mock_bit.html", block_back_button = True)

#the finish shift button on home screen renders here, grabs all unfinsihed shiftd adn displays 
#to the screen

#this route is rendered from above, it leads to the total parts and total rejects screen that the user 
# directed out of for an unfinished shift

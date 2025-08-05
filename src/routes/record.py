from flask import Blueprint, render_template, request, redirect, session
from src.services.time_utils import get_current_html_time 

from src.db import (
    get_planned_shift_id,
    insert_shift_start,
    get_latest_unstopped_shift_id,
    update_shift_stop,
    is_clock_running,
    get_latest_stop_time,
    get_latest_start,
   get_multiple_causes, 
    get_active_shift,
    get_latest_shift_by_auth_and_planned,
    get_planned_id,
    get_latest_unconfirmed_data,
     get_latest_unconfirmed_data,
     insert_reason_and_comment_to_unconfirmed, 
     get_last_stop_cause,
     get_runtime_shift_id,
     clear_runtime_shift_id,
      update_shift_cause_reason_comment
)
from dateutil import parser
from datetime import timezone, datetime
from zoneinfo import ZoneInfo

bp = Blueprint("record", __name__)
# this is not being used anymore, can clean this out when confirmed 



    # should be good on the route
    #record stop route, rendered during stops no matter what 
    # needs to check if unconfirmed data exists,
    #needs the shift id for this
    # store shift id in the db or grab from the route directly 
    # this first code abslutely sucks 
@bp.route("/record_stop", methods=["GET", "POST"])
def record_stop():   
   planned_id = get_planned_id()
   if not planned_id:
       return redirect("/login")
   auth_id = 1;
   shift_id = get_runtime_shift_id(auth_id)
   cause = get_last_stop_cause(shift_id) 
   clear_runtime_shift_id(auth_id)
   print("what is my cause statement", cause)
   #safe to do this, cause wont be none unless multiple causes exist 
   if cause == "unconfirmed": 
       print("so we get here")
       return redirect(f"/record_multiple_causes?shift_id={shift_id}")
   
   
   if request.method == "POST":
       reason = request.form.get("reason")
       comment = request.form.get("comment")
       shift_id = request.form.get("shift_id")
       if not comment:
           comment = None
    
       insert_reason_and_comment_to_unconfirmed(shift_id, reason, comment)  # this is good #insert the stops cayses reaons 
       return redirect("/record_stop_success")

   reason_flag, comment_flag = get_latest_unconfirmed_data(shift_id) # returns boolean, for if needed reason or comment 
   print("reason flag", reason_flag) 
   print("comment_flag", comment_flag)
   
   if not reason_flag and not comment_flag:
       
       return redirect("/record_stop_success")

  
   cause = get_last_stop_cause(shift_id) 
   return render_template("record_stop.html",
                       reason_flag=reason_flag,
                       comment_flag=comment_flag,
                       shift_id=shift_id,
                       cause=cause,
                       block_back_button = True)
   

@bp.route("/record_multiple_causes", methods = ["GET", "POST"])
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
        return redirect("/record_stop_success")
        
    shift_id = request.args.get("shift_id") 
    print("shift_id" ,shift_id) 
    multiple_causes = get_multiple_causes(shift_id) #grabbing the multiple causes from the db
    
    causes = multiple_causes.split(",")
    return render_template("record_multiple_causes.html",causes=causes, shift_id =shift_id, block_back_button = True )
    
    
    
@bp.route("/record_start_success") # we good here 
def record_start_success():
    auth_id = session.get("auth_id")
    planned_id = get_planned_id()

    if not auth_id or not planned_id:
        return redirect("/")


    shift_id = get_latest_shift_by_auth_and_planned(auth_id, planned_id)
    return render_template("record_start_success.html", shift_id=shift_id)


@bp.route("/record_stop_success")
def record_stop_success():
    
    return render_template("record_stop_success.html")


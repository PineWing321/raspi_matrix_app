
from tkinter import SW
from flask import redirect, render_template 
from src.db import set_next_transition, set_next_transition_and_message,set_transition_lock, get_latest_stop_reason , set_message, insert_shift_start, get_planned_id,  change_end_shift_function, grab_total_parts_and_reject_parts, set_end_shift_reason,insert_final_analytics, change_shift_completion, clear_planned_id, get_stop_cause_label, update_shift_stop,  get_latest_unstopped_shift_id, insert_comment_needed, insert_cause_for_shift, insert_unfinished_shift, get_incomplete_data, update_unfinished_parts,  get_unfinished_parts,  get_latest_unfinished_shift,  get_last_shift_row_by_planned_id, pop_unfinished_shift, shift_start_already_exists, update_runtime_state_shift_id, insert_stop_unconfirmed, set_first_parts_and_rejects,  pop_first_parts_and_rejects, grab_first_rejects, grab_first_parts, get_total_parts, get_total_rejects
from dateutil import parser
from datetime import timezone, datetime
from zoneinfo import ZoneInfo
from src.services.analytics import final_analytics 
from src.plc import get_stop_cause
from threading import Event
from src.globals import render_ack_event, grab_total_parts, grab_total_rejects
#0 = idle
#1 = cycle on with no shift planned
#2 = waiting for cycle to start and planned window 
#3= machine is off but within shift window
#4 =  cycle is on and planned shift hasnt ended but outside shift window
#5 = all are running 

def adjust_real_parts(parts): # helper functions for end of shift 
    start_parts = grab_first_parts()
    total = parts - start_parts
    if total < 0:
        return None 
    return total
    
    
def adjust_real_rejects(rejects):  # helper functions for end of shift 
    start_rejects = grab_first_rejects()
    total = rejects - start_rejects 
    if total < 0:
        return None
    return total
    
    
    
    
def render_route(new_state, old_state):
    """Handles all meaningful state transitions and side-effects.
    - Only called when background thread detects a change in `overall_state`
    - Responsible for updating message, calling record endpoints, and ending shift.
    """
 
    print(f"[STATE CHANGE] {old_state} → {new_state}")

    if new_state == "finalizing":
        print("so now im curious") 
        end_shift()
        set_next_transition_and_message("/end_shift", "Shift time is over. Finalizing shift...")
        return

    elif old_state == "machine_on" and new_state == "machine_off":
        print("am i being it blutiple time?")
        auto_record_stop()
        set_next_transition_and_message("/record_stop", "Machine stopped during active shift.")
        return

    elif old_state == "idle" and new_state == "waiting":
        set_next_transition_and_message("/", "Shift planned. Waiting for shift window.")
        return

    elif old_state in ("idle", "waiting") and new_state == "cycle_running":
        set_next_transition_and_message("/", "Cycle started before shift window. Adjust start time or stop machine.")
        return

    elif old_state in ("idle", "waiting") and new_state in ("machine_off"):
        parts = grab_total_parts()  # updated
        reject = grab_total_rejects()  # updated
        print("is the route manager being hit") 
        pop_first_parts_and_rejects()
        set_first_parts_and_rejects(parts, reject)
        set_next_transition_and_message("/", "Shift window began. Start machine cycle.")
        return

    elif old_state == "cycle_running" and new_state in ("machine_on"):
        print("dont tell me i was hit too")
        record_start()
        parts = grab_total_parts()  # updated
        reject = grab_total_rejects()  # updated
        pop_first_parts_and_rejects()
        set_first_parts_and_rejects(parts, reject)
        set_next_transition_and_message("/", "Shift started while machine was already cycling.")
        return

    elif old_state == "plan_shift" and new_state == "waiting":
        set_next_transition_and_message("/", "Shift planned. Awaiting shift window.")
        return

    elif new_state == "plan_shift" and old_state == "machine_on":
        set_next_transition_and_message("/", "Cycle running with no shift planned. Please plan a shift.")
        return

    elif new_state == "machine_on" and old_state == "finalizing":
        parts = grab_total_parts()  # updated
        reject = grab_total_rejects()  # updated
        pop_first_parts_and_rejects()
        set_first_parts_and_rejects(parts, reject)
        record_start()
        set_next_transition_and_message("/", "shift started back to back recording start")
        return

    elif new_state == "machine_off" and old_state == "finalizing":
        parts = grab_total_parts()  # updated
        reject = grab_total_rejects()  # updated
        pop_first_parts_and_rejects()
        set_first_parts_and_rejects(parts, reject)
        set_next_transition_and_message("/", "shift started, turn on machine")
        return 

    elif new_state == "plan_shift" and old_state == "finalizing":
        set_next_transition_and_message("/", "shift ended, but cycle still on")
        return 

    elif new_state == "idle" and old_state == "finalizing":
        set_next_transition_and_message("/", "shift ended")
        return 

    elif new_state == "machine_on" and old_state == "plan_shift":
        record_start()
        parts = grab_total_parts()  # updated
        reject = grab_total_rejects()  # updated
        pop_first_parts_and_rejects()
        print("what is parts", parts)
        print("what is rejects", reject)
        print("is this being hit") 
        set_first_parts_and_rejects(parts, reject)
        set_next_transition_and_message("/index", "shift started")
        return 

    elif new_state == "machine_off" and old_state == "plan_shift":
        parts = grab_total_parts()  # updated
        reject = grab_total_rejects()  # updated
        pop_first_parts_and_rejects()
        set_first_parts_and_rejects(parts, reject)
        set_next_transition_and_message("/index", "shift started")

    elif new_state == "machine_on" and old_state != "machine_on":
        print("idk how this could happen")
        record_start()
        set_next_transition_and_message("/record_start_success", "Machine started.")
        return

    elif new_state == "idle":
        set_next_transition_and_message("/", "System is idle.")
        return

    #this route, sets cause and reason as unconfirmed,
    #once the cause is grabbed it will no longer be unconfirmed,
    #the two cases where the reason needs user input the db will have reason as unconfirmed,
    #the one case a comment is needed will mark comment has unconfirmed, 
    #this is how the incomplete data will travel throughout the app
def render_starved_blocked(starved_or_blocked):
    render_ack_event.clear()  # Pause main loop until frontend confirms

    if starved_or_blocked == "starved":
        msg = "Machine is Starved"
        set_next_transition_and_message("/index", msg)
    elif starved_or_blocked == "blocked":
        msg = "Machine is Blocked"
        set_next_transition_and_message("/index", msg)
    else:
        raise ValueError("Invalid argument: must be 'starved' or 'blocked'")
        return 
    # Wait until frontend acknowledges transition (via /api/acknowledge_transition)
    print(f"[render_starved_blocked] Waiting for frontend to acknowledge: {msg}")
    render_ack_event.wait(timeout=5)  # You can adjust timeout as needed

    print(f"[render_starved_blocked] Transition acknowledged by frontend.")
    return

def render_end_starved_blocked(starved_or_blocked):
    render_ack_event.clear()  # Pause main loop until frontend confirms

    if starved_or_blocked == "starved":
        msg = "Machine is No Longer Starved"
        set_next_transition_and_message("/index", msg)
    elif starved_or_blocked == "blocked":
        msg = "Machine is No Longer Blocked"
        set_next_transition_and_message("/index", msg)
    else:
        raise ValueError("Invalid argument: must be 'starved' or 'blocked'")
        return

    print(f"[render_end_starved_blocked] Waiting for frontend to acknowledge: {msg}")
    render_ack_event.wait(timeout=5)

    print(f"[render_end_starved_blocked] Transition acknowledged by frontend.")
    return

    
    
    
    
    
    
    
    
    
def auto_record_stop():
    planned_id = get_planned_id()
    print("ine 82", planned_id)
    insert_stop_unconfirmed(1,planned_id) # auto inserts reason and cause as uncofnirmed in db and stop time
   
    shift_id = get_latest_unstopped_shift_id(1, planned_id) # this needs to grab the newest shift_id when reason and cause are unconfirmed, 
    print("this is the shift_id", shift_id)
    auth_id = 1
    update_runtime_state_shift_id(auth_id, shift_id)
    print("what about past this line 101")
    id = 1
    
    
    reason = "unconfirmed"
    multiple_causes = None
    cause = get_stop_cause()  # Can return a string or list
    need_comment = False

    print("what is cause returning", cause)

# Handle list of causes
    if isinstance(cause, list) and len(cause) > 1:

        multiple_causes = ",".join(cause)
        cause = "unconfirmed"

# Handle single-cause in list
    elif isinstance(cause, list) and len(cause) == 1:
        cause = cause[0]

# Now handle special logic
#these causes were determined to need comments to explain them 
    if cause == "other":
        need_comment = True
    elif cause == "quality_stop":
        need_comment = True
    
    print("do we get past the elif block")
    insert_cause_for_shift(shift_id, 1, cause)

    if need_comment:
        insert_comment_needed(shift_id, 1)
        return
    else:
        print("dont tell em")
        update_shift_stop(
        shift_id=shift_id,
        auth_id=1,
        stop_time=datetime.now(timezone.utc).isoformat(),
        reason=reason,
        cause=cause,
        comments=None,
        multiple_causes=multiple_causes
        )
        return



def record_start():
    auth_id = 1
    planned_id = get_planned_id()
    start_already = shift_start_already_exists(planned_id)
    if start_already:
        print("it is being hit twice")
        return 
    if not planned_id:
        print("❌ No planned shift to start")
        return

    try:
        now_utc = datetime.now(timezone.utc).isoformat()
        insert_shift_start(auth_id, now_utc, planned_id)

        print(f"✅ Shift started at {now_utc} for planned_id {planned_id}")
        

    except Exception as e:
        print(f"[ERROR] Failed to start shift: {e}")
        

    except Exception as e:
        print(f"[ERROR] Failed to start shift: {e}")
        
        

     #rethink this end_shift code 
     #lets build this as cleanly modular and simple as possible, 
     #seperate into clock_state conditions?
     #cannot end the shift with incomplete data [call the incmplete data function, if its exists render the incomplete shift route completely]
     # we have to mark the change_end_shift condition to be true, this will define the state [call the chnage end shift function]
     #this is the bottle neck, sort that out first to filter,  [else clause and such]
     #if its incomplete render page and set condition state and app wide

     #once data is complete and fully collected sort by clock state [grab clcok state function if else]
     #if the clock_state is on than we can enter the final stop have it be the shift ending and add to final analytics accordingly  [pass in the clock state to compute final analytics function, also insert the final stop as end shift to the shift table]

     #if its off pass the end shift now time  and use the planned end to calculate the shift. [use the planned end and grab last reason to calculate final analytics]

     # finish cleaning up shift, once everything is done and cleaned up we can mark the end_shif functionality as done. [ clean up]

     # what are the functions needed for each, 

def end_shift():
   
 #0 or 1, if 1 the program assumes that we are in the middle of ending a shift
   
   planned_id = get_planned_id()
   if not planned_id:
      print("there is absolutely no way") 
      return
   change_end_shift_function(True) 
   incomplete_data = get_incomplete_data(planned_id) #grabbing the incomplete data DO THIS!!!!
    # this has to work! we can only pop this here, this is the key no where else can a planned_id be popped but at the end of this function 

   inserted = get_latest_unfinished_shift() #check if its already inserted and we are revisiting 
   if not inserted: # if its not we can insert 
     
     insert_unfinished_shift(planned_id) #here is the unfinished shift. 
   print("do we get here")
   is_parts_in = get_unfinished_parts(inserted) #check if we already have them in storage db 
   if not is_parts_in:
     parts = grab_total_parts()
     rejects = grab_total_rejects()
     parts = adjust_real_parts(parts)
     rejects = adjust_real_rejects(rejects) 
     update_unfinished_parts(planned_id, parts, rejects)
     print("is it the update_unifnished_parts")
   else: 
       
       parts = is_parts_in["total_parts"]
       rejects = is_parts_in["rejected_parts"]
   print("not in the parts block")
   auth_id = 1
   if incomplete_data:  #cannot end a shift if incomplete data exists 
       return

   else:
       last_row = get_last_shift_row_by_planned_id(planned_id) # grabs if the cycle is running or not 
       if not last_row:
           #no shift at all so that is fine 
           change_shift_completion(planned_id)
           clear_planned_id()
           change_end_shift_function(False) #everything done is needed 
           pop_unfinished_shift(planned_id)
           return 0
       if last_row["stop_time"] == None:  #if the machine is on we have to insert the final stop 
           set_end_shift_reason(planned_id, auth_id)#this function sets the reason as an end_shift, final_analytics function will be built for it now
           cycle_status = True
       else:
           cycle_status = False
       
       final_analytics_value = final_analytics(cycle_status,planned_id, parts, rejects) #fix this function, 
       print("pls tell me what planned end is", final_analytics_value["planned_end"])
   
       #at this point, we have the final anlytics, theres no icomplete data, all the info is needed, now we can store and pop 
       if final_analytics_value:
         print("and what about here")
         insert_final_analytics(final_analytics_value)
         change_shift_completion(planned_id)# we can now mark the shift ad definitely over
     
       clear_planned_id() # we have successfully popped
       value = False
       
       change_end_shift_function(value) #everything done is needed 
      
       pop_unfinished_shift(planned_id)
     
       pop_first_parts_and_rejects()
       return 0 # return 0 to show we can resume
     
    
    
    
    
    
    
  # get_incomplete_data() what to do for this frunction 
  #- db function? grab the rows, or grab the shift_ids, or just be true or false, 
  # i say true or false in the end_shift button 
  #if true than we can render that route, what would happen, 
  # incompelte data when ending a shift? App freezes, the interval stops, all pages stop, entire app blares and tells, buttons show up, new tab too just make sure to render in db

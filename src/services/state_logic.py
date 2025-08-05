from src.db import get_bit_from_mock_tags, get_active_planned_shift, get_timezone, get_current_state, update_runtime_state, set_planned_id, clear_planned_id, get_planned_id,  get_end_shift_function, update_total_parts, update_total_rejects, grab_first_rejects, grab_first_parts,  change_end_shift_function, insert_start_starved, insert_start_block, insert_stop_starved, insert_stop_block, get_status_starved, get_status_block
from datetime import datetime, timezone
from dateutil import parser 
from src.routes.route_manager import render_route, render_starved_blocked,render_end_starved_blocked
from src.plc import get_live_shift_data,  get_stop_cause
from zoneinfo import ZoneInfo
import time 
import os
from threading import Event
from src.globals import update_current_parts_and_rejects
render_lock = Event()
render_lock.set() 

current_state = get_current_state()
def app_state():
    interval = 1
    auth_id = 1
    global current_state

    while True:
        block = get_end_shift_function()
        render_lock.wait()
        if block:
            continue

        try:
            shift_status = get_shift_status()
            data = get_live_shift_data()
            cycle_status = data["cycle_status"]
            parts = data["total_parts"]
            rejects = data["total_rejects"]
            update_current_parts_and_rejects(parts, rejects) 
            starved = data["starved"]
            blocked = data["blocked"]
            planned_id = get_planned_id()
            now = datetime.utcnow().isoformat()
            print("blocked", blocked)
            print("starved", starved)
            block = get_status_block(planned_id)
            strv = get_status_starved(planned_id)
            print("what is my starved db", strv)
            print("what is my blocked db" , block) 
            if cycle_status:
                if planned_id:
                    if starved:
                        if not get_status_starved(planned_id):
                            try:
                                insert_start_starved(planned_id, now)
                            except Exception as e:
                                print(f"[DB ERROR] insert_start_starved failed: {e}")
                            print("→ Starved started at", now)
                            render_lock.clear()
                            render_starved_blocked("starved")
                            render_lock.set()
                    else:
                        if get_status_starved(planned_id):
                            try:
                                insert_stop_starved(planned_id, now)
                            except Exception as e:
                                print(f"[DB ERROR] insert_stop_starved failed: {e}")
                            render_lock.clear()
                            render_end_starved_blocked("starved")
                            render_lock.set()
                            print("→ Starved stopped at", now)
                        else:
                            print("what is this")
                else:
                    print("nothing")
                if planned_id:
                    if blocked:
                        if not get_status_block(planned_id):
                            try:
                                insert_start_block(planned_id, now)
                            except Exception as e:
                                print(f"[DB ERROR] insert_start_block failed: {e}")
                            print("→ Block started at", now)
                            render_lock.clear()
                            render_starved_blocked("blocked")
                            render_lock.set()
                    else:
                        if get_status_block(planned_id):
                            print("and what is this")
                            try:
                                insert_stop_block(planned_id, now)
                            except Exception as e:
                                print(f"[DB ERROR] insert_stop_block failed: {e}")
                            render_lock.clear()
                            render_end_starved_blocked("blocked")
                            render_lock.set()
                            print("→ Block stopped at", now)
                else:
                    print("nothing")
        

            elif planned_id:
                if get_status_block(planned_id):
                    print("running")
                    try:
                        insert_stop_block(planned_id, now)
                    except Exception as e:
                        print(f"[DB ERROR] insert_stop_block failed: {e}")
                if get_status_starved(planned_id):
                    try:
                        insert_stop_starved(planned_id, now)
                    except Exception as e:
                        print(f"[DB ERROR] insert_stop_starved failed: {e}")
            else:
                print("continue")

            if shift_status == "No Shift Planned":
                new_state = "plan_shift" if cycle_status else "idle"
            elif shift_status == "Before Shift":
                new_state = "cycle_running" if cycle_status else "waiting"
            elif shift_status == "Shift Running":
                new_state = "machine_on" if cycle_status else "machine_off"
            elif shift_status == "Shift End":
                new_state = "finalizing"
            else:
                new_state = "idle"

            if new_state != current_state:
                update_runtime_state(
                    auth_id=auth_id,
                    overall_state=new_state,
                    clock_state=cycle_status,
                    shift_state=shift_status
                )
                temp = current_state
                current_state = new_state
                render_route(new_state, temp)

            time.sleep(interval)

        except Exception as e:
            print(f"[ERROR] app_state loop: {e}")
            time.sleep(interval)




def get_shift_status():
    planned_shift = get_active_planned_shift()
    if not planned_shift:
        clear_planned_id()  # Clean it if no shift found
        return "No Shift Planned"

    # Timezone setup
    tz_str = get_timezone()
    tz = ZoneInfo(tz_str)
    utc_now = datetime.now(timezone.utc)

    try:
     planned_start = parser.isoparse(planned_shift["planned_start"])
     planned_end = parser.isoparse(planned_shift["planned_end"])

     if planned_start.tzinfo is None:
      planned_start = planned_start.replace(tzinfo=timezone.utc)
     else:
      planned_start = planned_start.astimezone(timezone.utc)
 
     if planned_end.tzinfo is None:
        planned_end = planned_end.replace(tzinfo=timezone.utc)
     else:
      planned_end = planned_end.astimezone(timezone.utc)


    except:
     clear_planned_id()
     return "No Shift Planned"

    planned_id = get_planned_id()

    if utc_now < planned_start:
        if planned_id:
            clear_planned_id()
        return "Before Shift"

    elif planned_start <= utc_now <= planned_end:
        if not planned_id:
            print("wjat is hte planned oid", planned_shift["id"])
            set_planned_id(planned_shift["id"])
        return "Shift Running"

    else:  # utc_now > planned_end
        
            
        return "Shift End"

def get_is_shift_planned():  # is there a shift planned
 
    planned_shift = get_active_planned_shift() 
    
    if not planned_shift:
        print("so whats happenning")
        return False, 0
    else:
        return True, planned_shift["id"]
        
def adjust_real_parts(parts):
    start_parts = grab_first_parts()
    total = parts - start_parts
    if total < 0:
        return None 
    return total
    
    
def adjust_real_rejects(rejects): 
    start_rejects = grab_first_rejects()
    total = rejects - start_rejects
    if total < 0:
        return None
    return total
    
    


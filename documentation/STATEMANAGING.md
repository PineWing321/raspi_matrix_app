Perfect—here’s the first half of your STATE_MANAGING.md written straight from that code. Clean, spaced, caps headers, no fluff.

STATE MANAGEMENT — OVERVIEW (PART 1)
FILE OF RECORD: src/services/STATE_LOGIC.py
LOOP: app_state() runs every 1s (cadence = 1 Hz)
PRIMARY EFFECTS:

Poll PLC → derive state → persist (update_runtime_state)

Render UI routes on state change (render_route)

Manage STARVED/BLOCKED sub-flows with DB logs + renders

THE SEVEN APP STATES (TOP-LEVEL)
These are the only values written to overall_state via update_runtime_state() and passed into render_route(new_state, prev_state):

IDLE

No shift planned and machine not cycling.

Set when shift_status == "No Shift Planned" and cycle_status == False.

PLAN_SHIFT

No shift planned but machine is cycling (edge case).

Set when shift_status == "No Shift Planned" and cycle_status == True.

WAITING

Shift exists but hasn’t started yet; machine not cycling.

Set when shift_status == "Before Shift" and cycle_status == False.

CYCLE_RUNNING

Shift hasn’t started (still “Before Shift”), but PLC reports cycling.

Set when shift_status == "Before Shift" and cycle_status == True.

MACHINE_ON

Shift is running and machine is cycling.

Set when shift_status == "Shift Running" and cycle_status == True.

MACHINE_OFF

Shift is running but machine is not cycling.

Set when shift_status == "Shift Running" and cycle_status == False.

FINALIZING

Shift has ended (past planned_end).

Set when shift_status == "Shift End" (ignores cycle_status).

Fallback: any unexpected shift_status maps to IDLE.

HOW WE INTERPRET PLC SIGNALS
SOURCE: get_live_shift_data() (from src/plc.py)
Fields used here:

cycle_status → bool; machine cycling (True) vs not (False)

total_parts / total_rejects → cumulative counters

starved → bool; machine starved signal

blocked → bool; machine blocked signal

Immediate side-effects on every loop:

update_current_parts_and_rejects(parts, rejects) writes the latest counters into globals for cheap UI reads.

If a planned shift is active (planned_id exists), we track STARVED/BLOCKED episodes:

When cycle_status == True:

STARVED start: if starved is True and DB says not currently starved → insert_start_starved(planned_id, now) + render_starved_blocked("starved").

STARVED stop: if starved is False and DB says currently starved → insert_stop_starved(planned_id, now) + render_end_starved_blocked("starved").

BLOCKED start: same pattern via insert_start_block(...) + render_starved_blocked("blocked").

BLOCKED stop: same pattern via insert_stop_block(...) + render_end_starved_blocked("blocked").

When cycle_status == False:

If DB shows starved/blocked “on”, force-close them: insert_stop_* (no render of the “start” UI).

Important:

Starved/blocked transitions are only logged/rendered when there’s an active planned_id.

All inserts are wrapped in try/except with console error logging to prevent crashing the main loop.

HOW WE DERIVE SHIFT STATUS (INDEPENDENT OF PLC)
Helper: get_shift_status()
DB Call: get_active_planned_shift() returns the upcoming/ongoing plan (or None).
TZ Handling:

We read tz = ZoneInfo(get_timezone()) (e.g., America/Chicago) but normalize planned_start/planned_end to UTC before comparison.

utc_now = datetime.now(timezone.utc).

Outputs:

"No Shift Planned" → no active planned shift (clears planned_id).

"Before Shift" → now < planned_start (clears planned_id if it exists).

"Shift Running" → planned_start ≤ now ≤ planned_end (sets planned_id if it wasn’t set).

"Shift End" → now > planned_end.

If planned timestamps can’t be parsed → clear planned_id and return "No Shift Planned".

STATE DERIVATION PIPELINE (WHAT RUNS EACH TICK)
Guard rails

If get_end_shift_function() returns truthy, we pause route rendering and loop work until end-shift flow clears it.

render_lock (a threading.Event) is used to serialize renders:

Before rendering starved/blocked UIs, we render_lock.clear(), render, then render_lock.set().

Read PLC + DB

data = get_live_shift_data() → cycle/parts/rejects/starved/blocked.

Update globals with parts/rejects.

Fetch planned_id to decide if starved/blocked logs should be updated.

Manage STARVED/BLOCKED (if planned_id)

Insert start/stop rows in DB based on signal edges and cycle_status.

Call the appropriate render for start/stop of these sub-states.

Compute shift_status

Call get_shift_status() → "No Shift Planned" | "Before Shift" | "Shift Running" | "Shift End".

Map to the 7 app states

bash
Copy
Edit
if "No Shift Planned":    new_state = "plan_shift" if cycle_status else "idle"
elif "Before Shift":      new_state = "cycle_running" if cycle_status else "waiting"
elif "Shift Running":     new_state = "machine_on"   if cycle_status else "machine_off"
elif "Shift End":         new_state = "finalizing"
else:                     new_state = "idle"
Persist + Render on change only

If new_state != current_state:

update_runtime_state(auth_id, overall_state=new_state, clock_state=cycle_status, shift_state=shift_status)

render_route(new_state, previous_state)

Update current_state = new_state

Sleep

time.sleep(1) and repeat.

WHEN WE RENDER route_manager (AND FRIENDS)
render_route(new_state, prev_state)
Triggered only when the top-level state changes (see mapping above). This is your primary “screen/navigation” router for:

Entering planning mode, waiting room, live running screens, machine off UI, finalizing/end flow, etc.

render_starved_blocked(kind)
Triggered immediately when a STARVED or BLOCKED episode starts during an active, cycling shift.

Serialized by render_lock to avoid overlapping renders.

render_end_starved_blocked(kind)
Triggered immediately when a STARVED or BLOCKED episode ends (either signal goes false while cycling, or cycle stops and we force-close).

End-shift block (get_end_shift_function())
When truthy, the loop continues but skips rendering until the end-shift UI/flow completes. This prevents race conditions during finalization.

NOTES & INVARIANTS (THIS CODE ASSUMES…)
planned_id is the gate for writing starved/blocked logs. No planned shift → no starved/blocked logging.

All timestamps inserted for starved/blocked use UTC ISO strings (datetime.utcnow().isoformat()).

DB truth dominates. UI ticking is visual only.

The top-level state changes are edge-triggered (we render only when new_state != current_state).

Starved/blocked start/stop are edge-triggered against DB “currently active” flags (get_status_starved, get_status_block).


PART 2:

To recap, a key conceptual point is that the app state is determined by external triggers (PLC signals), and internal triggers (user action determining shift)
-state is both determined outside the realm of the app and internal

-The transitions that are triggered based on the state changes are key so that the app reperesents the truth (stops, starts, end of shifts) 

ROUTE_MANAGER.py:

vital part of the app, has all of the key transitions

-to quickly explain the auto transitions, app_state registers a state change and calls render_route

-depending on the previous and current state, the next transition is set in the database and whatever function needed is called 

-the frontend has its own interval found in base.html for the jinja/flask side, and the react side has its own

-this interval is polling the api next_transition in api.py which gets the next transition

-from there all of the data is in place, and the front end simply renders the given page and shows the message 

-this is not a deterministic engine, but it is effective and will always trigger a transition when the new state is different than the current 
















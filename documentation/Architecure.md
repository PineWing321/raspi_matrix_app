MAIN FOLDER DIRECTORY 

Shift_manager_front_end
-------contains react side of app, shift_manager and history 
	dist
	node_modules
	src
        -----contains source code for the react side
	     pages
	     ------contains most of the code 
		   history 
		    ---contains code for history page 
                              (SEE BELOW FOR MORE DETAILS)
		   EditShift.jsx
		   HistoryDayView.css
	           PlanShift.jsx
	           ViewShifts.jsx
	     hooks
		  UseTransitionPoller.js 
		  
	     assets		

src
-------contains source code for flask side of app (SEE BELOW FOR DETAILS ON SRC)
      
      services
      routes
      static
      templates
      db.py
      plc.py
      globals.py
	
app.py

requirements.txt

matrixapp_v2.db

EXPLANATIONs 

src/ 
-this is regarding the source code for the Flask side of the app

important pages found within SRC
PLC.py
-the plc reading logic is found in here
-the page contains a few seperate functiosn that get information about the system from the plc
(FOR MORE INFO, SEE PLC_READING.md) 


DB.py
-Has all of the sqlite3 database query's
NOTE: some functions may not be in use, it is nota priority to clean them up, use the search bar to search for ones needed

(FOR MORE INFO SEE DATABASE.md) 

GLOBALS.py
-has some global data stored that is used to quickly and cheaply share variables across the architecture 




src/routes
	-this folder handles the flask routes connection the html templates together. Each route page is declared as a blueprint 
	in app.py, each route is bottlenecked by auth_id (which is set as 1 for now)
	KEY FEATURES
	-the routes in each folders are what load the templates up with variables, and allow for navigation between screens
	-these routes utilize a variety of db functions to get their data 
	-some routes pass data between eachother through the url 
Shift Tracking System — Architecture (Gist)

Purpose: Quick map for new devs. High-level only. When you need details, see the linked docs.

Deep dives: API.md, DATABASE.md, STATE_MANAGING.md, PLC_READING.md

1) What this app is

A state-driven shift tracking system with a Flask backend (PLC polling, state machine, analytics, APIs) and a React frontend (Shift Manager + History).

Key truth: The database is source of truth. Any ticking you see in templates is UI-only for live feedback.

PLC → Flask services (plc.py, STATE_LOGIC) → ROUTE_MANAGER → routes/APIs →
  ├─ Jinja templates (live shift UI w/ ticking)
  └─ React front end (Shift Manager, History) via /api/*
DB (SQLite now; Postgres later) is the ground truth.

2) Repo layout (why each folder exists)

app.py — boots Flask, registers Blueprints, wires globals, enables background state thread.

src/ — Flask backend

routes/ — Blueprints that render templates and expose APIs

api.py — analytics/history APIs consumed by React (see API.md)

plan.py — routes for planning/current-shift screens + some Shift Manager APIs

ROUTE_MANAGER.py — reacts to state swaps (render end/start/stop flows)

services/ — app logic

STATE_LOGIC.py — 1 Hz background loop; compares prev/current state and triggers actions

analytics.py — during-shift + final analytics math (see API.md / DATABASE.md)

templates/ — Jinja pages

base.html — global layout + UI ticking loop (never writes DB)

index.html — current shift view

db.py — all SQLite access. Invariant: scope queries by auth_id. (see DATABASE.md)

plc.py — PLC reads; contract for bits/tags (see PLC_READING.md)

globals.py — small shared values

Shift_manager_front_end/ — React front end

src/pages/ — PlanShift.jsx, EditShift.jsx, ViewShifts.jsx, history/*

src/hooks/ — UseTransitionPoller.js (polls transitions/state as needed)

3) Runtime data flow (bird’s-eye)

Polling (backend): STATE_LOGIC.app_state() runs every second:

Pulls bits from plc.py (Running, parts, rejects, starved, blocked, Event Bit Array (EBA), etc.)

Derives current state; compares to previous state.

On change → call ROUTE_MANAGER.route_manager() to handle side effects (log, route transitions, end/start flows).

Persistence: Events, stops, shift logs → db.py (UTC timestamps).

Live UI: Jinja templates render current shift; base.html ticking animates timers client-side.

History/Analytics (frontend): React queries /api/* to render day/range analytics and causes.

4) State machine (what we track)

States: Running, Stopped, Starved, Blocked, Other (derived via EBA and signals).

Inputs: Running bit, Auto/Ready, EBA (9 classified causes), parts/rejects counts, starved, blocked.

Transitions:

Running → Stopped: snapshot EBA; if none set ⇒ cause = Other. Log event.

Stopped → Running: resume; log restart.

While Running: starved/blocked signals tracked (UI warns; durations logged).

Cadence: 1 Hz loop. On each swap, ROUTE_MANAGER decides which route to render or which DB actions to take.

More: see STATE_MANAGING.md.

5) Analytics (what we compute)

During shift: rolling total_runtime, machine_uptime, machine_downtime, non_downtime, planned_runtime.

Final: same plus OEE components (availability, performance, quality), and composite oee.

Engaged runtime (V1+): dynamic planned time accounting for planned stops/breaks.

Formulas and exact API payloads in API.md.

6) Time & timezone rules (read this twice)

DB stores UTC. Convert at API edges.

User TZ = America/Chicago.

Anchored window rule (History filters): given date range (e.g., Aug 1–7) and time window (e.g., 17:00–06:00), anchor each day from start date to day before end; each window spans into the next calendar day. Include only shifts fully contained within their day’s anchored window. (Edge case examples in API.md.)

7) API surface (React needs)

Minimal contract summary (exact shapes in API.md):

GET /api/analytics_by_date?start_date&end_date&start_time?&end_time?

Returns compressed day-wise analytics used by Range graphs (OEE, availability, performance, quality + mr variants).

GET /api/analytics_whole_by_date?date

Returns whole-day aggregates for a single day.

GET /api/causes_by_range?start_date&end_date&start_time?&end_time?

Returns stop cause breakdowns across the filtered range.

Shift Manager helpers exposed via plan.py (IDs, planning, editing). Details in API.md.

8) Database model (minimal mental model)

planned_shifts — planned start/end/breaks, auth_id scoped.

current_shift / logs — per-shift event logs (stops, resumes, causes, starved/blocked durations).

shift_summary — finalized metrics after end_shift (totals, efficiencies, parts/rejects).

Invariants:

Every query isolates by auth_id.

Logs are monotonic in time for a shift.

shift_summary exists only after a shift ends.

More detail, column types, indices: DATABASE.md.

9) Front end (what pages do)

Shift Manager: plan/edit/view shifts; calls planning APIs; mirrors DB structure.

History: Day view + Range view using standardized analytics keys (oee, mr_oee, availability, mr_availability, quality, performance, total_stops, machine_error_stops, break_stops, total_runtime, engaged_runtime, machine_uptime, total_downtime, available_downtime, unavailable_downtime, total_parts, total_rejects, expected_parts).

UseTransitionPoller: light polling to reflect state changes.

10) Templates (Jinja) contract

base.html runs the ticking loop (increments UI timers every second). It never writes the DB—it just visualizes.

index.html renders the current shift view and initializes tickers from server values.

11) Config & deploy (bare minimum)

.env: PLC IPs/ports, DB path, FLASK_ENV, secret key.

Local dev: flask run for backend; npm/yarn dev for React front end.

Dependencies: requirements.txt (Flask, SQLite libs) + Node version for front end.

Postgres migration planned for cloud.

12) Logging & troubleshooting

Printouts on state swaps, PLC read failures, API errors (500s).

If live UI is stuck: check PLC comms, app_state thread running, planned_id in session, DB locks.

13) Known limitations

Multiple simultaneous causes → user disambiguation.

PLC disconnect mid-shift → resilience paths still improving.

History filter excludes partially overlapping shifts by design (anchored rule).

14) ADRs (why we did it this way)

Python state machine instead of ladder logic: faster iteration, richer logging.

UI ticking separate from DB: responsive UX without corrupting truth.

Blueprints + services split: clear separation of routing vs. logic; easier to test/migrate.

15) Roadmap (next)

V2: auto starts/stops from signals; recovery on reload; Postgres.

V3: full automation; multi-user; cloud deploy; richer observability.

16) Glossary

EBA: Event Bit Array (9 classified stop causes)

OEE: Overall Equipment Effectiveness (availability × performance × quality)

Engaged runtime: planned runtime adjusted by planned stops

Starved/Blocked: machine waiting for material / unable to output










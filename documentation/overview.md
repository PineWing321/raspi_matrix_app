Overview
📌 Project Summary
This system is a real-time shift tracking and analytics application designed for industrial environments. Its primary goal is to monitor machine state, track shift performance, and calculate key operational metrics like uptime, downtime, and OEE. The application integrates live PLC signals, operator interaction, and backend analytics to deliver accurate shift summaries and actionable data.

🧱 Core Features
Planned Shift Management
Foremen can define planned shift windows including start, stop, and break periods.

Real-Time State Monitoring
A background thread continuously polls PLC tags and detects transitions (e.g., machine_on, cycle_running, blocked, starved).

Auto Recording of Start/Stop Events
Shifts are auto-initiated and stopped based on PLC-driven logic — no manual clock-in required.

Dynamic Analytics Calculations
Metrics such as:

Total Runtime

Machine Uptime

Planned Runtime

Starved / Blocked Time

Parts / Rejects

Efficiency (Machine + Overall)

are calculated on the fly and displayed live.

UI Alerts for Starved / Blocked States
The frontend displays banner warnings and background color changes if the machine enters a starved or blocked state.

Historical Shift Log Access
Operators can view shift summaries, analyze causes, and access granular log history.

⚙️ Tech Stack
Layer	Technology
Backend	Python + Flask
Frontend	Jinja2 Templates + Vanilla JS
Database	SQLite (V1), PostgreSQL-ready
Integration	PLC over Ethernet/IP
Hosting	Local on Pi + optional cloud

🔄 System Flow
Operator plans a shift

Background thread detects PLC state change

Shift auto-starts or stops based on logic

Data is logged, metrics calculated live

Frontend updates UI and stores active metrics in localStorage

Final analytics written to DB at shift end

🧠 Key Design Philosophy
Resilience-first: The app gracefully handles edge cases like early machine cycling or PLC silence.

Simplicity over overengineering: Where possible, logic is expressed clearly and isolated to separate modules.

Scalability-ready: Modular backend supports migration to PostgreSQL, WebSockets, and distributed deployment.

Let me know if you want the Architecture.md next or want this converted into a doc file.








Ask ChatGPT

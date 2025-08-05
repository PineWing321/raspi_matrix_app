# src/__init__.py
from flask import Flask, send_from_directory
from datetime import datetime
from dateutil import parser
import logging
import sys
import os
from threading import Thread
from flask_cors import CORS

from .routes.plan import bp as plan_bp
from .routes.record import bp as record_bp
from .routes.static_pages import bp as static_bp
from .routes.details import bp as details_bp
from .routes.end_shift import bp as end_shift_bp
from .routes.homescreen import bp as home_screen_bp
from .routes.auth import bp as auth_bp
from .routes.extendShift import bp as extend_shift_bp
from .routes.api import bp as api_bp
from .routes.history import bp as history_bp
from .routes import init_db_routes
from .routes.edit_shift import bp as edit_shift_bp
from .services.state_logic import app_state

def setup_logger():
    logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )

def start_poller_thread():
    print(f"[🟢] Starting poller thread in PID {os.getpid()}")
    thread = Thread(target=app_state, daemon=True)
    thread.start()

def create_app():
    app = Flask(__name__,
                static_folder="static",
                template_folder="templates")
    app.secret_key = "super-secret-key-123"
    setup_logger()
    CORS(app)
    # Register Blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(plan_bp)
    app.register_blueprint(record_bp)
    app.register_blueprint(static_bp)
    app.register_blueprint(details_bp)
    app.register_blueprint(end_shift_bp)
    app.register_blueprint(home_screen_bp)
    app.register_blueprint(extend_shift_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(init_db_routes.bp)
    app.register_blueprint(edit_shift_bp)

    # Jinja filters
    def datetimeformat(value, format="%I:%M %p"):
        try:
            if isinstance(value, datetime):
                dt = value
            elif isinstance(value, str):
                dt = parser.parse(value)
            else:
                return value
            return dt.strftime(format)
        except Exception as e:
            print("❌ datetimeformat error:", e)
            return value

    def hmm_format(seconds):
        try:
            seconds = int(float(seconds))
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:02}:{minutes:02}"
        except Exception:
            return "00:00"

    app.jinja_env.filters["datetimeformat"] = datetimeformat
    app.jinja_env.filters["hmm_format"] = hmm_format

    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.route("/shiftmanager")
    def serve_shift_manager():
        return send_from_directory(app.static_folder + "/dist", "index.html")

    @app.route("/assets/<path:filename>")
    def serve_static_assets(filename):
        return send_from_directory(app.static_folder + "/dist/assets", filename)

    # ✅ Only start poller once: in main dev process or in production
    if (os.environ.get("WERKZEUG_RUN_MAIN") == "true") or not app.debug:
     start_poller_thread()

    return app

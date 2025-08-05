from flask import Blueprint, send_from_directory
import os

bp = Blueprint("static_pages", __name__)

@bp.route("/shift_manager", defaults={"path": ""})
@bp.route("/shift_manager/<path:path>")
def serve_react_app(path):
    return send_from_directory("static/dist", "index.html")
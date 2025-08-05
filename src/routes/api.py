#api.py
from flask import Blueprint, jsonify, session
from src.db import get_shift_summaries, get_next_transition, pop_latest_path, grab_first_parts, grab_first_rejects  #You'll write this in a sec
from src.globals import render_ack_event, grab_total_parts, grab_total_rejects
bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/summaries", methods=["GET"])
def summaries():
    auth_id = session["auth_id"]
    try:
        summaries = get_shift_summaries(auth_id)
        return jsonify(summaries)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/shift_logs",methods=["GET"])
def shift_log():
    auth_id=session["auth_id"]

@bp.route('/parts_rejects')
def get_parts_and_rejects():
    first_parts = grab_first_parts()
    first_rejects = grab_first_rejects()
    first_parts = int(first_parts)
    first_rejects = int(first_rejects)
    
    total_parts = grab_total_parts()
    total_rejects = grab_total_rejects() 
    total_parts = total_parts - first_parts
    total_rejects = total_rejects - first_rejects
    return jsonify({
        'parts': total_parts,
        'rejects': total_rejects
    })    

@bp.route("/next_transition", methods=["GET"])
def api_next_transition():
    result = get_next_transition() 
    
    if result:
        
        next_path, message = result
        pop_latest_path()
        return jsonify({
            "next_path": next_path,
            "message": message
            })
       
    else:
        return jsonify({
            "next_path": None,
            "message": None, 
            })
@bp.route("/acknowledge_transition", methods=["POST"])
def clear_next_transition():
    print("ever beign hit dudedddddddd?")
    render_ack_event.set() 
    return jsonify({"status": "cleared"})

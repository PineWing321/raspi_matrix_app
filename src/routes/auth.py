#auth.py
from flask import Blueprint, render_template, request, redirect, session
from src.db import seed_auth_id, get_all_usernames, get_password_by_username, set_mock_auth_id
bp = Blueprint("auth", __name__)



@bp.route("/login", methods=["GET", "POST"])
def log_in():
       if request.method == "POST":
           auth_id = request.form.get("auth_id").strip()
           
           usernames = get_all_usernames()
           if auth_id in usernames:
               session["auth_id"] = auth_id
               return redirect("/password")
           else:
               return render_template("login.html", error="Invalid ID")
       return render_template("login.html")

@bp.route("/password", methods = ["GET", "POST"])
def password():
    if session["auth_id"]:
        auth_id = session["auth_id"]
    else:
        return redirect("login.html", error= "ID failed, re-enter")
    if request.method == "POST":
        password = request.form.get("password").strip()
        info = get_password_by_username(auth_id)
       
        if password == info:
            return redirect("/")
        else:
            return render_template("password.html", error="code is invalid")
    return render_template("password.html")
@bp.route("/logout")
def logout():
    
    session.clear()
    return redirect("/login")

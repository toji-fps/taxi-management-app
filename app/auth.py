import os
from functools import wraps

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _admin_username():
    return os.environ.get("ADMIN_USERNAME", "admin")


def _password_is_valid(password):
    password_hash = os.environ.get("ADMIN_PASSWORD_HASH")
    if password_hash:
        return check_password_hash(password_hash, password)

    plain_password = os.environ.get("ADMIN_PASSWORD")
    return bool(plain_password and password == plain_password)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return jsonify({"error": "Authentication required"}), 401
        return view(*args, **kwargs)

    return wrapped


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if username != _admin_username() or not _password_is_valid(password):
        return jsonify({"error": "Invalid username or password"}), 401

    session.clear()
    session.permanent = True
    session["admin_logged_in"] = True
    session["admin_username"] = username
    return jsonify({"user": {"username": username}})


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.get("/me")
def me():
    if not session.get("admin_logged_in"):
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, "user": {"username": session.get("admin_username")}})

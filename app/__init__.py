import os
from datetime import timedelta

from flask import Flask, jsonify, render_template, request, send_from_directory

from .auth import auth_bp
from .booking import booking_bp
from .clients import clients_bp
from .appointments import appointments_bp
from .db import close_db, ensure_schema, get_db
from .stats import stats_bp


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", os.urandom(32)),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
        JSON_SORT_KEYS=False,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(stats_bp)
    app.teardown_appcontext(close_db)

    app.config["SCHEMA_READY"] = False

    def prepare_schema():
        if app.config["SCHEMA_READY"]:
            return
        ensure_schema()
        app.config["SCHEMA_READY"] = True

    with app.app_context():
        try:
            prepare_schema()
        except Exception as exc:
            app.logger.warning("Database schema check skipped: %s", exc)

    @app.before_request
    def ensure_schema_before_data_routes():
        if request.path.startswith("/api/") and not request.path.startswith("/api/auth/"):
            prepare_schema()

    @app.get("/")
    def index():
        return render_template("book.html")

    @app.get("/book")
    def book_page():
        return render_template("book.html")

    @app.get("/admin")
    def admin_page():
        return render_template("admin.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/debug-db")
    def debug_db():
        try:
            prepare_schema()
            db = get_db()
            with db.cursor() as cur:
                cur.execute("select current_database(), current_user, version()")
                database_info = cur.fetchone()
                cur.execute(
                    """
                    select table_name
                    from information_schema.tables
                    where table_schema = 'public'
                    order by table_name
                    """
                )
                tables = [row["table_name"] for row in cur.fetchall()]
            return jsonify(
                {
                    "status": "connected",
                    "database": database_info["current_database"],
                    "user": database_info["current_user"],
                    "postgres": database_info["version"],
                    "tables": tables,
                }
            )
        except Exception as exc:
            return jsonify({"status": "error", "message": str(exc)}), 500

    @app.get("/favicon.ico")
    def favicon():
        return send_from_directory(app.static_folder, "favicon.svg", mimetype="image/svg+xml")

    return app

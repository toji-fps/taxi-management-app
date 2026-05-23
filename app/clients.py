from flask import Blueprint, jsonify, request

from .auth import login_required
from .db import execute, fetch_all, fetch_one
from .validation import optional_text, required_text


clients_bp = Blueprint("clients", __name__, url_prefix="/api/clients")


@clients_bp.get("")
@login_required
def list_clients():
    search = (request.args.get("search") or "").strip()
    if search:
        rows = fetch_all(
            """
            select c.*,
                count(a.id) as appointment_count,
                coalesce(sum(a.fare_amount) filter (where a.status = 'completed'), 0) as total_revenue
            from clients c
            left join appointments a on a.client_id = c.id
            where c.name ilike %s or c.phone ilike %s or coalesce(c.email, '') ilike %s
            group by c.id
            order by c.created_at desc
            limit 200
            """,
            (f"%{search}%", f"%{search}%", f"%{search}%"),
        )
    else:
        rows = fetch_all(
            """
            select c.*,
                count(a.id) as appointment_count,
                coalesce(sum(a.fare_amount) filter (where a.status = 'completed'), 0) as total_revenue
            from clients c
            left join appointments a on a.client_id = c.id
            group by c.id
            order by c.created_at desc
            limit 200
            """
        )
    return jsonify({"clients": rows})


@clients_bp.post("")
@login_required
def create_client():
    payload = request.get_json(silent=True) or {}
    try:
        name = required_text(payload, "name", "Name")
        phone = required_text(payload, "phone", "Phone")
        email = optional_text(payload, "email")
        notes = optional_text(payload, "notes")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    row = execute(
        """
        insert into clients (name, phone, email, notes)
        values (%s, %s, %s, %s)
        returning *
        """,
        (name, phone, email, notes),
    )
    return jsonify({"client": row}), 201


@clients_bp.patch("/<int:client_id>")
@login_required
def update_client(client_id):
    payload = request.get_json(silent=True) or {}
    try:
        name = required_text(payload, "name", "Name")
        phone = required_text(payload, "phone", "Phone")
        email = optional_text(payload, "email")
        notes = optional_text(payload, "notes")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    row = execute(
        """
        update clients
        set name = %s, phone = %s, email = %s, notes = %s
        where id = %s
        returning *
        """,
        (name, phone, email, notes, client_id),
    )
    if not row:
        return jsonify({"error": "Client not found"}), 404
    return jsonify({"client": row})


@clients_bp.delete("/<int:client_id>")
@login_required
def delete_client(client_id):
    row = fetch_one("select id from clients where id = %s", (client_id,))
    if not row:
        return jsonify({"error": "Client not found"}), 404
    execute("delete from clients where id = %s returning id", (client_id,))
    return jsonify({"ok": True})

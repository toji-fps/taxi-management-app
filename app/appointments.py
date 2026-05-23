from flask import Blueprint, jsonify, request

from .auth import login_required
from .booking import find_or_create_client
from .db import execute, fetch_all, fetch_one
from .validation import (
    optional_text,
    parse_date,
    parse_money,
    parse_passenger_count,
    parse_status,
    parse_time,
    required_text,
)


appointments_bp = Blueprint("appointments", __name__, url_prefix="/api/appointments")


APPOINTMENT_SELECT = """
select
    a.*,
    c.name as client_name,
    c.phone as client_phone,
    c.email as client_email
from appointments a
join clients c on c.id = a.client_id
"""


@appointments_bp.get("")
@login_required
def list_appointments():
    search = (request.args.get("search") or "").strip()
    status = (request.args.get("status") or "").strip()

    clauses = []
    params = []
    if search:
        clauses.append(
            "(c.name ilike %s or c.phone ilike %s or a.pickup_address ilike %s or a.destination ilike %s)"
        )
        params.extend([f"%{search}%"] * 4)
    if status:
        clauses.append("a.status = %s")
        params.append(status)

    where = f" where {' and '.join(clauses)}" if clauses else ""
    rows = fetch_all(
        f"""
        {APPOINTMENT_SELECT}
        {where}
        order by a.appointment_date desc, a.appointment_time desc
        limit 300
        """,
        tuple(params),
    )
    return jsonify({"appointments": rows})


def _appointment_payload(payload):
    name = required_text(payload, "client_name", "Client name")
    phone = required_text(payload, "client_phone", "Client phone")
    client_notes = optional_text(payload, "client_notes")
    client = find_or_create_client(name, phone, client_notes)

    return {
        "client_id": client["id"],
        "pickup_address": required_text(payload, "pickup_address", "Pickup address"),
        "destination": required_text(payload, "destination", "Destination"),
        "appointment_date": parse_date(payload),
        "appointment_time": parse_time(payload),
        "passenger_count": parse_passenger_count(payload),
        "notes": optional_text(payload, "notes"),
        "status": parse_status(payload),
        "fare_amount": parse_money(payload),
    }


@appointments_bp.post("")
@login_required
def create_appointment():
    payload = request.get_json(silent=True) or {}
    try:
        data = _appointment_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    row = execute(
        """
        insert into appointments (
            client_id, pickup_address, destination, appointment_date,
            appointment_time, passenger_count, notes, status, fare_amount
        )
        values (%(client_id)s, %(pickup_address)s, %(destination)s, %(appointment_date)s,
            %(appointment_time)s, %(passenger_count)s, %(notes)s, %(status)s, %(fare_amount)s)
        returning *
        """,
        data,
    )
    return jsonify({"appointment": row}), 201


@appointments_bp.patch("/<int:appointment_id>")
@login_required
def update_appointment(appointment_id):
    payload = request.get_json(silent=True) or {}
    try:
        data = _appointment_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    data["id"] = appointment_id

    row = execute(
        """
        update appointments
        set client_id = %(client_id)s,
            pickup_address = %(pickup_address)s,
            destination = %(destination)s,
            appointment_date = %(appointment_date)s,
            appointment_time = %(appointment_time)s,
            passenger_count = %(passenger_count)s,
            notes = %(notes)s,
            status = %(status)s,
            fare_amount = %(fare_amount)s
        where id = %(id)s
        returning *
        """,
        data,
    )
    if not row:
        return jsonify({"error": "Appointment not found"}), 404
    return jsonify({"appointment": row})


@appointments_bp.delete("/<int:appointment_id>")
@login_required
def delete_appointment(appointment_id):
    row = fetch_one("select id from appointments where id = %s", (appointment_id,))
    if not row:
        return jsonify({"error": "Appointment not found"}), 404
    execute("delete from appointments where id = %s returning id", (appointment_id,))
    return jsonify({"ok": True})

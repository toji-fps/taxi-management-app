from flask import Blueprint, jsonify, request

from .db import execute, fetch_one
from .validation import optional_text, parse_date, parse_passenger_count, parse_time, required_text


booking_bp = Blueprint("booking", __name__, url_prefix="/api")


def find_or_create_client(name, phone, notes=None):
    existing = fetch_one("select * from clients where lower(phone) = lower(%s)", (phone,))
    if existing:
        execute(
            """
            update clients
            set name = %s, notes = coalesce(%s, notes)
            where id = %s
            returning *
            """,
            (name, notes, existing["id"]),
        )
        return fetch_one("select * from clients where id = %s", (existing["id"],))

    return execute(
        """
        insert into clients (name, phone, notes)
        values (%s, %s, %s)
        returning *
        """,
        (name, phone, notes),
    )


@booking_bp.post("/book")
def create_public_booking():
    payload = request.get_json(silent=True) or {}
    try:
        name = required_text(payload, "name", "Name")
        phone = required_text(payload, "phone", "Phone")
        pickup_address = required_text(payload, "pickup_address", "Pickup address")
        destination = required_text(payload, "destination", "Destination")
        appointment_date = parse_date(payload)
        appointment_time = parse_time(payload)
        passenger_count = parse_passenger_count(payload)
        notes = optional_text(payload, "notes")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    client = find_or_create_client(name, phone)
    appointment = execute(
        """
        insert into appointments (
            client_id, pickup_address, destination, appointment_date,
            appointment_time, passenger_count, notes, status
        )
        values (%s, %s, %s, %s, %s, %s, %s, 'pending')
        returning *
        """,
        (
            client["id"],
            pickup_address,
            destination,
            appointment_date,
            appointment_time,
            passenger_count,
            notes,
        ),
    )

    return jsonify(
        {
            "message": "Booking request received",
            "client": {"id": client["id"], "name": client["name"], "phone": client["phone"]},
            "appointment": appointment,
        }
    ), 201

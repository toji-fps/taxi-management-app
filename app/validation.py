from datetime import datetime


STATUSES = {"pending", "confirmed", "in_progress", "completed", "cancelled", "no_show"}


def required_text(payload, field, label=None):
    value = (payload.get(field) or "").strip()
    if not value:
        raise ValueError(f"{label or field.replace('_', ' ').title()} is required")
    return value


def optional_text(payload, field):
    value = payload.get(field)
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def parse_date(payload, field="date"):
    value = required_text(payload, field, "Date")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Date must use YYYY-MM-DD") from exc


def parse_time(payload, field="time"):
    value = required_text(payload, field, "Time")
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise ValueError("Time must use HH:MM") from exc


def parse_passenger_count(payload):
    try:
        value = int(payload.get("passenger_count", 1))
    except (TypeError, ValueError) as exc:
        raise ValueError("Passenger count must be a number") from exc
    if value < 1 or value > 99:
        raise ValueError("Passenger count must be between 1 and 99")
    return value


def parse_status(payload):
    value = (payload.get("status") or "pending").strip()
    if value not in STATUSES:
        raise ValueError("Invalid appointment status")
    return value


def parse_money(payload):
    value = payload.get("fare_amount")
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Fare amount must be numeric") from exc
    if parsed < 0:
        raise ValueError("Fare amount cannot be negative")
    return round(parsed, 2)

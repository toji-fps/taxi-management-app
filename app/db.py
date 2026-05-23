import os
from datetime import date, datetime, time
from decimal import Decimal
from urllib.parse import urlparse, urlunparse

import psycopg2
from flask import g
from psycopg2.extras import RealDictCursor


def _database_url():
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required")

    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://") :]

    parsed = urlparse(value)
    query = parsed.query
    if "sslmode=" not in query and os.environ.get("PGSSLMODE"):
        query = f"{query}&sslmode={os.environ['PGSSLMODE']}" if query else f"sslmode={os.environ['PGSSLMODE']}"
        value = urlunparse(parsed._replace(query=query))
    return value


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(_database_url(), cursor_factory=RealDictCursor)
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def fetch_all(query, params=None):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(query, params or ())
        return [_serialize(row) for row in cur.fetchall()]


def fetch_one(query, params=None):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(query, params or ())
        return _serialize(cur.fetchone())


def execute(query, params=None, returning=True):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(query, params or ())
        row = _serialize(cur.fetchone()) if returning else None
    db.commit()
    return row


def _serialize(value):
    if value is None:
        return None
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, Decimal):
        return float(value)
    return value


def ensure_schema():
    db = get_db()
    statements = [
        """
        create table if not exists clients (
            id bigserial primary key,
            name text not null,
            phone text not null,
            email text,
            notes text,
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now()
        )
        """,
        "create index if not exists clients_phone_lookup_idx on clients (lower(phone))",
        """
        create table if not exists appointments (
            id bigserial primary key,
            client_id bigint not null references clients(id) on delete cascade,
            pickup_address text not null,
            destination text not null,
            appointment_date date not null,
            appointment_time time not null,
            passenger_count integer not null default 1,
            notes text,
            status text not null default 'pending',
            fare_amount numeric(10, 2),
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now(),
            constraint appointments_status_check check (
                status in ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show')
            ),
            constraint passenger_count_positive check (passenger_count > 0)
        )
        """,
        "create index if not exists appointments_client_id_idx on appointments(client_id)",
        "create index if not exists appointments_date_time_idx on appointments(appointment_date, appointment_time)",
        "create index if not exists appointments_status_idx on appointments(status)",
        """
        create or replace function set_updated_at()
        returns trigger as $$
        begin
            new.updated_at = now();
            return new;
        end;
        $$ language plpgsql
        """,
        """
        drop trigger if exists clients_set_updated_at on clients
        """,
        """
        create trigger clients_set_updated_at
        before update on clients
        for each row execute function set_updated_at()
        """,
        """
        drop trigger if exists appointments_set_updated_at on appointments
        """,
        """
        create trigger appointments_set_updated_at
        before update on appointments
        for each row execute function set_updated_at()
        """,
    ]

    alter_statements = [
        "alter table clients add column if not exists email text",
        "alter table clients add column if not exists notes text",
        "alter table clients add column if not exists created_at timestamptz not null default now()",
        "alter table clients add column if not exists updated_at timestamptz not null default now()",
        "alter table appointments add column if not exists pickup_address text",
        "alter table appointments add column if not exists destination text",
        "alter table appointments add column if not exists appointment_date date",
        "alter table appointments add column if not exists appointment_time time",
        "alter table appointments add column if not exists passenger_count integer not null default 1",
        "alter table appointments add column if not exists notes text",
        "alter table appointments add column if not exists status text not null default 'pending'",
        "alter table appointments add column if not exists fare_amount numeric(10, 2)",
        "alter table appointments add column if not exists created_at timestamptz not null default now()",
        "alter table appointments add column if not exists updated_at timestamptz not null default now()",
    ]

    with db.cursor() as cur:
        for statement in statements:
            cur.execute(statement)
        for statement in alter_statements:
            cur.execute(statement)
    db.commit()

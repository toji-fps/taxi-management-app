from flask import Blueprint, jsonify

from .auth import login_required
from .db import fetch_all, fetch_one


stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


@stats_bp.get("/revenue")
@login_required
def revenue_stats():
    summary = fetch_one(
        """
        select
            count(*) as total_appointments,
            count(*) filter (where status = 'pending') as pending,
            count(*) filter (where status = 'confirmed') as confirmed,
            count(*) filter (where status = 'in_progress') as in_progress,
            count(*) filter (where status = 'completed') as completed,
            count(*) filter (where status = 'cancelled') as cancelled,
            count(*) filter (where status = 'no_show') as no_show,
            coalesce(sum(fare_amount) filter (where status = 'completed'), 0) as completed_revenue,
            coalesce(avg(fare_amount) filter (where status = 'completed' and fare_amount is not null), 0) as average_completed_fare
        from appointments
        """
    )
    monthly = fetch_all(
        """
        select
            to_char(date_trunc('month', appointment_date), 'YYYY-MM') as month,
            coalesce(sum(fare_amount) filter (where status = 'completed'), 0) as revenue,
            count(*) filter (where status = 'completed') as rides
        from appointments
        where appointment_date >= current_date - interval '12 months'
        group by date_trunc('month', appointment_date)
        order by month
        """
    )
    return jsonify({"summary": summary, "monthly": monthly})

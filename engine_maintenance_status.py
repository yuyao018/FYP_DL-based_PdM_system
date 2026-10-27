"""Engine maintenance lifecycle, separate from sensor-derived condition."""
from assets import database_integration as db
from dash import html


STATUS_LABELS = {
    "under_maintenance": "Under Maintenance",
    "pending_verification": "Pending Verification",
    "follow_up_required": "Follow-up Required",
    "unavailable": "Maintenance status unavailable",
}


def maintenance_status(schedule_status):
    return {
        "in_progress": "under_maintenance",
        "completed": "pending_verification",
        "follow_up_required": "follow_up_required",
    }.get(schedule_status)


def engine_maintenance_statuses(client, engine_ids):
    """Read lifecycle for a scoped engine set in one query.

    A future booking or cancellation does not clear completed, unverified work.
    Only started work contributes to the lifecycle; latest work takes precedence.
    """
    ids = list(dict.fromkeys(str(eid) for eid in engine_ids if eid))
    if client is None or not ids:
        return {}
    rows = db.fetch_records(
        client, "maintenance_schedules", "engine_id,status,created_at",
        filters=[("in_", "engine_id", ids),
                 ("in_", "status", ["in_progress", "completed", "follow_up_required"])],
        order_by=[("created_at", True)],
    ).data or []
    result = {}
    for row in rows:
        eid = str(row.get("engine_id"))
        if eid in ids and eid not in result:
            result[eid] = maintenance_status(row.get("status"))
    return result


def maintenance_badge(status):
    label = STATUS_LABELS.get(status)
    if not label:
        return None
    color = "#a78bfa" if status == "pending_verification" else "#4a9eff"
    if status == "follow_up_required":
        color = "#ffd93d"
    return html.Span(label, style={
        "color": color, "background": "rgba(167,139,250,0.10)",
        "border": f"1px solid {color}", "borderRadius": "6px",
        "padding": "3px 10px", "fontSize": "11px", "fontWeight": "700",
        "display": "inline-block", "whiteSpace": "nowrap",
    }, title="Maintenance lifecycle; the condition badge shows the last measured condition.")

"""Deterministic maintenance proposals and signed email responses.

One process owns scheduling in the current deployment. The lock serializes
email acceptances; cross-process conflict exclusion requires a DB constraint.
"""
from assets import database_integration as db
import os
import threading
import uuid
from datetime import datetime, timedelta, timezone
from html import escape
from urllib.parse import quote

from itsdangerous import URLSafeTimedSerializer, BadSignature

LOCAL_TZ = timezone(timedelta(hours=8))
BOOKING_LOCK = threading.RLock()
TOKEN_AGE = 7 * 86400


def _signer():
    secret = os.getenv("MAINTENANCE_LINK_SECRET") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not secret:
        raise ValueError("Maintenance email signing is not configured.")
    return URLSafeTimedSerializer(secret, salt="maintenance-response-v1")


def read_proposal(token):
    return _signer().loads(token, max_age=TOKEN_AGE)


def _engine(sb, engine_id):
    response = db.get_engine(sb, engine_id, "id, engine_id, responsible_by, organization_id")
    if not response.data or not response.data.get("responsible_by"):
        raise ValueError("This engine has no responsible technician.")
    return response.data


def _bookings(sb, engine):
    # Include both bookings created by the technician and jobs on their engines.
    assigned = db.fetch_records(
        sb,
        "engines",
        "id",
        filters=[('eq', "responsible_by", engine["responsible_by"])],
    ).data or []
    ids = [str(e["id"]) for e in assigned]
    fields = "id, engine_id, scheduled_date, start_time, end_time, status, created_by"
    rows = db.fetch_records(
        sb,
        "maintenance_schedules",
        fields,
        filters=[('eq', "created_by", engine["responsible_by"])],
    ).data or []
    if ids:
        rows += db.fetch_records(
            sb,
            "maintenance_schedules",
            fields,
            filters=[('in_', "engine_id", ids)],
        ).data or []
    return [r for r in rows if r.get("status") not in ("cancelled", "canceled", "completed")]


def _bounds(row):
    day = row["scheduled_date"]
    return tuple(datetime.fromisoformat(f"{day}T{row[k]}").replace(tzinfo=LOCAL_TZ)
                 for k in ("start_time", "end_time"))


def _available(start, end, bookings):
    return all(not (start < b_end and end > b_start)
               for b_start, b_end in map(_bounds, bookings))


def create_manual_booking(sb, engine_id, day, start_time, end_time, notes, session):
    """Use the same technician and availability rules for the editable form."""
    with BOOKING_LOCK:
        engine = _engine(sb, engine_id)
        if (str(engine["organization_id"]) != str((session or {}).get("organization_id"))
                or ((session or {}).get("role") != "admin"
                    and str(engine["responsible_by"]) != str((session or {}).get("user_id")))):
            raise ValueError("Only the responsible technician or an organization admin can book this engine.")
        start, end = _bounds(dict(scheduled_date=day, start_time=start_time, end_time=end_time))
        if start <= datetime.now(LOCAL_TZ) or start.weekday() >= 5:
            raise ValueError("Choose a future time from Monday to Friday.")
        if end - start != timedelta(hours=2):
            raise ValueError("Please reserve a two-hour maintenance slot.")
        morning = start.hour >= 8 and (end.hour * 60 + end.minute) <= 12 * 60
        afternoon = start.hour >= 13 and (end.hour * 60 + end.minute) <= 17 * 60
        if not (morning or afternoon):
            raise ValueError("Use 08:00–12:00 or 13:00–17:00, excluding lunch.")
        if not _available(start, end, _bookings(sb, engine)):
            raise ValueError("The responsible technician already has a booking at this time.")
        return db.insert_records(sb, "maintenance_schedules", {
            "engine_id": engine_id, "scheduled_date": day,
            "start_time": start_time, "end_time": end_time,
            "notes": notes or "", "status": "scheduled",
            "created_by": engine["responsible_by"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })


def recommend(sb, engine_id, rul, now=None):
    return find_slots(sb, engine_id, rul, now=now, limit=1)[0]


def find_slots(sb, engine_id, rul, now=None, period="any", not_before=None, not_after=None, limit=3):
    now = now or datetime.now(LOCAL_TZ)
    if period not in ("any", "morning", "afternoon"):
        raise ValueError("Choose morning, afternoon, or any time.")
    first_date = datetime.fromisoformat(not_before).date() if not_before else now.date()
    last_date = datetime.fromisoformat(not_after).date() if not_after else None
    slots = []
    engine = _engine(sb, engine_id)
    bookings = _bookings(sb, engine)
    if any(str(b["engine_id"]) == str(engine_id) and _bounds(b)[1] > now for b in bookings):
        raise ValueError("This engine already has a maintenance booking. Review its existing schedule.")
    # Explicit configurable demo margin, shown in every proposal email.
    margin = max(0, float(os.getenv("MAINTENANCE_MARGIN_CYCLES", "5")))
    deadline = now + timedelta(hours=max(0, float(rul) - margin) * 8)
    for offset in range(366):
        day = (now + timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        if day > deadline:
            break
        if day.weekday() >= 5 or day.date() < first_date or (last_date and day.date() > last_date):
            continue
        for hour in (8, 9, 10, 13, 14, 15):
            if (period == "morning" and hour >= 12) or (period == "afternoon" and hour < 13):
                continue
            start = day.replace(hour=hour)
            end = start + timedelta(hours=2)
            if start > now and end <= deadline and _available(start, end, bookings):
                slots.append(dict(engine_id=str(engine_id), technician=str(engine["responsible_by"]),
                            organization_id=str(engine["organization_id"]),
                            scheduled_date=start.date().isoformat(), start_time=start.strftime("%H:%M"),
                            end_time=end.strftime("%H:%M"), deadline=deadline.isoformat(),
                            margin=margin, id=str(uuid.uuid4())))
                if len(slots) >= max(1, min(int(limit), 6)):
                    return slots
    if slots:
        return slots
    raise ValueError("No available two-hour slot before the planning deadline. Please review the engine schedule.")


def email_section(sb, engine_id, rul, base_url):
    try:
        proposal = recommend(sb, engine_id, rul)
        token = _signer().dumps(proposal)
        url = base_url.rstrip("/") + "/maintenance-response/" + token
        return (f'<h3>Recommended maintenance time</h3><p>{proposal["scheduled_date"]}, '
                f'{proposal["start_time"]}–{proposal["end_time"]} (Malaysia time, UTC+8). '
                'Duration: 2 hours. Assigned to this engine’s responsible technician.</p>'
                f'<p>Assumes 1× operation (8 hours/cycle), with a {proposal["margin"]:g}-cycle '
                'planning margin. The slot is rechecked when accepted; this is not a reservation.</p>'
                f'<p><a class="btn" href="{escape(url)}?answer=yes">Yes — accept this time</a> '
                f'<a class="btn" href="{escape(url)}?answer=no">No — choose another time</a></p>'
                '<p>Yes opens a confirmation page. Links expire after seven days; a past slot cannot be accepted.</p>')
    except ValueError as exc:
        return f'<h3>Recommended maintenance time</h3><p>{escape(str(exc))}</p>'
    except Exception:
        return '<h3>Recommended maintenance time</h3><p>Recommendation unavailable. Please open the system to schedule maintenance.</p>'


def accept(sb, proposal, source="email"):
    with BOOKING_LOCK:
        existing = db.fetch_records(sb, "maintenance_schedules", "id", filters=[('eq', "id", proposal["id"])])
        if existing.data:
            return "This recommendation has already been booked."
        engine = _engine(sb, proposal["engine_id"])
        if str(engine["responsible_by"]) != proposal["technician"] or str(engine["organization_id"]) != proposal["organization_id"]:
            raise ValueError("The engine assignment has changed. Please request a new recommendation.")
        start, end = _bounds(proposal)
        now = datetime.now(LOCAL_TZ)
        if start <= now or end > datetime.fromisoformat(proposal["deadline"]):
            raise ValueError("This recommendation is out of date. Please choose another time.")
        from engine_simulation_manager import get_simulation_state
        state = get_simulation_state(proposal["engine_id"])
        if state and state["running"] and state["speed"] != 1:
            raise ValueError("The simulation is accelerated. Return to 1× and request a new recommendation.")
        pred = db.get_latest_prediction(sb, proposal["engine_id"], "predicted_rul")
        if not pred.data:
            raise ValueError("A current RUL prediction is required before booking.")
        deadline = now + timedelta(hours=max(0, float(pred.data[0]["predicted_rul"]) - proposal["margin"]) * 8)
        if end > deadline:
            raise ValueError("The latest prediction requires an earlier appointment.")
        bookings = _bookings(sb, engine)
        if any(str(b["engine_id"]) == proposal["engine_id"] and _bounds(b)[1] > now for b in bookings):
            raise ValueError("This engine already has a booking. Please review its schedule.")
        if not _available(start, end, bookings):
            raise ValueError("The technician is no longer available at this time. Please choose another slot.")
        db.insert_records(sb, "maintenance_schedules", {
            "id": proposal["id"], "engine_id": proposal["engine_id"],
            "scheduled_date": proposal["scheduled_date"], "start_time": proposal["start_time"],
            "end_time": proposal["end_time"], "status": "scheduled",
            "created_by": proposal["technician"],
            "notes": "Accepted via Scheduling Agent." if source == "agent" else "Accepted via signed maintenance recommendation email.",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return "Maintenance has been scheduled successfully."


def register_response_routes(server, sb):
    from flask import request, redirect

    @server.route("/maintenance-response/<token>", methods=["GET", "POST"])
    def maintenance_response(token):
        try:
            proposal = read_proposal(token)
        except (BadSignature, ValueError):
            return "This maintenance link is invalid or expired. Please open the system to schedule maintenance.", 400
        edit_path = f'/schedule-maintenance/{proposal["engine_id"]}/recommendation/{token}'
        if request.method == "GET" and request.args.get("answer") == "no":
            return redirect("/?next=" + quote(edit_path, safe=""))
        status = 200
        if request.method == "POST":
            try:
                message = accept(sb, proposal)
            except ValueError as exc:
                message, status = str(exc), 409
            except Exception:
                message, status = "Unable to save the booking. Please try again or open the scheduling page.", 503
            body = f'<p>{escape(message)}</p>'
        else:
            body = (f'<p>{proposal["scheduled_date"]}, {proposal["start_time"]}–{proposal["end_time"]} '
                    '(Malaysia time). Two hours with the responsible technician.</p>'
                    '<form method="post"><button type="submit">Confirm maintenance booking</button></form>')
        page = ('<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">'
                '<title>Maintenance recommendation</title></head><body style="background:#0a1628;color:#e7f2ff;'
                'font:16px system-ui;max-width:600px;margin:60px auto;padding:24px">'
                '<h1>Maintenance recommendation</h1>' + body +
                f'<p><a style="color:#8bc3ff" href="/?next={quote(edit_path, safe="")}">Choose another time in the system</a></p></body></html>')
        return page, status, {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
                              "X-Frame-Options": "DENY"}


def prefill_layout(layout, proposal):
    values = {"sm-modal-engine": proposal["engine_id"], "sm-modal-date": proposal["scheduled_date"],
              "sm-modal-start-time": proposal["start_time"], "sm-modal-end-time": proposal["end_time"]}
    def visit(node):
        component_id = getattr(node, "id", None)
        if component_id in values:
            node.value = values[component_id]
        if component_id == "sm-modal-engine" and not any(
                str(o["value"]) == proposal["engine_id"] for o in node.options):
            node.options = list(node.options) + [{"label": "Recommended engine", "value": proposal["engine_id"]}]
        if component_id == "sm-modal-overlay":
            node.style = {**node.style, "display": "flex"}
        children = getattr(node, "children", [])
        for child in children if isinstance(children, (list, tuple)) else [children]:
            if child is not None:
                visit(child)
    visit(layout)
    return layout

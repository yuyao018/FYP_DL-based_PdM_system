"""
email_notifications.py
======================
Automated email notification manager for the Predictive Maintenance System.

Two notification types:
  1. Daily fleet summary  — sent every day at 09:00 local time
  2. Threshold alerts     — sent immediately when a new prediction crosses
                            the warning or critical RUL threshold

Configuration (add to .env):
    EMAIL_SENDER=your-sender@gmail.com
    EMAIL_PASSWORD=your-app-password          # Gmail App Password
    # Daily recipients come from users and engine responsibility assignments.
    DASHBOARD_URL=http://localhost:8050  # base URL for the Open Dashboard button
    EMAIL_DAILY_HOUR=9                        # hour (0-23) for daily report, default 9
    SMTP_HOST=smtp.gmail.com                  # optional, default smtp.gmail.com
    SMTP_PORT=587                             # optional, default 587

Usage — call once at app startup:
    from email_notifications import start_notification_manager
    start_notification_manager(supabase)
"""

import os
import json
import smtplib
import threading
import traceback
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from assets import database_integration as db


# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────

def _cfg(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


# ─────────────────────────────────────────────
#  SMTP SEND
# ─────────────────────────────────────────────

def _send_email(subject: str, html_body: str, recipients_override: list = None) -> bool:
    """Send an HTML email via SMTP (Gmail)."""
    sender    = _cfg("EMAIL_SENDER")
    password  = _cfg("EMAIL_PASSWORD")
    smtp_host = _cfg("SMTP_HOST")
    smtp_port = int(_cfg("SMTP_PORT"))

    # Use dynamic recipients if provided, else skip
    if recipients_override:
        recipients = recipients_override
    else:
        recipients = []

    if not recipients:
        print("[EMAIL] Skipping — no recipients found for this engine.")
        return False

    if not sender or not password:
        print("[EMAIL] Skipping — EMAIL_SENDER or EMAIL_PASSWORD not configured.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        print(f"[EMAIL] Sent via SMTP '{subject}' → {recipients}")
        return True
    except Exception:
        print(f"[EMAIL][ERROR] SMTP failed:\n{traceback.format_exc()}")
        return False


# ─────────────────────────────────────────────
#  FETCH HELPERS
# ─────────────────────────────────────────────

def _fetch_thresholds(supabase) -> tuple[int, int]:
    """Return (warn_thresh, crit_thresh) from the alert_thresholds table."""
    try:
        resp = db.get_alert_thresholds(
            supabase, "warning_threshold, critical_threshold")
        if resp.data:
            return (
                int(resp.data[0].get("warning_threshold", 50)),
                int(resp.data[0].get("critical_threshold", 30)),
            )
    except Exception:
        pass
    return 50, 30


def _fetch_fleet_summary(supabase, engine_ids=None) -> dict:
    """
    Return fleet summary counts using the latest predicted_rul per engine,
    evaluated against the current alert_thresholds.
    """
    warn_thresh, crit_thresh = _fetch_thresholds(supabase)
    total = critical = warning = normal = 0

    try:
        if engine_ids is None:
            engines_resp = db.fetch_records(supabase, "engines", "id")
            engine_ids = [e["id"] for e in (engines_resp.data or []) if e.get("id")]
        total        = len(engine_ids)

        if not engine_ids:
            return {"total": 0, "critical": 0, "warning": 0, "normal": 0}

        # Fetch latest predicted_rul per engine
        pred_resp = db.fetch_records(
            supabase, "rul_predictions", "engine_id, predicted_rul",
            filters=[("in_", "engine_id", engine_ids)],
            order_by=[("predicted_at", True)])

        # Keep only the first (latest) row per engine
        seen: set = set()
        for row in (pred_resp.data or []):
            eid = row.get("engine_id")
            if eid and eid not in seen and row.get("predicted_rul") is not None:
                seen.add(eid)
                rul = float(row["predicted_rul"])
                if rul <= crit_thresh:
                    critical += 1
                elif rul <= warn_thresh:
                    warning += 1
                else:
                    normal += 1

        # Engines with no prediction yet count as normal
        no_pred = total - len(seen)
        normal += no_pred

    except Exception:
        print(f"[EMAIL][ERROR] Fleet summary fetch:\n{traceback.format_exc()}")

    return {"total": total, "critical": critical, "warning": warning, "normal": normal}


# ─────────────────────────────────────────────
#  EMAIL TEMPLATES
# ─────────────────────────────────────────────

def _fmt_date(dt: Optional[datetime] = None) -> str:
    """Format a datetime as '10th Jun 2026'."""
    if dt is None:
        dt = datetime.now()
    day = dt.day
    suffix = (
        "th" if 11 <= day <= 13 else
        {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    )
    return dt.strftime(f"{day}{suffix} %b %Y")


def _email_header(title: str, subtitle: str) -> str:
    """One email-safe PRISM heading shared by daily and threshold reports."""
    from html import escape
    return f'''<table role="presentation" width="100%" cellspacing="0" cellpadding="0">
      <tr><td style="background:#0d1e36;padding:28px 30px;border-radius:15px 15px 0 0;border-top:4px solid #49cfc6;font-family:Arial,Helvetica,sans-serif;">
        <div style="font-size:23px;font-weight:700;letter-spacing:4px;color:#ffffff;">PRISM<span style="color:#64e6dd;"> /</span></div>
        <div style="font-size:11px;letter-spacing:1.5px;color:#a8c4df;padding-top:7px;">PREDICTIVE MAINTENANCE</div>
        <h1 style="font-size:26px;line-height:34px;font-weight:700;color:#ffffff;margin:28px 0 6px;">{escape(title)}</h1>
        <div style="font-size:13px;color:#a8c4df;">{escape(subtitle)}</div>
      </td></tr>
    </table>'''


def _daily_report_html(summary: dict) -> str:
    from html import escape

    login_url = escape(_cfg("DASHBOARD_URL", "http://localhost:8050").rstrip("/") + "/login", quote=True)
    date_str = _fmt_date()
    critical, warning = summary["critical"], summary["warning"]
    if critical:
        headline = "Critical engines need your attention"
        message = "Review critical engines first, then plan maintenance for those in warning."
        accent, tint = "#c03640", "#fff1f2"
    elif warning:
        headline = "Plan ahead for engines in warning"
        message = "Review their remaining useful life and upcoming maintenance in your dashboard."
        accent, tint = "#946200", "#fff8e8"
    elif not summary["total"]:
        headline = "No engines in this report"
        message = "Your daily summary will appear here once engines are available."
        accent, tint = "#245caa", "#eff5ff"
    else:
        headline = "No warning or critical engines reported"
        message = "Open your dashboard to review the latest predictions and monitoring coverage."
        accent, tint = "#167457", "#edf9f3"

    cards = []
    for label, key, color, background in (
        ("MONITORED", "total", "#245caa", "#eff5ff"),
        ("CRITICAL", "critical", "#c03640", "#fff1f2"),
        ("WARNING", "warning", "#946200", "#fff8e8"),
        ("NORMAL", "normal", "#167457", "#edf9f3"),
    ):
        cards.append(f'''<td width="50%" valign="top" style="padding:6px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{background};border:1px solid #e2e8f0;border-radius:10px;">
            <tr><td style="padding:20px 22px;">
              <div style="font-size:11px;font-weight:700;letter-spacing:1px;color:{color};">{label}</div>
              <div style="padding-top:8px;font-size:36px;line-height:42px;font-weight:700;color:#102440;">{summary[key]}</div>
              <div style="font-size:12px;color:#64748b;padding-top:3px;">engines</div>
            </td></tr>
          </table>
        </td>''')
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PRISM daily report</title></head>
<body style="margin:0;padding:0;background:#eef2f7;font-family:Arial,Helvetica,sans-serif;color:#102440;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">Your daily engine summary: {critical} critical, {warning} warning, {summary['total']} monitored.</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef2f7;">
<tr><td align="center" style="padding:32px 12px;">
  <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="width:100%;max-width:600px;background:#ffffff;border:1px solid #dce4ee;border-radius:16px;">
    <tr><td>{_email_header("Your daily engine briefing", date_str + " · Daily RUL status report")}</td></tr>
    <tr><td style="padding:26px 24px 0;">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{tint};border-left:3px solid {accent};border-radius:6px;">
        <tr><td style="padding:16px 18px;">
          <div style="font-size:15px;line-height:22px;font-weight:700;color:{accent};">{headline}</div>
          <div style="font-size:13px;line-height:21px;color:#475569;padding-top:5px;">{message}</div>
        </td></tr>
      </table>
    </td></tr>
    <tr><td style="padding:24px 30px 10px;font-size:11px;font-weight:700;letter-spacing:1.5px;color:#64748b;">ENGINE STATUS AT A GLANCE</td></tr>
    <tr><td style="padding:0 18px;">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
        <tr>{cards[0]}{cards[1]}</tr><tr>{cards[2]}{cards[3]}</tr>
      </table>
    </td></tr>
    <tr><td style="padding:24px 30px 28px;">
      <p style="font-size:14px;line-height:23px;color:#475569;margin:0 0 20px;">Explore engine predictions, sensor trends and maintenance activity in PRISM.</p>
      <table role="presentation" cellspacing="0" cellpadding="0"><tr><td bgcolor="#205caa" style="border-radius:7px;text-align:center;">
        <a href="{login_url}" style="display:inline-block;padding:14px 24px;border:1px solid #205caa;border-radius:7px;font-size:14px;font-weight:700;color:#ffffff;text-decoration:none;">Open dashboard &nbsp;&rarr;</a>
      </td></tr></table>
    </td></tr>
    <tr><td style="padding:20px 30px;border-top:1px solid #e6edf5;background:#f8fafc;border-radius:0 0 15px 15px;">
      <div style="font-size:12px;font-weight:700;color:#475569;">PRISM &middot; Predictive Maintenance Monitoring System</div>
      <p style="font-size:11px;line-height:18px;color:#7b889a;margin:7px 0 0;">This report covers the engines available to your account. Status counts use the configured RUL thresholds; engines without predictions are currently included as normal.</p>
      <p style="font-size:11px;line-height:18px;color:#7b889a;margin:7px 0 0;">Automated daily report. Please do not reply to this email.</p>
    </td></tr>
  </table>
</td></tr></table>
</body></html>'''



def _threshold_alert_html(
    engine_display_id: str,
    level: str,              # "warning" or "critical"
    pred_rul: float,
    threshold: int,
    engine_db_id: str,
    triggered_at: Optional[datetime] = None,
    recommendation_html: str = "",
) -> str:
    base_url = _cfg("DASHBOARD_URL", "http://localhost:8050")
    # Deep link: after login, navigate directly to this engine's alert log
    dashboard_url = f"{base_url}/?next=/alert-log/{engine_db_id}"
    date_str = _fmt_date(triggered_at)
    is_critical = level.lower() == "critical"

    btn_bg      = "#a00000" if is_critical else "#7a5c1e"
    badge_bg    = "#f5c6c6" if is_critical else "#fde8a0"
    badge_color = "#a00000" if is_critical else "#7a5c1e"
    badge_text  = "CRITICAL" if is_critical else "WARNING"
    title       = f"Critical RUL Alert" if is_critical else "RUL Warning"
    intro       = (
        "The Predictive Maintenance Monitoring System has detected a critical "
        "degradation condition. Immediate inspection or maintenance is required."
        if is_critical else
        "An engine is approaching its maintenance threshold. Please schedule "
        "an inspection at your earliest convenience."
    )
    dashboard_link_text = (
        "View the full sensor report and SHAP analysis on the dashboard:"
        if is_critical else
        "View sensor trends and degradation analysis report on the dashboard:"
    )

    return f"""<!DOCTYPE html>
    <html>
    <head><meta charset="utf-8">
    <style>
    body {{ font-family: Georgia, serif; background: #f4f4f4; margin: 0; padding: 0; }}
    .wrapper {{ max-width: 640px; margin: 30px auto; background: #fff; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.12); }}
    .engine-badge {{ background: rgba(255,255,255,0.18); color: #fff; padding: 3px 10px; border-radius: 4px; font-size: 13px; font-family: monospace; }}
    .body {{ padding: 28px 28px 20px; color: #222; font-size: 14px; line-height: 1.7; }}
    .detail-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    .detail-table td {{ padding: 8px 12px; border-bottom: 1px solid #eee; font-size: 14px; }}
    .detail-table td:first-child {{ color: #555; width: 38%; }}
    .detail-table td:last-child {{ font-weight: bold; text-align: right; }}
    .badge {{ display: inline-block; background: {badge_bg}; color: {badge_color}; padding: 3px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; letter-spacing: 0.5px; }}
    .btn {{ display: inline-block; background: {btn_bg}; color: #ffffff !important; padding: 11px 22px; border-radius: 4px; text-decoration: none; font-size: 13px; margin-top: 6px; font-weight: 600; }}
    .footer {{ padding: 14px 28px; border-top: 1px solid #eee; color: #999; font-size: 11px; }}
    </style>
    </head>
    <body>
    <div class="wrapper">
    {_email_header(title, date_str + " · Engine #" + str(engine_display_id))}
    <div class="body">
        <p>Hi <strong>Team</strong>,</p>
        <p>{intro}</p>
        <table class="detail-table">
        <tr><td>Engine ID</td>      <td>#{engine_display_id}</td></tr>
        <tr><td>Alert level</td>    <td><span class="badge">{badge_text}</span></td></tr>
        <tr><td>Estimated RUL</td>  <td>{int(round(pred_rul))} cycles</td></tr>
        <tr><td>Alert threshold</td><td>{threshold} cycles</td></tr>
        <tr><td>Timestamp</td>      <td>{date_str}</td></tr>
        </table>
        {recommendation_html}
        <p>{dashboard_link_text}</p>
        <a class="btn" href="{dashboard_url}" style="color: #ffffff !important; text-decoration: none;">Open Dashboard</a>
    </div>
    <div class="footer">
        This is an automated message from the Predictive Maintenance Monitoring System. Do not reply to this email.
    </div>
    </div>
    </body>
    </html>"""


# ─────────────────────────────────────────────
#  ALERT DEDUPLICATION & RE-ALERT LOGIC
#  - Fires once when threshold first crossed
#  - Re-fires every 12h if the alert remains active
#  - Escalation from warning → critical always fires immediately
# ─────────────────────────────────────────────

# { engine_db_id: {"level": str, "last_sent": datetime} }
_alert_state: dict[str, dict] = {}
_alert_lock = threading.Lock()

_REALERT_INTERVAL = timedelta(hours=12)


def _should_send_alert(engine_db_id: str, new_level: str, supabase=None) -> bool:
    """
    Return True if an alert should be sent.
    Logic:
      - healthy → reset state, no alert
      - First time crossing threshold → alert
      - Same level already sent → check if 12h passed AND the alert remains active
      - Escalation (warning → critical) → always alert
    """
    with _alert_lock:
        prev = _alert_state.get(engine_db_id)
        now = datetime.now(timezone.utc)

        if new_level == "healthy":
            _alert_state[engine_db_id] = None
            return False

        if prev is None:
            # First time this session — check DB to avoid duplicate sends
            # within the same app session. But only block if already resolved.
            # An existing "active" row means it was logged before but email may not have
            # been sent (e.g. app restarted). We should still attempt to send.
            if supabase:
                try:
                    resp = db.fetch_records(
                        supabase, "alert_logs", "status, triggered_at",
                        filters=[("eq", "engine_id", engine_db_id)],
                        order_by=[("triggered_at", True)], limit=1)
                    if resp.data:
                        latest_status = resp.data[0].get("status")
                        if latest_status == "resolved":
                            # Already handled — don't re-alert
                            _alert_state[engine_db_id] = {"level": new_level, "last_sent": now}
                            return False
                        # "active" → fall through and send (may have been missed)
                except Exception:
                    pass
            _alert_state[engine_db_id] = {"level": new_level, "last_sent": now}
            return True

        prev_level = prev.get("level")
        last_sent = prev.get("last_sent", now)

        # Escalation: warning → critical — always fire
        if new_level == "critical" and prev_level == "warning":
            _alert_state[engine_db_id] = {"level": new_level, "last_sent": now}
            return True

        # Don't downgrade
        if new_level == "warning" and prev_level == "critical":
            return False

        # Same level — check if 12h passed and still the alert remains active
        if now - last_sent >= _REALERT_INTERVAL:
            # Check DB: is the latest alert still active?
            if supabase:
                try:
                    resp = db.fetch_records(
                        supabase, "alert_logs", "status",
                        filters=[("eq", "engine_id", engine_db_id)],
                        order_by=[("triggered_at", True)], limit=1)
                    if resp.data and resp.data[0].get("status") == "active":
                        # Still active after 12h — re-alert
                        _alert_state[engine_db_id] = {"level": new_level, "last_sent": now}
                        return True
                except Exception:
                    pass

        return False


# ─────────────────────────────────────────────
#  THRESHOLD ALERT TRIGGER  (called from simulation loop)
# ─────────────────────────────────────────────

def _get_alert_recipients(supabase, engine_db_id: str) -> list:
    """
    Return only the engine's responsible user's email address.
    Organization administrators monitor alerts through the dashboard.
    """
    recipients = set()

    if not supabase:
        print("[EMAIL] _get_alert_recipients: no supabase client")
        return []

    try:
        # Get engine's organization_id and responsible_by
        eng_resp = db.get_engine(
            supabase, engine_db_id, "organization_id, responsible_by")

        if not eng_resp.data:
            print(f"[EMAIL] No engine row found for id={engine_db_id}")
            return []

        org_id = eng_resp.data.get("organization_id")
        responsible_by = eng_resp.data.get("responsible_by")
        print(f"[EMAIL] engine org_id={org_id} responsible_by={responsible_by}")

        # Get responsible user's email
        if responsible_by:
            try:
                user_resp = db.fetch_records(
                    supabase, "users", "email_address,is_deleted",
                    filters=[("eq", "id", responsible_by)], single=True)
                profile = user_resp.data or {}
                if profile.get("is_deleted") is False:
                    return []
                email = profile.get("email_address")
                if email:
                    recipients.add(email)
                    print(f"[EMAIL] Responsible user email: {email}")
                else:
                    print(f"[EMAIL] Responsible user {responsible_by} has no email_address")
            except Exception as e:
                print(f"[EMAIL] Failed to fetch responsible user email: {e}")

    except Exception as e:
        print(f"[EMAIL] Failed to resolve recipients for engine {engine_db_id}: {e}")

    result = sorted(recipients)
    print(f"[EMAIL] Final recipients for engine {engine_db_id}: {result}")
    return result


def check_and_send_threshold_alert(
    supabase,
    engine_db_id: str,
    engine_display_id: str,   # human-readable e.g. "01"
    pred_rul: float,
    warn_thresh: int,
    crit_thresh: int,
    trigger_cycle: int = None,
) -> None:
    """
    Call this every prediction cycle. Sends an email only when the engine
    first crosses a threshold (deduplication prevents repeated alerts).
    Stores a snapshot of pred_rul and trigger_cycle in alert_logs so
    historical alerts are never overwritten by later simulation data.
    """
    if pred_rul <= crit_thresh:
        level = "critical"
        threshold = crit_thresh
    elif pred_rul <= warn_thresh:
        level = "warning"
        threshold = warn_thresh
    else:
        # Engine healthy — reset alert state
        _should_send_alert(engine_db_id, "healthy", supabase=supabase)
        return

    print(f"[EMAIL] Threshold crossed: engine={engine_db_id} rul={pred_rul:.1f} level={level} thresh={threshold}")

    if not _should_send_alert(engine_db_id, level, supabase=supabase):
        print(f"[EMAIL] Skipping — alert already sent for level={level} on engine {engine_db_id}")
        return  # already sent for this level

    print(f"[EMAIL] Sending {level} alert for engine {engine_db_id}...")

    now = datetime.now(timezone.utc)

    # ── Insert into alert_logs table — snapshot RUL and cycle at trigger time ──
    try:
        insert_data = {
            "engine_id":     engine_db_id,
            "severity":      level,
            "status":        "active",              # legacy column kept for compatibility
            "triggered_at":  now.isoformat(),
            "predicted_rul": round(float(pred_rul), 2),
        }
        if trigger_cycle is not None:
            insert_data["trigger_cycle"] = int(trigger_cycle)
        db.insert_records(supabase, "alert_logs", insert_data)
        print(f"[EMAIL] Logged alert to alert_logs: engine={engine_db_id} severity={level} "
              f"rul={pred_rul:.1f} cycle={trigger_cycle}")
    except Exception:
        print(f"[EMAIL][ERROR] Failed to insert alert_logs:\n{traceback.format_exc()}")

    display_id = f"Engine-{str(engine_display_id).zfill(2)}"
    subject = (
        f"🚨 Critical RUL Alert — {display_id}"
        if level == "critical"
        else f"⚠️ RUL Warning — {display_id}"
    )
    # Resolve only the responsible user; administrators use dashboard charts.
    dynamic_recipients = _get_alert_recipients(supabase, engine_db_id)

    def _send():
        from maintenance_recommendations import email_section

        recommendation_html = email_section(
            supabase, engine_db_id, pred_rul,
            _cfg("DASHBOARD_URL", "http://localhost:8050"),
        )
        html = _threshold_alert_html(
            engine_display_id=str(engine_display_id).zfill(2),
            level=level,
            pred_rul=pred_rul,
            threshold=threshold,
            engine_db_id=engine_db_id,
            triggered_at=now,
            recommendation_html=recommendation_html,
        )
        _send_email(subject, html, recipients_override=dynamic_recipients)

    threading.Thread(target=_send, daemon=True, name=f"email-alert-{engine_db_id}").start()


# ─────────────────────────────────────────────
#  DAILY REPORT SCHEDULER
# ─────────────────────────────────────────────

def _send_daily_reports(supabase) -> None:
    """Send private summaries of assigned engines or an admin's organization."""
    if not supabase:
        print("[EMAIL] Daily reports skipped — no database client")
        return
    users = db.fetch_records(
        supabase, "users", "id,email_address,role,organization_id,is_deleted").data or []
    engines = db.fetch_records(
        supabase, "engines", "id,organization_id,responsible_by,is_deleted").data or []
    subject = f"Daily RUL Status Report — {_fmt_date()}"
    summaries = {}
    for user in users:
        # Legacy schema: false means removed; true/NULL means available.
        # Online/offline presence in status does not determine eligibility.
        if user.get("is_deleted") is False:
            continue
        email = (user.get("email_address") or "").strip()
        org_id = user.get("organization_id")
        if not email or not org_id or not user.get("id"):
            continue
        role = (user.get("role") or "").strip().lower()
        if role not in ("admin", "administrator", "user"):
            continue
        is_admin = role in ("admin", "administrator")
        engine_ids = tuple(sorted({
            engine["id"] for engine in engines
            if engine.get("id") and engine.get("organization_id") == org_id
            and engine.get("is_deleted") is not False
            and (is_admin or engine.get("responsible_by") == user["id"])
        }))
        if not engine_ids and not is_admin:
            continue
        try:
            if engine_ids not in summaries:
                summaries[engine_ids] = _fetch_fleet_summary(supabase, engine_ids)
            _send_email(subject, _daily_report_html(summaries[engine_ids]),
                        recipients_override=[email])
        except Exception:
            print(f"[EMAIL][ERROR] Daily recipient report failed:\n{traceback.format_exc()}")


def _seconds_until_next_run(hour: int) -> float:
    """Return seconds until the next occurrence of `hour:00` local time."""
    now  = datetime.now()
    next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return (next_run - now).total_seconds()


def _daily_scheduler_loop(supabase, hour: int) -> None:
    """Background thread: sleeps until 09:00, sends report, repeats."""
    while True:
        wait = _seconds_until_next_run(hour)
        print(f"[EMAIL] Daily report scheduled in {wait/3600:.2f} h (at {hour:02d}:00)")
        threading.Event().wait(wait)  # interruptible sleep

        try:
            _send_daily_reports(supabase)
        except Exception:
            print(f"[EMAIL][ERROR] Daily report failed:\n{traceback.format_exc()}")


# ─────────────────────────────────────────────
#  PUBLIC ENTRY POINT
# ─────────────────────────────────────────────

def start_notification_manager(supabase) -> None:
    """
    Start the background daily-report scheduler thread.
    Call once from app.py at startup.

    Threshold alerts are fired from engine_simulation_manager.py by calling
    check_and_send_threshold_alert() inside the prediction loop.
    """
    # Require EMAIL_SENDER + EMAIL_PASSWORD for SMTP
    if not _cfg("EMAIL_SENDER") or not _cfg("EMAIL_PASSWORD"):
        print("[EMAIL] Notification manager not started — "
              "set EMAIL_SENDER and EMAIL_PASSWORD in .env")
        return

    hour = int(_cfg("EMAIL_DAILY_HOUR", "9"))
    t = threading.Thread(
        target=_daily_scheduler_loop,
        args=(supabase, hour),
        daemon=True,
        name="email-daily-scheduler",
    )
    t.start()
    print(f"[EMAIL] Notification manager started — daily report at {hour:02d}:00")

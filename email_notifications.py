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
    EMAIL_RECIPIENTS=a@co.com,b@co.com        # comma-separated
    DASHBOARD_URL=http://localhost:8050        # base URL for the Open Dashboard button
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


# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────

def _cfg(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


# ─────────────────────────────────────────────
#  SMTP SEND
# ─────────────────────────────────────────────

def _send_email(subject: str, html_body: str) -> bool:
    """Send an HTML email via Resend API. Falls back to SMTP if Resend not configured."""
    resend_key = _cfg("RESEND_API_KEY")
    recipients = [r.strip() for r in _cfg("EMAIL_RECIPIENTS").split(",") if r.strip()]
    sender     = _cfg("EMAIL_SENDER", "alerts@resend.dev")

    if not recipients:
        print("[EMAIL] Skipping — EMAIL_RECIPIENTS not configured.")
        return False

    # ── Primary: Resend API (works on all platforms) ──
    if resend_key:
        try:
            import resend
            resend.api_key = resend_key
            r = resend.Emails.send({
                "from": sender,
                "to": recipients,
                "subject": subject,
                "html": html_body,
            })
            print(f"[EMAIL] Sent via Resend '{subject}' → {recipients} (id={r.get('id', '?')})")
            return True
        except Exception:
            print(f"[EMAIL][ERROR] Resend failed:\n{traceback.format_exc()}")
            return False

    # ── Fallback: SMTP (for local development) ──
    password  = _cfg("EMAIL_PASSWORD")
    smtp_host = _cfg("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(_cfg("SMTP_PORT", "587"))

    if not sender or not password:
        print("[EMAIL] Skipping — no RESEND_API_KEY or EMAIL_PASSWORD configured.")
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
        resp = supabase.table("alert_thresholds") \
            .select("warning_threshold, critical_threshold") \
            .order("updated_at", desc=True) \
            .limit(1) \
            .execute()
        if resp.data:
            return (
                int(resp.data[0].get("warning_threshold", 62)),
                int(resp.data[0].get("critical_threshold", 30)),
            )
    except Exception:
        pass
    return 62, 30


def _fetch_fleet_summary(supabase) -> dict:
    """
    Return fleet summary counts using the latest predicted_rul per engine,
    evaluated against the current alert_thresholds.
    """
    warn_thresh, crit_thresh = _fetch_thresholds(supabase)
    total = critical = warning = normal = 0

    try:
        engines_resp = supabase.table("engines").select("id").execute()
        engine_ids   = [e["id"] for e in (engines_resp.data or []) if e.get("id")]
        total        = len(engine_ids)

        if not engine_ids:
            return {"total": 0, "critical": 0, "warning": 0, "normal": 0}

        # Fetch latest predicted_rul per engine
        pred_resp = supabase.table("rul_predictions") \
            .select("engine_id, predicted_rul") \
            .in_("engine_id", engine_ids) \
            .order("predicted_at", desc=True) \
            .execute()

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


def _daily_report_html(summary: dict) -> str:
    login_url = _cfg("DASHBOARD_URL", "http://localhost:8050") + "/login"
    date_str = _fmt_date()

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  body {{ font-family: Georgia, serif; background: #f4f4f4; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 640px; margin: 30px auto; background: #fff; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.12); }}
  .header {{ background: #1a3a6b; padding: 18px 28px; }}
  .header h1 {{ color: #fff; margin: 0; font-size: 18px; font-weight: normal; letter-spacing: 0.3px; }}
  .header span {{ color: #a8c4f0; font-size: 14px; }}
  .body {{ padding: 28px 28px 20px; color: #222; font-size: 14px; line-height: 1.6; }}
  .cards {{ display: flex; gap: 12px; margin: 22px 0; }}
  .card {{ flex: 1; text-align: center; padding: 14px 10px; border-radius: 6px; border: 1px solid #ddd; }}
  .card .label {{ font-size: 12px; color: #666; margin-bottom: 6px; }}
  .card .value {{ font-size: 28px; font-weight: bold; }}
  .card-monitored {{ background: #f0f4ff; }}
  .card-critical  {{ background: #fff0f0; }} .card-critical .value {{ color: #c0392b; }}
  .card-warning   {{ background: #fffbea; }} .card-warning  .value {{ color: #b8860b; }}
  .card-normal    {{ background: #f0fff4; }} .card-normal   .value {{ color: #27ae60; }}
  .btn {{ display: inline-block; background: #1a3a6b; color: #ffffff !important; padding: 11px 22px; border-radius: 4px; text-decoration: none; font-size: 13px; margin-top: 6px; font-weight: 600; }}
  .footer {{ padding: 14px 28px; border-top: 1px solid #eee; color: #999; font-size: 11px; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Daily RUL Status Report &mdash; <span>{date_str}</span></h1>
  </div>
  <div class="body">
    <p>Hi <strong>Team</strong>,</p>
    <p>Here is your fleet status summary for today.</p>
    <div class="cards">
      <div class="card card-monitored">
        <div class="label">Monitored</div>
        <div class="value">{summary['total']}</div>
      </div>
      <div class="card card-critical">
        <div class="label" style="color:#c0392b">Critical</div>
        <div class="value">{summary['critical']}</div>
      </div>
      <div class="card card-warning">
        <div class="label" style="color:#b8860b">Warning</div>
        <div class="value">{summary['warning']}</div>
      </div>
      <div class="card card-normal">
        <div class="label" style="color:#27ae60">Normal</div>
        <div class="value">{summary['normal']}</div>
      </div>
    </div>
    <p>For detailed sensor data and RUL predictions, visit the dashboard:</p>
    <a class="btn" href="{login_url}" style="color: #ffffff !important; text-decoration: none;">Open Dashboard</a>
  </div>
  <div class="footer">
    This is an automated message from the Predictive Maintenance Monitoring System. Do not reply to this email.
  </div>
</div>
</body>
</html>"""


def _threshold_alert_html(
    engine_display_id: str,
    level: str,              # "warning" or "critical"
    pred_rul: float,
    threshold: int,
    engine_db_id: str,
    triggered_at: Optional[datetime] = None,
) -> str:
    dashboard_url = (
        _cfg("DASHBOARD_URL", "http://localhost:8050")
        + "/login"
    )
    date_str = _fmt_date(triggered_at)
    is_critical = level.lower() == "critical"

    header_bg   = "#8b1a1a" if is_critical else "#7a5c1e"
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
  .header {{ background: {header_bg}; padding: 16px 24px; display: flex; align-items: center; gap: 12px; }}
  .header h1 {{ color: #fff; margin: 0; font-size: 17px; font-weight: normal; }}
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
  <div class="header">
    <h1>{title} &mdash; Engine</h1>
    <span class="engine-badge">#{engine_display_id}</span>
  </div>
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
#  - Re-fires every 12h if not acknowledged by the responsible person
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
      - Same level already sent → check if 12h passed AND not acknowledged
      - Escalation (warning → critical) → always alert
    """
    with _alert_lock:
        prev = _alert_state.get(engine_db_id)
        now = datetime.now(timezone.utc)

        if new_level == "healthy":
            _alert_state[engine_db_id] = None
            return False

        if prev is None:
            # First time this session — check DB to avoid duplicate alerts
            if supabase:
                try:
                    resp = supabase.table("alert_logs") \
                        .select("status, triggered_at") \
                        .eq("engine_id", engine_db_id) \
                        .order("triggered_at", desc=True) \
                        .limit(1) \
                        .execute()
                    if resp.data:
                        latest_status = resp.data[0].get("status")
                        if latest_status in ("acknowledged", "resolved"):
                            # Already handled — don't re-alert
                            _alert_state[engine_db_id] = {"level": new_level, "last_sent": now}
                            return False
                        elif latest_status == "active":
                            # Active alert exists — track state but don't duplicate
                            _alert_state[engine_db_id] = {"level": new_level, "last_sent": now}
                            return False
                except Exception:
                    pass
            # No existing alert found — send first alert
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

        # Same level — check if 12h passed and still not acknowledged
        if now - last_sent >= _REALERT_INTERVAL:
            # Check DB: is the latest alert still unacknowledged?
            if supabase:
                try:
                    resp = supabase.table("alert_logs") \
                        .select("status") \
                        .eq("engine_id", engine_db_id) \
                        .order("triggered_at", desc=True) \
                        .limit(1) \
                        .execute()
                    if resp.data and resp.data[0].get("status") == "active":
                        # Not acknowledged after 12h — re-alert
                        _alert_state[engine_db_id] = {"level": new_level, "last_sent": now}
                        return True
                except Exception:
                    pass

        return False


# ─────────────────────────────────────────────
#  THRESHOLD ALERT TRIGGER  (called from simulation loop)
# ─────────────────────────────────────────────

def check_and_send_threshold_alert(
    supabase,
    engine_db_id: str,
    engine_display_id: str,   # human-readable e.g. "01"
    pred_rul: float,
    warn_thresh: int,
    crit_thresh: int,
) -> None:
    """
    Call this every prediction cycle. Sends an email only when the engine
    first crosses a threshold (deduplication prevents repeated alerts).
    Runs in the calling thread (simulation loop) so it's non-blocking for
    other engines but does add the SMTP latency to that engine's tick.
    To avoid this, run in a thread: threading.Thread(target=..., daemon=True).start()
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

    # ── Insert into alert_logs table ──
    try:
        supabase.table("alert_logs").insert({
            "engine_id": engine_db_id,
            "severity": level,
            "status": "active",
            "triggered_at": now.isoformat(),
        }).execute()
        print(f"[EMAIL] Logged alert to alert_logs: engine={engine_db_id} severity={level}")
    except Exception:
        print(f"[EMAIL][ERROR] Failed to insert alert_logs:\n{traceback.format_exc()}")

    display_id = f"Engine-{str(engine_display_id).zfill(2)}"
    subject = (
        f"🚨 Critical RUL Alert — {display_id}"
        if level == "critical"
        else f"⚠️ RUL Warning — {display_id}"
    )
    html = _threshold_alert_html(
        engine_display_id=str(engine_display_id).zfill(2),
        level=level,
        pred_rul=pred_rul,
        threshold=threshold,
        engine_db_id=engine_db_id,
        triggered_at=now,
    )

    def _send():
        _send_email(subject, html)

    threading.Thread(target=_send, daemon=True, name=f"email-alert-{engine_db_id}").start()


# ─────────────────────────────────────────────
#  DAILY REPORT SCHEDULER
# ─────────────────────────────────────────────

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
            summary = _fetch_fleet_summary(supabase)
            date_str = _fmt_date()
            subject  = f"Daily RUL Status Report — {date_str}"
            html     = _daily_report_html(summary)
            _send_email(subject, html)
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
    if not _cfg("EMAIL_SENDER") or not _cfg("EMAIL_PASSWORD") or not _cfg("EMAIL_RECIPIENTS"):
        print("[EMAIL] Notification manager not started — "
              "EMAIL_SENDER / EMAIL_PASSWORD / EMAIL_RECIPIENTS missing from .env")
        return

    # ── Backfill: log alerts for engines in warning/critical with NO alert_logs at all ──
    try:
        eng_resp = supabase.table("engines") \
            .select("id, condition_status") \
            .in_("condition_status", ["warning", "critical"]) \
            .execute()
        for eng in (eng_resp.data or []):
            eid = eng["id"]
            severity = eng["condition_status"]
            # Only backfill if this engine has ZERO alert_logs entries
            existing = supabase.table("alert_logs") \
                .select("id") \
                .eq("engine_id", eid) \
                .limit(1) \
                .execute()
            if not existing.data:
                supabase.table("alert_logs").insert({
                    "engine_id": eid,
                    "severity": severity,
                    "status": "active",
                    "triggered_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
                print(f"[EMAIL] Backfilled alert_log for engine {eid} ({severity})")
    except Exception:
        print(f"[EMAIL][WARN] Alert backfill failed:\n{traceback.format_exc()}")

    hour = int(_cfg("EMAIL_DAILY_HOUR", "9"))
    t = threading.Thread(
        target=_daily_scheduler_loop,
        args=(supabase, hour),
        daemon=True,
        name="email-daily-scheduler",
    )
    t.start()
    print(f"[EMAIL] Notification manager started — daily report at {hour:02d}:00")

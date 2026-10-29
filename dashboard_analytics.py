"""Organization-scoped dashboard summaries using existing alert/job records."""
from collections import Counter
from datetime import datetime, timedelta, timezone

from dash import dcc, html
import plotly.graph_objects as go

from assets import database_integration as db

LOCAL_TZ = timezone(timedelta(hours=8))
JOB_LABELS = {
    "scheduled": "Scheduled",
    "in_progress": "In Progress",
    "completed": "Completed / Pending Verification",
    "follow_up_required": "Follow-up Required",
}


def _all_rows(client, table, columns, filters):
    rows = []
    # Paginate to avoid silently truncating counts at the PostgREST row limit.
    while True:
        page = db.fetch_records(
            client, table, columns, filters=filters,
            order_by=[("id", False)], row_range=(len(rows), len(rows) + 499),
        ).data or []
        rows.extend(page)
        if len(page) < 500:
            return rows


def summarize(alerts, jobs, now=None):
    today = (now or datetime.now(LOCAL_TZ)).astimezone(LOCAL_TZ).date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    counts = {severity: Counter() for severity in ("warning", "critical")}
    for alert in alerts:
        try:
            stamp = datetime.fromisoformat(alert["triggered_at"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            day = stamp.astimezone(LOCAL_TZ).date()
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        severity = (alert.get("severity") or "").lower()
        if day in days and severity in counts:
            counts[severity][day] += 1
    statuses = Counter(job.get("status") for job in jobs)
    return days, counts, statuses


def build_admin_analytics(client, org_id):
    alerts, jobs = [], []
    unavailable = False
    now = datetime.now(LOCAL_TZ)
    try:
        if not client or not org_id:
            raise ValueError("Organization context unavailable")
        engines = _all_rows(client, "engines", "id", [("eq", "organization_id", org_id)])
        engine_ids = [row["id"] for row in engines]
        start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        for index in range(0, len(engine_ids), 100):
            scope = [("in_", "engine_id", engine_ids[index:index + 100])]
            alerts.extend(_all_rows(client, "alert_logs", "id,severity,triggered_at", scope + [
                ("gte", "triggered_at", start.astimezone(timezone.utc).isoformat()),
            ]))
            jobs.extend(_all_rows(client, "maintenance_schedules", "id,status", scope))
    except Exception:
        # Never present a failed or partially fetched query as an accurate zero.
        unavailable = True

    days, counts, statuses = summarize(alerts, jobs, now)
    alert_fig = go.Figure()
    job_fig = go.Figure()
    if not unavailable:
        for severity, color in (("warning", "#ffd93d"), ("critical", "#ff4d4d")):
            alert_fig.add_bar(name=severity.capitalize(), x=[day.isoformat() for day in days],
                              y=[counts[severity][day] for day in days], marker_color=color,
                              hovertemplate="%{x}<br>%{y} alerts<extra>%{fullData.name}</extra>")
        labels = list(JOB_LABELS.values())
        job_fig.add_bar(x=[statuses[key] for key in JOB_LABELS], y=labels, orientation="h",
                        marker_color=["#4a9eff", "#ffd93d", "#a78bfa", "#ff934d"],
                        hovertemplate="%{y}: %{x} jobs<extra></extra>")
        job_fig.update_yaxes(autorange="reversed", automargin=True)
        alert_fig.update_layout(barmode="stack", legend=dict(orientation="h", y=1.2, x=0))
        alert_fig.update_xaxes(type="category", tickvals=[d.isoformat() for d in days],
                              ticktext=[d.strftime("%d %b") for d in days])
        alert_fig.update_yaxes(title="Alerts", rangemode="tozero", dtick=1)
        job_fig.update_xaxes(title="Jobs", rangemode="tozero", dtick=1)
    for fig in (alert_fig, job_fig):
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#dbe8ff"),
                          margin=dict(l=10, r=12, t=30, b=35), autosize=True)
        if unavailable:
            fig.add_annotation(text="Data unavailable. Reload to try again.", x=.5, y=.5,
                               xref="paper", yref="paper", showarrow=False)
            fig.update_xaxes(visible=False)
            fig.update_yaxes(visible=False)
    def chart_section(title, graph_id, figure):
        return html.Div(
            style={"display": "flex", "flexDirection": "column", "minHeight": "0",
                   "minWidth": "0", "overflow": "hidden",
                   "background": "#101a2f", "border": "1px solid rgba(74,158,255,0.3)",
                   "borderRadius": "16px", "padding": "18px"},
            children=[
                html.H3(title, style={"fontSize": "15px", "margin": "0 0 6px", "flexShrink": "0"}),
                html.Div(
                    style={"position": "relative", "flex": "1", "minHeight": "0"},
                    children=dcc.Graph(
                        id=graph_id, figure=figure, responsive=True,
                        config={"displayModeBar": False},
                        style={"position": "absolute", "inset": "0", "height": "100%", "width": "100%"},
                    ),
                ),
            ],
        )

    return html.Div(
        style={"flex": "1", "minWidth": "0", "minHeight": "0", "overflow": "hidden",
               "display": "grid", "gridTemplateRows": "minmax(0, 1fr) minmax(0, 1fr)",
               "gap": "16px"},
        children=[
            chart_section(
                "Alerts Generated — Last 7 Days", "admin-alert-trend", alert_fig,
            ),
            chart_section(
                "Maintenance Job Status", "admin-maintenance-status", job_fig,
            ),
        ],
    )

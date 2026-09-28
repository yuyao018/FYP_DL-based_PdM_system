from assets.schedule_modal import build_schedule_modal
import dash
from dash import dcc, html, Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import json as _json
import io
import base64
from datetime import datetime, timezone, timedelta

# Malaysia Standard Time — UTC+8
_MYT = timezone(timedelta(hours=8))

def _to_myt(dt: datetime) -> datetime:
    """Convert a timezone-aware datetime to MYT (UTC+8)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_MYT)

def _fmt_myt(ts_str: str, fmt: str = "%Y/%m/%d %H:%M") -> str:
    """Parse an ISO timestamp string and format it in MYT."""
    if not ts_str:
        return "—"
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return _to_myt(dt).strftime(fmt)
    except Exception:
        return ts_str[:16]
from assets.components import build_sidebar, build_topbar

#  CONSTANTS — maintenance workflow
MAINT_STATUSES = [
    "maintenance_required",
    "scheduled",
    "in_progress",
    "completed",
    "follow_up_required",
]

MAINT_LABELS = {
    "maintenance_required": "Maintenance Required",
    "scheduled":            "Scheduled",
    "in_progress":          "In Progress",
    "completed":            "Completed",
    "follow_up_required":   "Follow-up Required",
}

MAINT_COLORS = {
    "maintenance_required": "#ff4d4d",
    "scheduled":            "#ffd93d",
    "in_progress":          "#4a9eff",
    "completed":            "#00c875",
    "follow_up_required":   "#c084fc",
}

#  SMALL UI HELPERS
def _label_style():
    return {
        "color": "rgba(168,212,255,0.8)",
        "fontSize": "11px",
        "fontWeight": "600",
        "marginBottom": "5px",
        "letterSpacing": "0.5px",
        "display": "block",
    }

def _input_style():
    return {
        "width": "100%",
        "background": "rgba(13,32,69,0.9)",
        "border": "1px solid rgba(74,158,255,0.25)",
        "borderRadius": "8px",
        "color": "white",
        "padding": "10px 14px",
        "fontSize": "13px",
        "outline": "none",
        "boxSizing": "border-box",
        "fontFamily": "'Segoe UI', sans-serif",
    }

def _section_heading(text):
    return html.Div(text, style={
        "color": "#4a9eff", "fontSize": "11px", "fontWeight": "700",
        "letterSpacing": "1px", "marginBottom": "10px", "marginTop": "6px",
    })

def _detail_row(label, value, value_color="white"):
    return html.Div(
        style={
            "display": "flex", "justifyContent": "space-between",
            "padding": "7px 0", "borderBottom": "1px solid rgba(74,158,255,0.07)",
        },
        children=[
            html.Span(label, style={"color": "#a8d4ff", "fontSize": "13px"}),
            html.Span(str(value), style={"color": value_color, "fontSize": "13px", "fontWeight": "700"}),
        ]
    )


#  SEVERITY BADGE
def severity_badge(severity):
    sev = (severity or "warning").lower()
    if sev == "critical":
        bg, border, color, icon = "rgba(255,80,80,0.13)", "#ff6464", "#ff6464", "⚠"
    elif sev == "warning":
        bg, border, color, icon = "rgba(255,212,59,0.12)", "#ffd43b", "#ffd43b", "!"
    else:
        bg, border, color, icon = "rgba(0,200,100,0.11)", "#00d98b", "#00d98b", "✓"

    return html.Span(
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "gap": "6px",

            # Important — prevent badge stretching
            "width": "fit-content",
            "maxWidth": "fit-content",
            "justifySelf": "start",

            "background": bg,
            "color": color,
            "border": f"1px solid {border}",
            "borderRadius": "6px",
            "padding": "5px 10px",

            "fontSize": "11px",
            "fontWeight": "700",
            "letterSpacing": "0.4px",
            "whiteSpace": "nowrap",
            "lineHeight": "1",
        },
        children=[
            html.Span(
                icon,
                style={
                    "fontSize": "11px",
                    "fontWeight": "900",
                    "lineHeight": "1",
                },
            ),
            html.Span(sev.upper()),
        ],
    )


def maintenance_status_badge(status, alert=None):
    """
    Rich status chip: icon + primary label + secondary description line.
    `alert` is the full alert dict (optional) — used for secondary timestamp text.
    Falls back to plain pill when alert is None (used in detail panel header).
    """
    key   = (status or "maintenance_required").lower().strip()
    color = MAINT_COLORS.get(key, "#a8d4ff")
    label = MAINT_LABELS.get(key, status or "—")

    # ── Icons (Unicode, no external dependency) ──
    icons = {
        "maintenance_required": "⚑",
        "scheduled":            "◷",
        "in_progress":          "◈",
        "completed":            "✔",
        "follow_up_required":   "↺",
    }
    icon = icons.get(key, "•")

    # ── Secondary description ──
    def _fmt(ts_str):
        """Format ISO timestamp → '19 Aug 2026, 10:00' in MYT."""
        if not ts_str:
            return None
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            return _to_myt(dt).strftime("%d %b %Y, %H:%M").lstrip("0")
        except Exception:
            return ts_str[:16]

    if alert is not None:
        if key == "maintenance_required":
            secondary = "No maintenance scheduled"
        elif key == "scheduled":
            sd = alert.get("scheduled_date")
            secondary = sd if sd else "Maintenance scheduled"
        elif key == "in_progress":
            ts = _fmt(alert.get("maintenance_started_at"))
            secondary = f"Started {ts}" if ts else "Maintenance underway"
        elif key == "completed":
            ts = _fmt(alert.get("maintenance_completed_at"))
            secondary = f"Completed {ts}" if ts else "Maintenance completed"
        elif key == "follow_up_required":
            secondary = "Additional maintenance needed"
        else:
            secondary = None
    else:
        # Plain pill mode — no secondary line (used in detail panel)
        secondary = None

    r, g, b = (int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) if color.startswith("#") and len(color) == 7 else (74, 158, 255)

    children = [
        html.Span(icon, style={
            "fontSize": "14px", "lineHeight": "1",
            "color": color, "flexShrink": "0", "marginTop": "1px",
        }),
        html.Div(
            style={"display": "flex", "flexDirection": "column", "minWidth": "0"},
            children=[
                html.Span(label, style={
                    "fontSize": "12px", "fontWeight": "700",
                    "color": color, "lineHeight": "1.2", "whiteSpace": "nowrap",
                }),
                *([] if secondary is None else [
                    html.Span(secondary, style={
                        "fontSize": "10px", "color": "rgba(168,212,255,0.55)",
                        "marginTop": "3px", "lineHeight": "1.2",
                        "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap",
                    })
                ]),
            ]
        ),
    ]

    if secondary is None:
        # Compact pill for detail panel use
        return html.Span(
            children=[
                html.Span(icon, style={"fontSize": "11px"}),
                html.Span(label),
            ],
            style={
                "display": "inline-flex", "alignItems": "center", "gap": "5px",
                "background": f"rgba({r},{g},{b},0.13)",
                "color": color, "border": f"1.5px solid {color}",
                "borderRadius": "6px", "padding": "3px 9px",
                "fontSize": "11px", "fontWeight": "700",
                "letterSpacing": "0.4px", "whiteSpace": "nowrap",
            },
        )

    return html.Div(
        style={
            "display": "inline-flex", "alignItems": "flex-start", "gap": "9px",
            "background": f"rgba({r},{g},{b},0.10)",
            "border": f"1.5px solid rgba({r},{g},{b},0.45)",
            "borderRadius": "10px", "padding": "9px 13px",
            "maxWidth": "240px", "minWidth": "160px",
            "boxSizing": "border-box",
        },
        children=children,
    )


def _hex_rgba(hex_color):
    """Return 'r,g,b' from a #rrggbb string."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    return "74,158,255"

#  SUMMARY CARDS
def summary_card(value, label, color="white", border=None):
    return html.Div(
        style={
            "flex": "1", "textAlign": "center", "padding": "14px 0",
            "borderRight": "1px solid rgba(74,158,255,0.2)" if border != "last" else "none",
            "minWidth": "0",
        },
        children=[
            html.Div(str(value), style={
                "color": color, "fontSize": "24px", "fontWeight": "800", "lineHeight": "1",
            }),
            html.Div(label.upper(), style={
                "color": "rgba(168,212,255,0.6)", "fontSize": "10px",
                "fontWeight": "700", "letterSpacing": "0.8px", "marginTop": "4px",
                "whiteSpace": "nowrap",
            }),
        ]
    )


#  RUL SPARKLINE
def build_rul_sparkline(progression, crit_thresh=30, warn_thresh=62):
    x = list(range(45, 45 + len(progression)))
    y = progression
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(color="#4a9eff", width=1.5),
        name="RUL", hoverinfo="none",
    ))
    x_end   = x[-1] if x else 50
    x_start = x[0]  if x else 45
    fig.add_shape(type="line", x0=x_start, x1=x_end, y0=warn_thresh, y1=warn_thresh,
                  line=dict(color="#ffd93d", width=1, dash="dot"))
    fig.add_shape(type="line", x0=x_start, x1=x_end, y0=crit_thresh, y1=crit_thresh,
                  line=dict(color="#ff4d4d", width=1, dash="dot"))
    fig.add_annotation(x=x_end, y=warn_thresh, text=f"  {warn_thresh}",
                       showarrow=False, font=dict(color="#ffd93d", size=9), xanchor="left")
    fig.add_annotation(x=x_end, y=crit_thresh, text=f"  {crit_thresh}",
                       showarrow=False, font=dict(color="#ff4d4d", size=9), xanchor="left")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=40, t=10, b=28), height=160,
        xaxis=dict(showgrid=False, color="#a8d4ff", tickfont=dict(size=9), zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(74,158,255,0.08)",
                   color="#a8d4ff", tickfont=dict(size=9), zeroline=False,
                   title=dict(text="RUL", font=dict(size=9, color="#a8d4ff"))),
        showlegend=False, hovermode="x",
        hoverlabel=dict(bgcolor="#0d1e3a", bordercolor="rgba(74,158,255,0.4)",
                        font=dict(color="white", size=11)),
    )
    return fig


#  SHAP MINI BARS
def shap_mini_bars(shap_values):
    if not shap_values:
        return []
    max_abs = max(abs(v) for _, v in shap_values) or 1
    rows = []
    for name, val in shap_values:
        pct   = min(100, int(abs(val) / max_abs * 100))
        color = "#ff4d4d" if val < -0.4 else "#7b61ff" if val < -0.2 else "#f5a623" if val < 0 else "#00c875"
        rows.append(html.Div(
            style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "8px"},
            children=[
                html.Span(name, style={"color": "#a8d4ff", "fontSize": "12px", "width": "32px", "flexShrink": "0"}),
                html.Div(
                    style={"flex": "1", "background": "rgba(255,255,255,0.05)",
                           "borderRadius": "4px", "height": "8px"},
                    children=[html.Div(style={"width": f"{pct}%", "height": "100%",
                                              "borderRadius": "4px", "background": color})]
                ),
                html.Span(f"{val:+.2f}", style={"color": color, "fontSize": "12px",
                                                 "fontWeight": "700", "width": "42px",
                                                 "textAlign": "right", "flexShrink": "0"}),
            ]
        ))
    return rows


#  ALERT TABLE ROW
ALERT_TABLE_COLUMNS = "55px minmax(130px,1.6fr) minmax(130px,1.6fr) minmax(60px,0.8fr)"

def _status_button_props(mstatus):
    # Primary blue gradient — schedule / open report actions
    primary = {
        "display": "inline-flex", "alignItems": "center", "gap": "7px",
        "background": "linear-gradient(90deg,#1557b8,#1f7fe8)",
        "color": "white", "border": "none",
        "borderRadius": "8px", "padding": "0 16px",
        "height": "38px", "fontSize": "12px", "fontWeight": "700",
        "cursor": "pointer", "letterSpacing": "0.3px", "whiteSpace": "nowrap",
        "boxShadow": "0 2px 8px rgba(21,87,184,0.35)",
    }
    # Secondary ghost — view / report actions
    secondary = {
        "display": "inline-flex", "alignItems": "center", "gap": "7px",
        "background": "rgba(10,25,50,0.5)",
        "color": "white", "border": "1px solid rgba(74,158,255,0.65)",
        "borderRadius": "8px", "padding": "0 16px",
        "height": "38px", "fontSize": "12px", "fontWeight": "700",
        "cursor": "pointer", "letterSpacing": "0.3px", "whiteSpace": "nowrap",
    }
    # Follow-up purple ghost
    followup = {
        **secondary,
        "border": "1px solid rgba(185,108,255,0.6)",
        "color": "#c084fc",
    }

    s = (mstatus or "maintenance_required").lower().strip()
    icon_cal  = html.Span("◷", style={"fontSize": "13px", "lineHeight": "1"})
    icon_doc  = html.Span("▤", style={"fontSize": "13px", "lineHeight": "1"})

    if s == "maintenance_required":
        return [icon_cal, "Schedule Maintenance"], primary
    elif s == "scheduled":
        return [icon_cal, "View Schedule"], secondary
    elif s == "in_progress":
        return [icon_doc, "Open Report"], secondary
    elif s == "completed":
        return [icon_doc, "View Report"], secondary
    elif s == "follow_up_required":
        return [icon_cal, "Schedule Follow-up"], followup
    return ["—"], {"color": "rgba(168,212,255,0.3)", "fontSize": "12px"}


def alert_table_row(idx, alert, is_selected=False):
    ts      = _to_myt(alert["timestamp"]).strftime("%Y/%m/%d %H:%M")
    if is_selected:
        row_bg = "rgba(25,74,130,0.25)"
        left_border = "4px solid #4a9eff"
    else:
        row_bg = (
            "rgba(7,21,42,0.35)"
            if idx % 2 == 0
            else "rgba(13,32,69,0.22)"
        )
        left_border = "4px solid transparent"

    # RUL colour: red when critical or very low
    rul_val = alert.get("rul", 0)
    rul_color = "#ff6b6b" if (alert.get("severity", "").lower() == "critical" or rul_val <= 30) else "white"

    row_style = {
        "display": "grid",
        "gridTemplateColumns": ALERT_TABLE_COLUMNS,
        "alignItems": "center",
        "padding": "14px 18px",
        "minHeight": "42px",
        "borderLeft": left_border,
        "background": row_bg,
        "borderBottom": "1px solid rgba(74,158,255,0.07)",
        "cursor": "pointer",
        "transition": "background 0.15s ease",
        "boxSizing": "border-box",
    }

    return html.Div(style=row_style, children=[
        # ── Clickable region — # | TIMESTAMP | RUL ──────────────────
        html.Div(
            id={"type": "al-row", "index": idx}, n_clicks=0,
            style={"display": "contents"},
            children=[
                # # column
                html.Div(
                    html.Span(alert["alert_no"],
                              style={"color": "rgba(168,212,255,0.7)", "fontSize": "13px",
                                     "fontWeight": "700"}),
                    style={"display": "flex", "alignItems": "center"},
                ),
                # TIMESTAMP column
                html.Div(
                    style={"display": "flex", "flexDirection": "column",
                           "justifyContent": "center", "gap": "3px"},
                    children=[
                        html.Span(ts, style={"color": "#a8d4ff", "fontSize": "13px",
                                             "lineHeight": "1.4"}),
                    ]
                ),
                # SEVERITY column
                html.Div(
                    style={"display": "flex", "flexDirection": "column",
                           "justifyContent": "center", "gap": "3px"},
                    children=[
                        severity_badge(alert["severity"]),
                    ]
                ),
                # RUL column
                html.Div(
                    style={"display": "flex", "flexDirection": "column",
                           "alignItems": "flex-start", "justifyContent": "center"},
                    children=[
                        html.Span(str(rul_val),
                                  style={"color": rul_color, "fontSize": "16px",
                                         "fontWeight": "800", "lineHeight": "1"}),
                    ]
                ),
            ]
        ),
    ])


#  MAINTENANCE SECTION — inside the right-hand detail panel
def _maintenance_section(alert, report=None):
    """
    Display-only maintenance block.
    """
    mstatus = (alert.get("maintenance_status") or "maintenance_required").lower().strip()
    color   = MAINT_COLORS.get(mstatus, "#a8d4ff")

    header = html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px",
                              "marginBottom": "10px"}, children=[
        _section_heading("MAINTENANCE"),
        maintenance_status_badge(mstatus),
    ])

    rows = [header]

    if mstatus == "maintenance_required":
        rows.append(_detail_row("Scheduled Maintenance", "Not Scheduled", "#a8d4ff"))

    elif mstatus == "scheduled":
        sched_date = alert.get("scheduled_date") or "—"
        assigned   = alert.get("assigned_user") or "—"
        rows += [
            _detail_row("Scheduled Date", sched_date, "#ffd93d"),
            _detail_row("Assigned To", assigned, "white"),
        ]

    elif mstatus == "in_progress":
        started = alert.get("maintenance_started_at") or "—"
        if started and started != "—":
            started = _fmt_myt(started)
        rows.append(_detail_row("Started At", started, "#4a9eff"))

    elif mstatus == "completed":
        completed_at = "—"
        if report and report.get("completed_at"):
            completed_at = _fmt_myt(report["completed_at"])
        fault  = (report or {}).get("fault_confirmed", "—").replace("_", " ").title() if report else "—"
        ai_use = (report or {}).get("ai_recommendation_usefulness", "—").replace("_", " ").title() if report else "—"
        rows += [
            _section_heading("MAINTENANCE OUTCOME"),
            _detail_row("Completed At", completed_at, "#00c875"),
            _detail_row("Fault Confirmed", fault, "white"),
            _detail_row("AI Rec. Usefulness", ai_use, "white"),
            _detail_row("Follow-up Required", "No", "#00c875"),
        ]

    elif mstatus == "follow_up_required":
        reason    = (report or {}).get("follow_up_reason") or "—" if report else "—"
        prev_date = "—"
        if report and report.get("completed_at"):
            prev_date = _fmt_myt(report["completed_at"])
        rows += [
            _section_heading("MAINTENANCE OUTCOME"),
            _detail_row("Reason", reason, "#c084fc"),
            _detail_row("Previous Maintenance", prev_date, "white"),
        ]

    return html.Div(
        style={
            "background": "rgba(10,20,45,0.4)", "borderRadius": "8px",
            "border": f"1px solid {color}33",
            "padding": "14px", "marginTop": "18px",
        },
        children=rows,
    )


#  ALERT DETAIL PANEL (right-hand panel)
def _diag_chips(degradation_type, rul, severity):
    sev = (severity or "warning").lower()
    if sev == "critical":
        s_bg, s_c, s_b = "rgba(255,77,77,0.18)", "#ff4d4d", "rgba(255,77,77,0.5)"
    elif sev == "warning":
        s_bg, s_c, s_b = "rgba(255,217,61,0.15)", "#ffd93d", "rgba(255,217,61,0.45)"
    else:
        s_bg, s_c, s_b = "rgba(0,200,117,0.15)", "#00c875", "rgba(0,200,117,0.4)"

    def chip(text, bg, color, border):
        return html.Span(text, style={
            "background": bg, "color": color, "border": f"1px solid {border}",
            "borderRadius": "5px", "padding": "2px 8px", "fontSize": "10px",
            "fontWeight": "700", "letterSpacing": "0.5px", "whiteSpace": "nowrap",
        })

    return [
        html.Div((degradation_type or "Unknown Pattern").upper(), style={
            "color": "white", "fontSize": "13px", "fontWeight": "800",
            "marginBottom": "7px", "letterSpacing": "0.3px",
        }),
        html.Div(style={"display": "flex", "gap": "6px", "flexWrap": "wrap", "alignItems": "center"},
                 children=[
                     chip(sev.upper(), s_bg, s_c, s_b),
                     chip(f"RUL: {rul} cycles" if rul is not None else "RUL: —",
                          "rgba(123,97,255,0.15)", "#b09aff", "rgba(123,97,255,0.4)"),
                 ]),
    ]


def alert_detail_panel(alert, report=None):
    ts = _to_myt(alert["timestamp"]).strftime("%Y/%m/%d %H:%M")
    children = [
        # Header
        html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "6px"},
                 children=[
                     html.H3(f"ALERT #{alert['alert_no']}",
                             style={"margin": "0", "color": "white", "fontSize": "18px", "fontWeight": "800"}),
                 ]),
        html.Div(style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "16px"},
                 children=[
                     html.Span(ts, style={"color": "#a8d4ff", "fontSize": "13px"}),
                     severity_badge(alert["severity"]),
                 ]),

        # RUL Progression
        _section_heading("RUL PROGRESSION"),
        html.Div(
            style={"background": "rgba(10,20,45,0.5)", "borderRadius": "10px",
                   "border": "1px solid rgba(74,158,255,0.1)", "marginBottom": "18px",
                   "position": "relative", "overflow": "hidden"},
            children=[dcc.Graph(
                id="al-rul-chart", clear_on_unhover=True,
                figure=build_rul_sparkline(
                    alert["rul_progression"],
                    crit_thresh=alert.get("crit_thresh", 30),
                    warn_thresh=alert.get("warn_thresh", 62),
                ),
                config={"displayModeBar": False},
                style={"height": "160px"},
            ),
                html.Div(id="al-rul-vline", className="al-rul-vline", style={"display": "none"}),
                html.Div(id="al-rul-tooltip", className="al-rul-tooltip", style={"display": "none"}),
            ]
        ),

        # Alert details
        _section_heading("ALERT DETAILS"),
        _detail_row("Alert ID", alert.get("alert_id")),
        _detail_row("Predicted RUL", f"{alert['rul']} cycles", "#ff6b6b"),
        _detail_row("Degradation Pattern", alert.get("degradation_pattern") or "—", "white"),
    ]

    # AI Analysis
    if alert.get("llm_explanation"):
        children += [
            html.Div(style={"marginBottom": "18px", "marginTop": "14px"}, children=[
                _section_heading("AI ANALYSIS"),
                html.Div(
                    style={"background": "rgba(10,20,45,0.55)", "border": "1px solid rgba(74,158,255,0.2)",
                           "borderRadius": "8px", "padding": "10px 12px", "marginBottom": "8px"},
                    children=_diag_chips(
                        alert.get("degradation_pattern"), alert.get("rul"), alert.get("severity")
                    ),
                ),
                html.Div(
                    style={"background": "rgba(10,20,45,0.4)", "borderRadius": "8px",
                           "padding": "10px 12px", "border": "1px solid rgba(74,158,255,0.1)",
                           "maxHeight": "180px", "overflowY": "auto"},
                    children=dcc.Markdown(alert.get("llm_explanation", ""), className="ai-explanation-md"),
                ),
            ]),
        ]

    # SHAP
    if alert.get("shap"):
        children += [
            _section_heading("SHAP AT TRIGGER"),
            html.Div(shap_mini_bars(alert["shap"]), style={"marginBottom": "14px"}),
        ]

    # Maintenance section
    children.append(_maintenance_section(alert, report=report))

    return html.Div(
        style={
            "background": "transparent", "border": "1px solid rgba(74,158,255,0.18)",
            "borderRadius": "0px", "padding": "22px", "height": "100%", "overflowY": "auto",
        },
        children=children,
    )

#  SCHEDULE MAINTENANCE MODAL (inline in Alert Log)
def _report_modal():
    """
    Full-screen overlay containing the maintenance report form.
    Read-only system info + editable technician fields.
    Shown for both In Progress (editable) and Completed/Follow-up (read-only view).
    """
    ls  = _label_style()
    is_ = _input_style()
    ta  = {**is_, "height": "90px", "resize": "vertical"}

    radio_opts_fault = [
        {"label": " Yes",          "value": "yes"},
        {"label": " No",           "value": "no"},
        {"label": " Inconclusive", "value": "inconclusive"},
    ]
    radio_opts_ai = [
        {"label": " Useful",           "value": "useful"},
        {"label": " Partially Useful", "value": "partially_useful"},
        {"label": " Not Useful",       "value": "not_useful"},
    ]

    section_card = lambda children: html.Div(
        style={"background": "rgba(10,22,40,0.55)", "border": "1px solid rgba(74,158,255,0.12)",
               "borderRadius": "10px", "padding": "16px 18px", "marginBottom": "16px"},
        children=children,
    )

    return html.Div(
        id="al-report-modal-overlay",
        style={"display": "none", "position": "fixed", "top": "0", "left": "0",
               "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.88)",
               "zIndex": "1300", "alignItems": "flex-start", "justifyContent": "center",
               "overflowY": "auto", "paddingTop": "20px", "paddingBottom": "40px"},
        children=[html.Div(
            style={"background": "linear-gradient(135deg,#0d1e3a 0%,#071530 100%)",
                   "border": "1px solid rgba(74,158,255,0.25)", "borderRadius": "16px",
                   "padding": "28px 32px", "width": "780px", "maxWidth": "96vw",
                   "boxShadow": "0 24px 72px rgba(0,0,0,0.65)", "position": "relative"},
            children=[
                # Close button
                html.Span("×", id="al-report-modal-close", n_clicks=0,
                          style={"position": "absolute", "top": "20px", "right": "24px",
                                 "color": "rgba(168,212,255,0.5)", "fontSize": "26px",
                                 "cursor": "pointer", "lineHeight": "1", "zIndex": "10"}),

                # REPORT HEADER (read-only, populated by callback)
                html.Div(id="al-report-header", style={"marginBottom": "22px"}),

                # A. PREDICTIVE ANALYSIS (read-only)
                section_card([
                    html.Div("A. PREDICTIVE ANALYSIS", style={
                        "color": "#4a9eff", "fontSize": "12px", "fontWeight": "800",
                        "letterSpacing": "1px", "marginBottom": "12px",
                    }),
                    html.Div(id="al-report-analysis-section"),
                ]),

                # B. MAINTENANCE WORK (editable)
                section_card([
                    html.Div("B. MAINTENANCE WORK", style={
                        "color": "#4a9eff", "fontSize": "12px", "fontWeight": "800",
                        "letterSpacing": "1px", "marginBottom": "12px",
                    }),
                    html.Div(style={"marginBottom": "12px"}, children=[
                        html.Label("MAINTENANCE ACTIONS PERFORMED", style=ls),
                        dcc.Textarea(id="al-report-actions", placeholder="Describe actions taken…", style=ta),
                    ]),
                    html.Div(style={"marginBottom": "12px"}, children=[
                        html.Label("COMPONENTS INSPECTED", style=ls),
                        dcc.Textarea(id="al-report-components-inspected", placeholder="List components inspected…", style=ta),
                    ]),
                    html.Div(style={"marginBottom": "12px"}, children=[
                        html.Label("COMPONENTS REPAIRED / REPLACED", style=ls),
                        dcc.Textarea(id="al-report-components-repaired", placeholder="List components repaired or replaced…", style=ta),
                    ]),
                    html.Div(children=[
                        html.Label("INSPECTION FINDINGS", style=ls),
                        dcc.Textarea(id="al-report-findings", placeholder="Record inspection findings…", style=ta),
                    ]),
                ]),

                # C. PREDICTION FEEDBACK
                section_card([
                    html.Div("C. PREDICTION FEEDBACK", style={
                        "color": "#4a9eff", "fontSize": "12px", "fontWeight": "800",
                        "letterSpacing": "1px", "marginBottom": "12px",
                    }),
                    html.Div(style={"marginBottom": "14px"}, children=[
                        html.Label("WAS THE PREDICTED DEGRADATION / FAULT CONFIRMED?", style=ls),
                        dcc.RadioItems(id="al-report-fault-confirmed",
                                       options=radio_opts_fault,
                                       value=None,
                                       inline=True,
                                       inputStyle={"marginRight": "5px"},
                                       labelStyle={"marginRight": "20px", "color": "#a8d4ff",
                                                   "fontSize": "13px", "cursor": "pointer"}),
                    ]),
                    html.Div(style={"marginBottom": "14px"}, children=[
                        html.Label("WAS THE AI MAINTENANCE RECOMMENDATION USEFUL?", style=ls),
                        dcc.RadioItems(id="al-report-ai-usefulness",
                                       options=radio_opts_ai,
                                       value=None,
                                       inline=True,
                                       inputStyle={"marginRight": "5px"},
                                       labelStyle={"marginRight": "20px", "color": "#a8d4ff",
                                                   "fontSize": "13px", "cursor": "pointer"}),
                    ]),
                    html.Div(children=[
                        html.Label("TECHNICIAN NOTES", style=ls),
                        dcc.Textarea(id="al-report-technician-notes",
                                     placeholder="Additional notes…",
                                     style=ta),
                    ]),
                ]),

                # D. MAINTENANCE OUTCOME
                section_card([
                    html.Div("D. MAINTENANCE OUTCOME", style={
                        "color": "#4a9eff", "fontSize": "12px", "fontWeight": "800",
                        "letterSpacing": "1px", "marginBottom": "12px",
                    }),
                    # Follow-up reason (shown only when follow-up is selected)
                    html.Div(id="al-report-followup-reason-row",
                             style={"marginBottom": "14px", "display": "none"},
                             children=[
                                 html.Label("REASON FOR FOLLOW-UP", style=ls),
                                 dcc.Textarea(id="al-report-followup-reason",
                                              placeholder="Describe why follow-up maintenance is required…",
                                              style=ta),
                             ]),
                    html.Div(id="al-report-msg",
                             style={"minHeight": "18px", "marginBottom": "8px"}),
                    # Action buttons
                    html.Div(style={"display": "flex", "gap": "10px", "flexWrap": "wrap"},
                             children=[
                                 html.Button("Save Progress",
                                             id="al-report-save-btn", n_clicks=0,
                                             style={"background": "rgba(74,158,255,0.12)",
                                                    "border": "1px solid rgba(74,158,255,0.4)",
                                                    "borderRadius": "8px", "color": "#7ab8ff",
                                                    "fontSize": "13px", "fontWeight": "700",
                                                    "padding": "9px 22px", "cursor": "pointer"}),
                                 html.Button("Complete Maintenance",
                                             id="al-report-complete-btn", n_clicks=0,
                                             style={"background": "rgba(0,200,117,0.15)",
                                                    "border": "1px solid rgba(0,200,117,0.4)",
                                                    "borderRadius": "8px", "color": "#00c875",
                                                    "fontSize": "13px", "fontWeight": "700",
                                                    "padding": "9px 22px", "cursor": "pointer"}),
                                 html.Button("Follow-up Required",
                                             id="al-report-followup-btn", n_clicks=0,
                                             style={"background": "rgba(192,132,252,0.12)",
                                                    "border": "1px solid rgba(192,132,252,0.4)",
                                                    "borderRadius": "8px", "color": "#c084fc",
                                                    "fontSize": "13px", "fontWeight": "700",
                                                    "padding": "9px 22px", "cursor": "pointer"}),
                             ]),
                ]),

                # Hidden store: current alert_id being reported
                dcc.Store(id="al-report-schedule-id-store", data=None),
                dcc.Store(id="al-report-id-store", data=None),
                dcc.Store(id="al-report-readonly-store", data=False),
            ]
        )]
    )


#  CONFIRMATION MODAL (used before completing maintenance)
def _confirm_modal():
    return html.Div(
        id="al-confirm-modal-overlay",
        style={"display": "none", "position": "fixed", "top": "0", "left": "0",
               "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.85)",
               "zIndex": "1500", "alignItems": "center", "justifyContent": "center"},
        children=[html.Div(
            style={"background": "linear-gradient(135deg,#0d1e3a,#071530)",
                   "border": "1px solid rgba(74,158,255,0.25)", "borderRadius": "14px",
                   "padding": "28px 32px", "width": "400px", "maxWidth": "92vw",
                   "boxShadow": "0 20px 60px rgba(0,0,0,0.6)"},
            children=[
                html.H3(id="al-confirm-modal-title",
                        children="Complete Maintenance?",
                        style={"margin": "0 0 12px", "color": "white",
                               "fontSize": "16px", "fontWeight": "700"}),
                html.P(id="al-confirm-modal-body",
                       children="This will finalise the report and cannot be undone.",
                       style={"color": "#a8d4ff", "fontSize": "13px", "marginBottom": "22px"}),
                html.Div(style={"display": "flex", "justifyContent": "flex-end", "gap": "10px"},
                         children=[
                             html.Button("Cancel", id="al-confirm-cancel-btn", n_clicks=0,
                                         style={"background": "rgba(74,158,255,0.06)",
                                                "border": "1px solid rgba(74,158,255,0.25)",
                                                "borderRadius": "8px", "color": "rgba(168,212,255,0.7)",
                                                "fontSize": "13px", "fontWeight": "600",
                                                "padding": "9px 20px", "cursor": "pointer"}),
                             html.Button("Confirm", id="al-confirm-ok-btn", n_clicks=0,
                                         style={"background": "rgba(0,200,117,0.15)",
                                                "border": "1px solid rgba(0,200,117,0.4)",
                                                "borderRadius": "8px", "color": "#00c875",
                                                "fontSize": "13px", "fontWeight": "700",
                                                "padding": "9px 22px", "cursor": "pointer"}),
                         ]),
            ]
        )]
    )


#  ENGINE STATUS BAR — right side of the engine title header
def _engine_status_bar_contents(alerts, current_schedule=None):
    """
    Returns a 3-tuple: (badge_children, btn_children, btn_style).

    NOTE: this used to return a flat list of components (badge + a freshly-built
    html.Button) that replaced the whole "al-engine-status-bar" Div's children on
    every update. That recreated the Button component each time, which resets its
    n_clicks to 0 — Dash sees that as a genuine click event and re-fires the
    callback that opens the schedule/report modal, making the modal look like it
    "pops back up" right after you confirm/save. Now the badge and button are
    separate, STATIC-id components in the layout, and callers update their
    children/style in place instead of recreating them.
    """
    if current_schedule:
        mstatus = (
            current_schedule.get("status")
            or "scheduled"
        ).lower().strip()

        status_data = {
            "scheduled_date":
                current_schedule.get("scheduled_date"),
            "maintenance_started_at":
                current_schedule.get("started_at"),
            "maintenance_completed_at":
                current_schedule.get("completed_at"),
        }

        badge = [maintenance_status_badge(mstatus, alert=status_data)]
        btn_children, btn_style = _status_button_props(mstatus)
        return badge, btn_children, btn_style

    if alerts:
        # Derive the current schedule from the first alert's resolved schedule info
        first = alerts[0]
        derived_status = (first.get("maintenance_status") or "maintenance_required").lower().strip()
        badge = [maintenance_status_badge(
            derived_status,
            alert={
                "scheduled_date":           first.get("scheduled_date"),
                "maintenance_started_at":   first.get("maintenance_started_at"),
                "maintenance_completed_at": first.get("maintenance_completed_at"),
            }
        )]
        btn_children, btn_style = _status_button_props(derived_status)
        return badge, btn_children, btn_style

    return [], ["—"], {"color": "rgba(168,212,255,0.3)", "fontSize": "12px"}

#  MAIN TABLE + LAYOUT BODY
def build_alert_log_body(engine_id="—", alerts=None, selected_idx=0,
                         org_users=None, role="user", current_user_label="You (logged-in user)"):
    if alerts is None:
        alerts = []

    selected_idx  = max(0, min(selected_idx, len(alerts) - 1)) if alerts else 0
    selected_alert = alerts[selected_idx] if alerts else None

    _badge0, _btn_children0, _btn_style0 = _engine_status_bar_contents(alerts)

    return [
        # Engine title bar — left: name, right: current maintenance status + action
        html.Div(
            id="al-engine-header-bar",
            style={
                "display": "flex", "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "18px 22px 16px",
                "borderBottom": "1px solid rgba(74,158,255,0.10)",
                "flexShrink": "0",
            },
            children=[
                # Left — engine name
                html.H2(f"ENGINE-{engine_id}",
                        style={"margin": "0", "color": "white",
                               "fontSize": "20px", "fontWeight": "800",
                               "letterSpacing": "0.5px"}),
                # Right — maintenance status chip + action button
                # NOTE: badge and button are separate STATIC-id children so that
                # callbacks can update them in place (see _engine_status_bar_contents
                # docstring) instead of rebuilding this whole Div's children.
                html.Div(
                    id="al-engine-status-bar",
                    style={"display": "flex", "alignItems": "center", "gap": "12px"},
                    children=[
                        html.Div(id="al-engine-status-badge", children=_badge0),
                        html.Button(
                            id="al-engine-action-btn",
                            n_clicks=0,
                            children=_btn_children0,
                            style=_btn_style0,
                        ),
                    ],
                ),
            ],
        ),

        # Table + detail panel
        html.Div(
            style={"display": "flex", "gap": "0", "flex": "1", "minHeight": "0"},
            children=[

                # ── Left: alert table ──────────────────────────────────
                html.Div(
                    style={
                        "flex": "1.45", "minWidth": "0",
                        "background": "rgba(5,18,38,0.25)",
                        "border": "1px solid rgba(74,158,255,0.12)",
                        "borderRight": "2px solid rgba(74,158,255,0.5)",
                        "borderRadius": "0",          # flush left edge; right divider takes precedence
                        "display": "flex", "flexDirection": "column", "overflow": "hidden",
                    },
                    children=[
                        # Filter bar
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "gap": "10px",
                                   "padding": "12px 18px",
                                   "borderBottom": "1px solid rgba(74,158,255,0.12)",
                                   "background": "rgba(7,21,42,0.4)"},
                            children=[
                                # Search
                                html.Div(
                                    style={"flex": "1", "display": "flex", "alignItems": "center",
                                           "background": "rgba(10,20,45,0.6)",
                                           "border": "1px solid rgba(74,158,255,0.25)",
                                           "borderRadius": "6px", "padding": "0 10px"},
                                    children=[
                                        html.Span("🔍", style={"fontSize": "12px", "marginRight": "6px",
                                                                "opacity": "0.5"}),
                                        dcc.Input(id="alert-search-input", type="text",
                                                  placeholder="Search alerts…", debounce=True,
                                                  style={"background": "transparent", "border": "none",
                                                         "color": "white", "fontSize": "12px",
                                                         "outline": "none", "width": "100%",
                                                         "padding": "7px 0"}),
                                    ]
                                ),
                                # Severity filter
                                html.Div(style={"width": "135px",
                                                "border": "1px solid rgba(74,158,255,0.15)",
                                                "borderRadius": "6px"},
                                         children=[dcc.Dropdown(
                                             id="alert-severity-filter",
                                             options=[
                                                 {"label": "All Severity", "value": "all"},
                                                 {"label": "Warning",      "value": "warning"},
                                                 {"label": "Critical",     "value": "critical"},
                                             ],
                                             value="all", clearable=False, searchable=False,
                                             className="dark-dropdown",
                                             style={"backgroundColor": "transparent", "border": "none",
                                                    "fontSize": "12px"},
                                         )]),
                                # Status filter
                                html.Div(style={"width": "168px",
                                                "border": "1px solid rgba(74,158,255,0.15)",
                                                "borderRadius": "6px"},
                                         children=[dcc.Dropdown(
                                             id="alert-status-filter",
                                             options=[
                                                 {"label": "All Status",          "value": "all"},
                                                 {"label": "Maintenance Required","value": "maintenance_required"},
                                                 {"label": "Scheduled",           "value": "scheduled"},
                                                 {"label": "In Progress",         "value": "in_progress"},
                                                 {"label": "Completed",           "value": "completed"},
                                                 {"label": "Follow-up Required",  "value": "follow_up_required"},
                                             ],
                                             value="all", clearable=False, searchable=False,
                                             className="dark-dropdown",
                                             style={"backgroundColor": "transparent", "border": "none",
                                                    "fontSize": "12px"},
                                         )]),
                            ]
                        ),
                        # Table header
                        html.Div(
                            style={
                                "display": "grid",
                                "gridTemplateColumns": ALERT_TABLE_COLUMNS,
                                "padding": "12px 18px",
                                "borderBottom": "2px solid rgba(74,158,255,0.35)",
                                "background": "rgba(7,21,42,0.55)",
                                "alignItems": "center",
                                "minHeight": "46px",
                            },
                            children=[
                                html.Span("#", style={
                                    "color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                    "fontWeight": "700", "letterSpacing": "0.6px",
                                }),
                                html.Span("TIMESTAMP", style={
                                    "color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                    "fontWeight": "700", "letterSpacing": "0.6px",
                                }),
                                html.Span("SEVERITY", style={
                                    "color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                    "fontWeight": "700", "letterSpacing": "0.6px",
                                }),
                                html.Div(style={"display": "flex", "flexDirection": "column",
                                                "gap": "1px"}, children=[
                                    html.Span("RUL", style={
                                        "color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                        "fontWeight": "700", "letterSpacing": "0.6px",
                                    }),
                                    html.Span("(cycles)", style={
                                        "color": "rgba(168,212,255,0.32)", "fontSize": "10px",
                                        "fontWeight": "600", "letterSpacing": "0.3px",
                                    }),
                                ]),
                            ]
                        ),
                        # Table body
                        html.Div(
                            id="alert-table-body",
                            style={"overflowY": "auto", "flex": "1"},
                            children=[
                                alert_table_row(i, a, is_selected=(i == selected_idx))
                                for i, a in enumerate(alerts)
                            ]
                        ),
                    ]
                ),

                # ── Right: detail panel ────────────────────────────────
                html.Div(
                    style={"flex": "1", "minWidth": "0", "display": "flex",
                           "flexDirection": "column"},
                    children=[
                        html.Div(
                            id="alert-detail-container",
                            style={"flex": "1", "minHeight": "0", "overflowY": "auto"},
                            children=[alert_detail_panel(selected_alert)] if selected_alert else [
                                html.Div("No alerts to display.",
                                         style={"color": "rgba(255,255,255,0.5)",
                                                "textAlign": "center", "padding": "60px 0"})
                            ]
                        ),
                    ]
                ),
            ]
        ),

        # ── Stores ────────────────────────────────────────────────────
        dcc.Store(id="alerts-data", data=[
            {**a, "timestamp": a["timestamp"].isoformat()} for a in alerts
        ]),
        dcc.Store(id="selected-alert-idx", data=selected_idx),
        # Stores used by modals
        dcc.Store(id="al-modal-trigger-store", data=None),  # "schedule"|"followup"|"view"
        dcc.Store(id="al-sched-org-users-store", data=org_users or []),
        dcc.Store(id="al-sched-role-store", data=role or "user"),
        dcc.Store(id="al-sched-current-user-label-store", data=current_user_label),
        dcc.Store(id="al-sched-schedule-db-id-store", data=None),  # schedule id being viewed/edited

        # Modals (always rendered in DOM)
        build_schedule_modal(),
        _report_modal(),
        _confirm_modal(),

        # Download component
        dcc.Download(id="al-pdf-download"),
    ]


#  PAGE LAYOUT ENTRY POINT
def create_alert_log_layout(supabase=None, engine_db_id=None,
                            org_id=None, role=None, user_id=None,
                            username=None, first_name=None, last_name=None):
    engine_id = "—"
    alerts = []
    org_users = []   # [{"label": "Name", "value": "user_id"}, ...]
    current_user_label = "You (logged-in user)"

    # Build display name for the logged-in user
    if first_name or last_name:
        current_user_label = f"{first_name or ''} {last_name or ''}".strip()
    elif username:
        current_user_label = username

    # Fetch org users for admin assignee dropdown
    if supabase and role == "admin" and org_id:
        try:
            u_resp = supabase.table("users") \
                .select("id,username,first_name,last_name") \
                .eq("organization_id", org_id) \
                .eq("is_deleted", False) \
                .execute()
            for u in (u_resp.data or []):
                first = u.get("first_name") or ""
                last  = u.get("last_name")  or ""
                name  = f"{first} {last}".strip() or u.get("username") or str(u["id"])[:8]
                org_users.append({"label": name, "value": str(u["id"])})
        except Exception as _e:
            print(f"[ALERT] fetch org users: {_e}")

    try:
        if supabase:
            # Fetch thresholds
            warn_thresh, crit_thresh = 62, 30
            try:
                t_resp = supabase.table("alert_thresholds") \
                    .select("warning_threshold,critical_threshold") \
                    .order("updated_at", desc=True).limit(1).execute()
                if t_resp.data:
                    warn_thresh = int(t_resp.data[0].get("warning_threshold", 62))
                    crit_thresh = int(t_resp.data[0].get("critical_threshold", 30))
            except Exception:
                pass

            # Fetch alert_logs — select only columns that exist in the DB.
            # All maintenance state lives in maintenance_schedules, not alert_logs.
            query = supabase.table("alert_logs").select(
                "id, engine_id, triggered_at, severity, predicted_rul, trigger_cycle"
            )
            if engine_db_id:
                query = query.eq("engine_id", engine_db_id)
                logs_resp = query.order("triggered_at", desc=True).execute()
                logs = logs_resp.data or []
            elif org_id:
                # Scope to engines belonging to this org
                try:
                    eng_scope_resp = supabase.table("engines").select("id").eq("organization_id", org_id).eq("is_deleted", False).execute()
                    org_engine_ids = [e["id"] for e in (eng_scope_resp.data or [])]
                except Exception:
                    org_engine_ids = []
                if org_engine_ids:
                    query = query.in_("engine_id", org_engine_ids)
                    logs_resp = query.order("triggered_at", desc=True).execute()
                    logs = logs_resp.data or []
                else:
                    # Org has no engines — nothing to show
                    logs = []
            else:
                # No engine and no org — fetch all (dev/standalone mode)
                logs_resp = query.order("triggered_at", desc=True).execute()
                logs = logs_resp.data or []

            # Collect engine IDs referenced
            engine_ids = list({log["engine_id"] for log in logs if log.get("engine_id")})
            engines_lookup = {}
            if engine_ids:
                eng_resp = supabase.table("engines") \
                    .select("id,engine_id,degradation_type,llm_explanation") \
                    .in_("id", engine_ids).execute()
                for e in (eng_resp.data or []):
                    engines_lookup[e["id"]] = e

            if engine_db_id and engine_db_id in engines_lookup:
                engine_id = str(engines_lookup[engine_db_id].get("engine_id", "—")).zfill(2)
            elif engines_lookup:
                engine_id = str(next(iter(engines_lookup.values())).get("engine_id", "—")).zfill(2)


            # Fetch the active maintenance schedule per engine.
            schedules_by_engine  = {}   # engine_id → schedule row
            schedules_by_id      = {}   # schedule_id → schedule row
            reports_by_schedule  = {}   # schedule_id → report row

            if engine_ids:
                try:
                    sched_resp = (
                        supabase.table("maintenance_schedules")
                        .select(
                            "id,engine_id,scheduled_date,created_by,status,"
                            "started_at,completed_at"
                        )
                        .in_("engine_id", engine_ids)
                        .order("created_at", desc=True)
                        .execute()
                    )
                    # Keep the most-recent schedule per engine
                    for s in (sched_resp.data or []):
                        eid = s.get("engine_id")
                        if eid and eid not in schedules_by_engine:
                            schedules_by_engine[eid] = s
                        if s.get("id"):
                            schedules_by_id[s["id"]] = s
                except Exception as e:
                    print(f"[ALERT] schedules fetch: {e}")

            schedule_ids = list(schedules_by_id.keys())

            if schedule_ids:
                try:
                    rpt_resp = (
                        supabase.table("maintenance_reports")
                        .select(
                            "id,maintenance_schedule_id,"
                            "fault_confirmed,ai_recommendation_usefulness,"
                            "follow_up_reason,completed_at,outcome,user_id"
                        )
                        .in_("maintenance_schedule_id", schedule_ids)
                        .order("created_at", desc=True)
                        .execute()
                    )
                    for r in (rpt_resp.data or []):
                        sid = r.get("maintenance_schedule_id")
                        if sid and sid not in reports_by_schedule:
                            reports_by_schedule[sid] = r
                except Exception as e:
                    print(f"[ALERT] reports fetch: {e}")

            # Build alert dicts
            for i, log in enumerate(logs):
                eng = engines_lookup.get(log.get("engine_id"), {})
                severity = (log.get("severity") or "warning").lower().strip()
                if severity not in ("warning", "critical"):
                    severity = "warning"

                triggered_at = log.get("triggered_at", "")
                try:
                    timestamp = datetime.fromisoformat(triggered_at.replace("Z", "+00:00"))
                except Exception:
                    timestamp = datetime.now(timezone.utc)

                snapshot_rul    = log.get("predicted_rul")
                snapshot_cycle  = log.get("trigger_cycle")
                alert_engine_id = log.get("engine_id")

                # Resolve schedule for this engine (one schedule per engine)
                sched_info      = schedules_by_engine.get(alert_engine_id, {})
                maint_sched_id  = sched_info.get("id")
                maint_started   = sched_info.get("started_at")
                maint_completed = sched_info.get("completed_at")

                # maintenance_status comes entirely from the schedule row
                maint_status = (sched_info.get("status") or "maintenance_required").lower().strip()

                # Scheduled date + user from linked schedule
                sched_date_v = sched_info.get("scheduled_date", "")
                assigned_uid = sched_info.get("created_by", "")

                # RUL progression
                rul_progression = []
                alert_rul = 0
                try:
                    pred_resp = supabase.table("rul_predictions") \
                        .select("cycle,predicted_rul") \
                        .eq("engine_id", alert_engine_id) \
                        .order("cycle", desc=False).execute()
                    all_preds = pred_resp.data or []
                    if snapshot_cycle is not None:
                        preds = [r for r in all_preds
                                 if r.get("cycle") is not None
                                 and int(r["cycle"]) <= int(snapshot_cycle)]
                    else:
                        preds = all_preds
                    rul_progression = [float(r["predicted_rul"]) for r in preds
                                       if r.get("predicted_rul") is not None]
                except Exception:
                    pass

                if snapshot_rul is not None:
                    alert_rul = int(round(float(snapshot_rul)))
                elif rul_progression:
                    alert_rul = int(round(rul_progression[-1]))
                if not rul_progression:
                    rul_progression = [alert_rul] if alert_rul else [0]

                report = reports_by_schedule.get(maint_sched_id)

                alerts.append({
                    "alert_no":              str(i + 1).zfill(2),
                    "alert_id":              log.get("id"),
                    "engine_id":             alert_engine_id,
                    "timestamp":             timestamp,
                    "severity":              severity,
                    "rul":                   alert_rul,
                    "degradation_pattern":   eng.get("degradation_type") or "Unknown",
                    "llm_explanation":       eng.get("llm_explanation") or "",
                    "shap":                  [],
                    "rul_progression":       rul_progression,
                    "warn_thresh":           warn_thresh,
                    "crit_thresh":           crit_thresh,
                    "maintenance_status":    maint_status,
                    "maintenance_schedule_id": maint_sched_id,
                    "maintenance_started_at":  maint_started,
                    "maintenance_completed_at": maint_completed,
                    "scheduled_date":        sched_date_v,
                    "assigned_user":         assigned_uid,
                    "report":                report,
                })

    except Exception:
        import traceback
        print(f"[ERROR] alert log fetch:\n{traceback.format_exc()}")

    return html.Div(
        style={"height": "100vh", "display": "flex", "flexDirection": "column",
               "fontFamily": "'Segoe UI','Inter',sans-serif",
               "background": "#0a1628", "color": "white", "overflow": "hidden"},
        children=[
            dcc.Location(id="url-alert-log", refresh=False),
            build_topbar(),
            html.Div(
                style={"flex": "1", "display": "flex", "flexDirection": "row",
                       "overflow": "hidden", "minHeight": "0"},
                children=[
                    build_sidebar(active_page="alert", engine_db_id=engine_db_id),
                    html.Div(
                        style={"flex": "1", "overflowY": "auto", "minWidth": "0",
                               "display": "flex", "flexDirection": "column"},
                        children=build_alert_log_body(engine_id=engine_id, alerts=alerts,
                                                       org_users=org_users, role=role,
                                                       current_user_label=current_user_label),
                    ),
                ]
            ),
        ]
    )



#  HELPER — fetch report from DB (or None)
def _fetch_report(supabase, maintenance_schedule_id):
    if not supabase or not maintenance_schedule_id:
        return None

    try:
        resp = (
            supabase.table("maintenance_reports")
            .select("*")
            .eq("maintenance_schedule_id", maintenance_schedule_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        return resp.data[0] if resp.data else None

    except Exception as e:
        print(f"[ALERT] fetch maintenance report: {e}")
        return None


def _fetch_alert_row(supabase, alert_id):
    """Return a single alert_logs row dict."""
    if not supabase or not alert_id:
        return {}
    try:
        resp = supabase.table("alert_logs").select("*").eq("id", alert_id).single().execute()
        return resp.data or {}
    except Exception:
        return {}


def _alert_from_store(a):
    """Re-hydrate an alert dict from the dcc.Store (converts ISO timestamp)."""
    a = dict(a)
    if isinstance(a.get("timestamp"), str):
        a["timestamp"] = datetime.fromisoformat(a["timestamp"])
    return a


#  PDF GENERATION
def _generate_pdf(alert, report):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.enums import TA_LEFT, TA_CENTER

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                  fontSize=16, textColor=colors.HexColor("#1a6fd4"),
                                  spaceAfter=4)
    section_style = ParagraphStyle("section", parent=styles["Heading2"],
                                    fontSize=11, textColor=colors.HexColor("#1a6fd4"),
                                    spaceBefore=10, spaceAfter=4,
                                    borderPad=3)
    body_style  = ParagraphStyle("body",  parent=styles["Normal"], fontSize=9, leading=13)
    label_style = ParagraphStyle("label", parent=styles["Normal"], fontSize=8,
                                  textColor=colors.HexColor("#666666"), leading=11)
    value_style = ParagraphStyle("value", parent=styles["Normal"], fontSize=9,
                                  textColor=colors.black, leading=13, fontName="Helvetica-Bold")

    def kv(label, value):
        return [Paragraph(label, label_style), Paragraph(str(value or "—"), value_style)]

    story = []

    # ── Title ──
    story.append(Paragraph("MAINTENANCE REPORT", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=colors.HexColor("#1a6fd4"), spaceAfter=8))

    # ── Report metadata ──
    ts_alert = alert.get("timestamp")
    if isinstance(ts_alert, datetime):
        ts_alert = _to_myt(ts_alert).strftime("%Y/%m/%d %H:%M")
    report_id   = (report or {}).get("id", "—")
    maint_id    = (report or {}).get("maintenance_schedule_id", "—")
    technician  = (report or {}).get("user_id", "—")
    started_at  = (report or {}).get("started_at", "—")
    completed_at = (report or {}).get("completed_at", "—")
    for ts_val in [started_at, completed_at]:
        pass  # format below inline

    def fmt_ts(v):
        if not v or v == "—":
            return "—"
        return _fmt_myt(v)

    meta_data = [
        kv("Report ID",       report_id),
        kv("Alert ID",        alert.get("alert_id", "—")),
        kv("Engine",          f"ENGINE-{alert.get('engine_id_display','—')}"),
        kv("Maintenance ID",  maint_id),
        kv("Technician",      technician),
        kv("Alert Generated", ts_alert),
        kv("Maintenance Started", fmt_ts(started_at)),
        kv("Maintenance Completed", fmt_ts(completed_at)),
    ]
    meta_table = Table([[kv[0], kv[1]] for kv in meta_data],
                       colWidths=[55*mm, 110*mm])
    meta_table.setStyle(TableStyle([
        ("VALIGN",    (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, colors.HexColor("#f5f8ff")]),
        ("GRID",      (0,0), (-1,-1), 0.3, colors.HexColor("#ccddee")),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # ── A: Predictive Analysis ──
    story.append(Paragraph("A. PREDICTIVE ANALYSIS (System-Generated)", section_style))
    snap = lambda k: (report or {}).get(k) or alert.get(k, "—")
    pred_rul  = snap("predicted_rul_snapshot") or alert.get("rul", "—")
    severity  = snap("severity_snapshot")      or alert.get("severity", "—")
    deg_pat   = snap("degradation_pattern_snapshot") or alert.get("degradation_pattern", "—")
    sim_score = snap("similarity_score_snapshot")
    top_driv  = snap("top_drivers_snapshot")
    ai_rec    = snap("ai_recommendation_snapshot") or alert.get("llm_explanation", "—")

    pred_data = [
        ["Predicted RUL",       str(pred_rul)],
        ["Alert Severity",      str(severity).upper()],
        ["Degradation Pattern", str(deg_pat)],
        ["Similarity Score",    str(sim_score) if sim_score else "N/A"],
    ]
    pred_table = Table(pred_data, colWidths=[60*mm, 105*mm])
    pred_table.setStyle(TableStyle([
        ("FONT",     (0,0), (-1,-1), "Helvetica", 9),
        ("FONT",     (0,0), (0,-1), "Helvetica-Bold", 9),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, colors.HexColor("#f5f8ff")]),
        ("GRID",     (0,0), (-1,-1), 0.3, colors.HexColor("#ccddee")),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(pred_table)

    if top_driv:
        story.append(Spacer(1, 4))
        drivers_text = str(top_driv) if not isinstance(top_driv, list) else ", ".join(
            [f"{d[0]}: {d[1]:+.3f}" if isinstance(d, (list, tuple)) and len(d)==2 else str(d)
             for d in top_driv])
        story.append(Paragraph(f"<b>Top SHAP Drivers:</b> {drivers_text}", body_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>AI-Generated Maintenance Recommendations:</b>", body_style))
    # Strip markdown for PDF
    ai_text = str(ai_rec).replace("**", "").replace("*", "").replace("#", "") if ai_rec else "—"
    story.append(Paragraph(ai_text[:2000], body_style))
    story.append(Spacer(1, 8))

    # ── B: Maintenance Work ──
    story.append(Paragraph("B. MAINTENANCE WORK (Technician-Recorded)", section_style))
    r = report or {}
    for heading, key in [
        ("Maintenance Actions Performed", "actions_performed"),
        ("Components Inspected",          "components_inspected"),
        ("Components Repaired / Replaced","components_repaired"),
        ("Inspection Findings",           "inspection_findings"),
    ]:
        story.append(Paragraph(f"<b>{heading}:</b>", body_style))
        story.append(Paragraph(str(r.get(key) or "—"), body_style))
        story.append(Spacer(1, 4))

    # ── C: Prediction Feedback ──
    story.append(Paragraph("C. PREDICTION FEEDBACK", section_style))
    fault = (r.get("fault_confirmed") or "—").replace("_", " ").title()
    ai_us = (r.get("ai_recommendation_usefulness") or "—").replace("_", " ").title()
    story.append(Paragraph(f"<b>Fault Confirmed:</b> {fault}", body_style))
    story.append(Paragraph(f"<b>AI Recommendation Usefulness:</b> {ai_us}", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Technician Notes:</b>", body_style))
    story.append(Paragraph(str(r.get("technician_notes") or "—"), body_style))
    story.append(Spacer(1, 8))

    # ── D: Outcome ──
    story.append(Paragraph("D. MAINTENANCE OUTCOME", section_style))
    outcome = (r.get("outcome") or "—").replace("_", " ").title()
    story.append(Paragraph(f"<b>Outcome:</b> {outcome}", body_style))
    story.append(Paragraph(f"<b>Started At:</b> {fmt_ts(r.get('started_at'))}", body_style))
    story.append(Paragraph(f"<b>Completed At:</b> {fmt_ts(r.get('completed_at'))}", body_style))
    if r.get("follow_up_reason"):
        story.append(Paragraph(f"<b>Follow-up Reason:</b> {r['follow_up_reason']}", body_style))

    doc.build(story)
    return buf.getvalue()


#  CALLBACKS
def register_alert_log_callbacks(app, supabase=None):
    app.clientside_callback(
        """
        function(hoverData) {
            const hidden = {display: 'none'};
            const points = hoverData && hoverData.points;
            const graph = document.getElementById('al-rul-chart');
            const plot = graph && graph.querySelector('.js-plotly-plot');
            const layout = plot && plot._fullLayout;
            if (!points || !points.length || !layout) return [hidden, hidden, []];
            const point = points[0];
            if (point.y == null || !Number.isFinite(Number(point.y)))
                return [hidden, hidden, []];
            const axis = layout.xaxis;
            const x = axis._offset + axis.l2p(point.x);
            const top = layout.yaxis._offset;
            const width = Math.min(190, Math.max(0, graph.clientWidth - 12));
            let left = x + 12;
            if (left + width > graph.clientWidth - 6) left = x - width - 12;
            left = Math.max(6, Math.min(left, graph.clientWidth - width - 6));
            function el(type, props) {
                return {namespace: 'dash_html_components', type: type, props: props};
            }
            return [
                {display: 'block', left: x + 'px', top: top + 'px',
                 height: layout.yaxis._length + 'px'},
                {display: 'block', left: left + 'px', top: (top + 6) + 'px', width: width + 'px'},
                [el('Div', {className: 'al-rul-tooltip-title', children: 'Cycle: ' + point.x}),
                 el('Div', {className: 'al-rul-tooltip-row', children: [
                     el('Span', {className: 'al-rul-tooltip-dot'}),
                     el('Span', {children: 'RUL'}),
                     el('Strong', {children: Number(point.y).toFixed(1) + ' cycles'})]}),
                 el('Div', {className: 'al-rul-tooltip-footer', children: 'Hover to view values'})]
            ];
        }
        """,
        Output("al-rul-vline", "style"),
        Output("al-rul-tooltip", "style"),
        Output("al-rul-tooltip", "children"),
        Input("al-rul-chart", "hoverData"),
    )


    # ── 1. Row selection ──────────────────────────────────────────────
    @app.callback(
        Output("alert-detail-container",  "children", allow_duplicate=True),
        Output("alert-table-body",        "children", allow_duplicate=True),
        Output("selected-alert-idx",      "data",     allow_duplicate=True),
        Input({"type": "al-row", "index": ALL}, "n_clicks"),
        State("alerts-data",       "data"),
        State("selected-alert-idx","data"),
        prevent_initial_call=True,
    )
    def select_alert(n_clicks_list, alerts_data, current_idx):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        parsed = _json.loads(trigger_id)
        if parsed.get("type") != "al-row":
            raise dash.exceptions.PreventUpdate
        idx     = parsed["index"]
        alerts  = [_alert_from_store(a) for a in alerts_data]
        report  = (alerts[idx].get("report")) if idx < len(alerts) else None
        detail  = alert_detail_panel(alerts[idx], report=report) if idx < len(alerts) else []
        rows    = [alert_table_row(i, a, is_selected=(i == idx)) for i, a in enumerate(alerts)]

        return (detail, rows, idx)
    # ── 2. Filter (severity + status + search) ────────────────────────
    @app.callback(
        Output("alert-table-body", "children", allow_duplicate=True),
        Input("alert-severity-filter", "value"),
        Input("alert-status-filter",   "value"),
        Input("alert-search-input",    "value"),
        State("alerts-data",           "data"),
        State("selected-alert-idx",    "data"),
        prevent_initial_call=True,
    )
    def filter_alerts(sev_filter, status_filter, search_text, alerts_data, selected_idx):
        alerts = [_alert_from_store(a) for a in alerts_data]
        if sev_filter and sev_filter != "all":
            alerts = [a for a in alerts if a.get("severity") == sev_filter]
        if status_filter and status_filter != "all":
            alerts = [a for a in alerts
                      if (a.get("maintenance_status") or "maintenance_required") == status_filter]
        if search_text:
            q = search_text.lower()
            alerts = [a for a in alerts if (
                q in a.get("alert_no", "").lower() or
                q in _to_myt(a["timestamp"]).strftime("%Y/%m/%d %H:%M").lower() or
                q in a.get("severity", "").lower() or
                q in str(a.get("rul", "")) or
                q in (a.get("degradation_pattern") or "").lower()
            )]
        rows = [alert_table_row(i, a, is_selected=(i == selected_idx)) for i, a in enumerate(alerts)]
        if not rows:
            rows = [html.Div("No alerts matching filter.",
                             style={"color": "rgba(168,212,255,0.5)", "textAlign": "center",
                                    "padding": "30px 0", "fontSize": "13px"})]
        return rows

    # ── 3. Action button click → open appropriate modal ───────────────
    @app.callback(
        # Schedule modal
        Output("al-sched-modal-overlay",       "style",    allow_duplicate=True),
        Output("al-sched-modal-title",         "children", allow_duplicate=True),
        Output("al-sched-modal-context",       "children", allow_duplicate=True),
        Output("al-modal-trigger-store",       "data",     allow_duplicate=True),
        # Report modal
        Output("al-report-modal-overlay",      "style",    allow_duplicate=True),
        Output("al-report-header",             "children", allow_duplicate=True),
        Output("al-report-analysis-section",   "children", allow_duplicate=True),
        Output("al-report-actions",            "value",    allow_duplicate=True),
        Output("al-report-components-inspected","value",   allow_duplicate=True),
        Output("al-report-components-repaired", "value",   allow_duplicate=True),
        Output("al-report-findings",           "value",    allow_duplicate=True),
        Output("al-report-fault-confirmed",    "value",    allow_duplicate=True),
        Output("al-report-ai-usefulness",      "value",    allow_duplicate=True),
        Output("al-report-technician-notes",   "value",    allow_duplicate=True),
        Output("al-report-schedule-id-store",     "data",     allow_duplicate=True),
        Output("al-report-id-store",           "data",     allow_duplicate=True),
        Output("al-report-readonly-store",     "data",     allow_duplicate=True),
        # Schedule input pre-fill (for View Schedule)
        Output("al-sched-date",                "value",    allow_duplicate=True),
        Output("al-sched-start",               "value",    allow_duplicate=True),
        Output("al-sched-end",                 "value",    allow_duplicate=True),
        Output("al-sched-original-store",      "data",     allow_duplicate=True),
        Output("al-sched-schedule-db-id-store","data",     allow_duplicate=True),
        # Input — static engine-level action button (see note above)
        Input("al-engine-action-btn",           "n_clicks"),
        State("alerts-data",                    "data"),
        State("selected-alert-idx",             "data"),
        State("al-sched-role-store",            "data"),
        State("al-sched-org-users-store",       "data"),
        State("al-sched-current-user-label-store","data"),
        prevent_initial_call=True,
    )
    def handle_action(n_clicks,
                      alerts_data, selected_idx,
                      role, org_users, current_user_label):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        no_update  = dash.no_update

        alerts = [_alert_from_store(a) for a in alerts_data]
        if not alerts:
            raise dash.exceptions.PreventUpdate

        # The engine-level action button always reflects the primary (first) alert
        idx = 0
        alert    = alerts[idx]
        mstatus  = (alert.get("maintenance_status") or "maintenance_required").lower().strip()
        alert_id = alert.get("alert_id")

        sched_hidden = {"display": "none", "position": "fixed", "top": "0", "left": "0",
                        "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.80)",
                        "zIndex": "1200", "alignItems": "center", "justifyContent": "center"}
        sched_shown  = {**sched_hidden, "display": "flex"}
        report_hidden = {"display": "none", "position": "fixed", "top": "0", "left": "0",
                         "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.88)",
                         "zIndex": "1300", "alignItems": "flex-start", "justifyContent": "center",
                         "overflowY": "auto", "paddingTop": "20px", "paddingBottom": "40px"}
        report_shown  = {**report_hidden, "display": "flex"}

        def _open_schedule_modal(is_followup=False):
            title   = "Schedule Follow-up Maintenance" if is_followup else "Schedule Maintenance"
            # Build engine_db_id for the calendar link
            engine_db_id = None
            if alerts_data and idx < len(alerts_data):
                engine_db_id = alerts_data[idx].get("engine_id") or ""
            cal_href = f"/schedule-maintenance/{engine_db_id}" if engine_db_id else "/schedule-maintenance"
            context = html.Div([
                html.Div(style={"marginBottom": "8px"}, children=[
                    html.Span(f"Alert #{alert['alert_no']}  |  ", style={"fontWeight": "700"}),
                    html.Span(f"Severity: {alert.get('severity','—').upper()}  |  "),
                    html.Span(f"RUL at alert: {alert.get('rul','—')} cycles  |  "),
                    html.Span(f"Pattern: {alert.get('degradation_pattern','—')}"),
                ]),
                html.A(
                    "◷  Open in Maintenance Schedule →",
                    href=cal_href,
                    target="_self",
                    style={
                        "color": "#4a9eff", "fontSize": "12px", "fontWeight": "600",
                        "textDecoration": "none", "display": "inline-block",
                        "padding": "5px 0", "letterSpacing": "0.2px",
                    }
                ),
            ])

            # Assignee row visibility
            is_admin = (role or "user") == "admin"
            admin_row_style = {"marginBottom": "14px", "display": "block"} if is_admin else {"marginBottom": "14px", "display": "none"}
            self_row_style  = {"marginBottom": "14px", "display": "none"} if is_admin else {"marginBottom": "14px", "display": "block"}
            user_opts  = org_users or []
            user_val   = None   # admin picks; no default pre-select
            self_label = current_user_label or "You (logged-in user)"

            return (sched_shown, title, context,
                    "followup" if is_followup else "schedule",
                    report_hidden,
                    *([no_update] * 12),
                    None, "09:00", "10:00", None, None)

        def _open_report_modal(readonly=False):
            schedule_id = alert.get("maintenance_schedule_id")

            if not schedule_id:
                print("[ALERT] No maintenance_schedule_id found for report")
                raise dash.exceptions.PreventUpdate

            report = _fetch_report(
                supabase,
                schedule_id
            ) if supabase else None

            r = report or {}

            rpt_header, rpt_analysis = _build_report_readonly_sections(
                alert,
                report
            )

            return (
                sched_hidden,
                no_update,
                no_update,
                no_update,
                report_shown,
                rpt_header,
                rpt_analysis,
                r.get("actions_performed", ""),
                r.get("components_inspected", ""),
                r.get("components_repaired", ""),
                r.get("inspection_findings", ""),
                r.get("fault_confirmed"),
                r.get("ai_recommendation_usefulness"),
                r.get("technician_notes", ""),

                # IMPORTANT
                schedule_id,

                r.get("id"),
                readonly,
                no_update, no_update, no_update, no_update, no_update,
            )

        # ── Engine-level action button ─────────────────────────────────
        if mstatus == "maintenance_required":
            return _open_schedule_modal(is_followup=False)
        elif mstatus == "scheduled":
            # Fetch current schedule from DB and pre-fill inputs
            sched_id   = alert.get("maintenance_schedule_id")
            sched_row  = {}
            if supabase and sched_id:
                try:
                    sr = supabase.table("maintenance_schedules") \
                        .select("id,scheduled_date,start_time,end_time") \
                        .eq("id", sched_id).single().execute()
                    sched_row = sr.data or {}
                except Exception as _e:
                    print(f"[ALERT] fetch schedule for view: {_e}")

            prefill_date  = sched_row.get("scheduled_date") or ""
            prefill_start = sched_row.get("start_time", "09:00") or "09:00"
            prefill_end   = sched_row.get("end_time", "10:00") or "10:00"
            original = {
                "date":  prefill_date,
                "start": prefill_start,
                "end":   prefill_end,
            }

            context = html.Div([
                html.Span(f"Engine {alert.get('engine_id')}  |  ", style={"fontWeight": "700"}),
                html.Span("Edit the schedule details below and save to update.",
                          style={"color": "#a8d4ff"}),
            ])
            return (sched_shown, "View / Edit Schedule", context, "view", report_hidden, *([no_update] * 12), prefill_date, prefill_start, prefill_end, original, sched_id)
        elif mstatus == "in_progress":
            return _open_report_modal(readonly=False)
        elif mstatus == "completed":
            return _open_report_modal(readonly=True)
        elif mstatus == "follow_up_required":
            return _open_schedule_modal(is_followup=True)

        raise dash.exceptions.PreventUpdate


    # ── Helper inside register scope ──────────────────────────────────
    def _build_report_readonly_sections(alert, report):
        """Build the read-only header and predictive analysis sections for the report modal."""
        ts = _to_myt(alert["timestamp"]).strftime("%Y/%m/%d %H:%M") if isinstance(alert.get("timestamp"), datetime) else str(alert.get("timestamp", "—"))
        r  = report or {}

        started_at = r.get("started_at", "—")
        if started_at and started_at != "—":
            started_at = _fmt_myt(started_at)

        header = html.Div([
            html.H3("MAINTENANCE REPORT",
                    style={"margin": "0 0 4px", "color": "white", "fontSize": "20px", "fontWeight": "800"}),
            html.Div(style={"display": "flex", "gap": "18px", "flexWrap": "wrap", "marginTop": "10px",
                            "marginBottom": "4px"}, children=[
                html.Div([html.Div("REPORT ID", style={"color": "#4a9eff", "fontSize": "10px", "fontWeight": "700", "letterSpacing": "0.8px"}),
                          html.Div((r.get("id") or "Pending"), style={"color": "white", "fontSize": "12px", "fontFamily": "monospace"})]),
                html.Div([html.Div("ENGINE ID", style={"color": "#4a9eff", "fontSize": "10px", "fontWeight": "700", "letterSpacing": "0.8px"}),
                          html.Div((alert.get("engine_id")), style={"color": "white", "fontSize": "12px", "fontFamily": "monospace"})]),
                html.Div([html.Div("MAINTENANCE ID",   style={"color": "#4a9eff", "fontSize": "10px", "fontWeight": "700", "letterSpacing": "0.8px"}),
                          html.Div((alert.get("engine_id")), style={"color": "white", "fontSize": "12px", "fontFamily": "monospace"})]),
                html.Div([html.Div("STARTED", style={"color": "#4a9eff", "fontSize": "10px", "fontWeight": "700", "letterSpacing": "0.8px"}),
                          html.Div(started_at, style={"color": "white", "fontSize": "12px"})]),
                html.Div([html.Div("STATUS", style={"color": "#4a9eff", "fontSize": "10px", "fontWeight": "700", "letterSpacing": "0.8px"}),
                          html.Div(style={"marginTop": "3px"}, children=[maintenance_status_badge(alert.get("maintenance_status", "in_progress"))])]),
            ]),
        ])

        # Predictive analysis read-only
        snap_rul   = r.get("predicted_rul_snapshot") or alert.get("rul", "—")
        snap_sev   = r.get("severity_snapshot")      or alert.get("severity", "—")
        snap_deg   = r.get("degradation_pattern_snapshot") or alert.get("degradation_pattern", "—")
        snap_sim   = r.get("similarity_score_snapshot")
        snap_driv  = r.get("top_drivers_snapshot")
        snap_ai    = r.get("ai_recommendation_snapshot") or alert.get("llm_explanation", "")

        analysis = html.Div([
            _detail_row("Predicted RUL",       f"{snap_rul} cycles", "#ff6b6b"),
            _detail_row("Severity",            (snap_sev or "—").upper(), "white"),
            _detail_row("Degradation Pattern", snap_deg or "—", "white"),
            _detail_row("Similarity Score",    f"{snap_sim:.3f}" if snap_sim else "N/A", "#a8d4ff"),
            html.Div(style={"marginTop": "10px"}) if snap_driv else html.Div(),
            html.Div([
                html.Div("Top SHAP Drivers", style={"color": "#4a9eff", "fontSize": "11px",
                                                      "fontWeight": "700", "letterSpacing": "1px",
                                                      "marginBottom": "6px"}),
                html.Div(shap_mini_bars(snap_driv) if isinstance(snap_driv, list) else
                         html.Span(str(snap_driv) if snap_driv else "—",
                                   style={"color": "#a8d4ff", "fontSize": "12px"})),
            ]) if snap_driv else html.Div(),
            html.Div(style={"marginTop": "10px"}) if snap_ai else html.Div(),
            html.Div([
                html.Div("AI Recommended Maintenance Actions",
                         style={"color": "#4a9eff", "fontSize": "11px", "fontWeight": "700",
                                "letterSpacing": "1px", "marginBottom": "6px"}),
                html.Div(
                    style={"background": "rgba(10,20,45,0.4)", "borderRadius": "6px",
                           "padding": "8px 12px", "border": "1px solid rgba(74,158,255,0.1)",
                           "maxHeight": "140px", "overflowY": "auto"},
                    children=dcc.Markdown(snap_ai, className="ai-explanation-md") if snap_ai else html.Span("—")
                ),
            ]) if snap_ai else html.Div(),
        ])

        return header, analysis

    # ── 3b. Dirty-check — enable/disable/rename confirm button ──────────
    @app.callback(
        Output("al-sched-modal-confirm", "disabled",  allow_duplicate=True),
        Output("al-sched-modal-confirm", "children",  allow_duplicate=True),
        Output("al-sched-modal-confirm", "style",     allow_duplicate=True),
        Input("al-sched-date",           "value"),
        Input("al-sched-start",          "value"),
        Input("al-sched-end",            "value"),
        Input("al-modal-trigger-store",  "data"),
        State("al-sched-original-store", "data"),
        prevent_initial_call=True,
    )
    def update_confirm_button(date_val, start_val, end_val, trigger, original):
        _btn_enabled = {
            "background": "rgba(74,158,255,0.18)",
            "border": "1px solid rgba(74,158,255,0.55)",
            "borderRadius": "8px", "color": "#7ab8ff",
            "fontSize": "13px", "fontWeight": "700",
            "padding": "9px 22px", "cursor": "pointer",
            "opacity": "1", "transition": "opacity 0.2s",
        }
        _btn_disabled = {
            **_btn_enabled,
            "opacity": "0.35",
            "cursor": "not-allowed",
        }

        mode = (trigger or "schedule")

        if mode == "view":
            # In view mode the button is labelled "Save Updated Schedule"
            # and only enabled when at least one field differs from the stored original
            orig = original or {}
            is_dirty = (
                (date_val  or "") != (orig.get("date")  or "") or
                (start_val or "") != (orig.get("start") or "") or
                (end_val   or "") != (orig.get("end")   or "") 
            )
            if is_dirty:
                return False, "Save Updated Schedule", _btn_enabled
            else:
                return True,  "Save Updated Schedule", _btn_disabled
        else:
            # New schedule / follow-up: always labelled "Confirm Schedule", always enabled
            return False, "Confirm Schedule", _btn_enabled

    # ── 4. Confirm schedule → update DB → update alert status ─────────
    # NOTE: the "Update local store" block below used to be nested INSIDE
    # `if supabase and alert_id:`, so whenever supabase was falsy (or the
    # alert had no alert_id) the function fell off the end with an implicit
    # `return None` — Dash can't unpack that into 8 outputs, the callback
    # silently errors, and the modal's overlay style is never reset back to
    # hidden. That block is now unconditional so the modal always closes.
    # The "al-engine-status-bar" output has also been split into three
    # separate outputs (badge children / button children / button style) so
    # the action button is updated in place instead of being recreated
    # (recreating it reset n_clicks and could re-open the modal — see the
    # docstring on _engine_status_bar_contents / _status_button_props).
    @app.callback(
        Output("al-sched-modal-overlay",  "style",    allow_duplicate=True),
        Output("al-sched-modal-msg",      "children", allow_duplicate=True),
        Output("alerts-data",             "data",     allow_duplicate=True),
        Output("al-engine-status-badge",  "children", allow_duplicate=True),
        Output("al-engine-action-btn",    "children", allow_duplicate=True),
        Output("al-engine-action-btn",    "style",    allow_duplicate=True),
        Output("alert-detail-container",  "children", allow_duplicate=True),
        Output("alert-table-body",        "children", allow_duplicate=True),
        Input("al-sched-modal-confirm",   "n_clicks"),
        State("al-sched-date",            "value"),
        State("al-sched-start",           "value"),
        State("al-sched-end",             "value"),
        State("al-modal-trigger-store",   "data"),
        State("alerts-data",              "data"),
        State("selected-alert-idx",       "data"),
        State("session-store",            "data"),
        State("al-sched-role-store",      "data"),
        State("al-sched-schedule-db-id-store", "data"),
        prevent_initial_call=True,
    )
    def confirm_schedule(n_clicks, sel_date, start_time, end_time,
                         trigger_type, alerts_data, selected_idx, session, role, existing_schedule_id):
        hidden = {"display": "none", "position": "fixed", "top": "0", "left": "0",
                  "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.80)",
                  "zIndex": "1200", "alignItems": "center", "justifyContent": "center"}

        if not sel_date:
            return (dash.no_update,
                    html.Span("Please select a date.", style={"color": "#ff6b6b", "fontSize": "12px"}),
                    *([dash.no_update] * 6))
        alerts = [_alert_from_store(a) for a in alerts_data]
        idx    = selected_idx or 0
        if idx >= len(alerts):
            raise dash.exceptions.PreventUpdate
        alert    = alerts[idx]
        alert_id = alert.get("alert_id")

        sched_db_id  = None
        engine_db_id = None
        if supabase and alert_id:
            try:
                user_id  = (session or {}).get("user_id")
                
                # Resolve the engine_id for this alert
                arow = _fetch_alert_row(supabase, alert_id)
                engine_db_id = arow.get("engine_id")

                # ── EDIT EXISTING SCHEDULE ─────────────────────────────
                if trigger_type == "view" and existing_schedule_id:

                    update_payload = {
                        "scheduled_date": sel_date,
                        "start_time": start_time or "09:00",
                        "end_time": end_time or "10:00",
                    }

                    result = (
                        supabase.table("maintenance_schedules")
                        .update(update_payload)
                        .eq("id", existing_schedule_id)
                        .execute()
                    )

                    sched_db_id = existing_schedule_id

                    print(
                        f"[ALERT] Updated maintenance schedule "
                        f"{sched_db_id}: {update_payload}"
                    )

                else:
                    # ── NEW SCHEDULE / FOLLOW-UP ───────────────────────────
                    responsible_user_id = None
                    if engine_db_id:
                        try:
                            engine_resp = (
                                supabase.table("engines")
                                .select("responsible_by")
                                .eq("id", engine_db_id)
                                .single()
                                .execute()
                            )

                            if engine_resp.data:
                                responsible_user_id = engine_resp.data.get("responsible_by")

                        except Exception as _e:
                            print(f"[ALERT] Failed to fetch engine responsible user: {_e}")

                    existing_sched = None
                    if engine_db_id:
                        try:
                            ex_resp = (
                                supabase.table("maintenance_schedules")
                                .select("id,scheduled_date,created_by")
                                .eq("engine_id", engine_db_id)
                                .not_.in_("status", ["completed", "cancelled"])
                                .order("created_at", desc=True)
                                .limit(1)
                                .execute()
                            )

                            if ex_resp.data:
                                existing_sched = ex_resp.data[0]

                        except Exception as _e:
                            print(f"[ALERT] check existing schedule: {_e}")

                    if existing_sched:
                        sched_db_id = existing_sched["id"]

                        print(
                            f"[ALERT] Reusing existing schedule "
                            f"{sched_db_id} for engine {engine_db_id}"
                        )
                    else:
                        result = (
                            supabase.table("maintenance_schedules")
                            .insert({
                                "engine_id": engine_db_id,
                                "scheduled_date": sel_date,
                                "start_time": start_time or "09:00",
                                "end_time": end_time or "10:00",
                                "status": "scheduled",
                                "created_by": user_id,
                                "assigned_to": responsible_user_id,
                            })
                            .execute()
                        )

                        if result.data:
                            sched_db_id = result.data[0]["id"]

                            print(
                                f"[ALERT] Created new schedule "
                                f"{sched_db_id} for engine {engine_db_id}"
                            )

                    # ── Link engine alerts to this maintenance schedule ──────────────
                        if sched_db_id and engine_db_id:
                            try:
                                # Get alerts for this engine
                                engine_alerts_resp = (
                                    supabase.table("alert_logs")
                                    .select("id")
                                    .eq("engine_id", engine_db_id)
                                    .execute()
                                )

                                engine_alert_ids = [
                                    row["id"]
                                    for row in (engine_alerts_resp.data or [])
                                ]

                                if engine_alert_ids:
                                    # Find alerts already linked to a maintenance schedule
                                    linked_resp = (
                                        supabase.table("maintenance_alerts")
                                        .select("alert_id")
                                        .in_("alert_id", engine_alert_ids)
                                        .execute()
                                    )

                                    linked_alert_ids = {
                                        row["alert_id"]
                                        for row in (linked_resp.data or [])
                                    }

                                    # Only link alerts that have not already been assigned
                                    rows_to_insert = [
                                        {
                                            "maintenance_schedule_id": sched_db_id,
                                            "alert_id": aid,
                                        }
                                        for aid in engine_alert_ids
                                        if aid not in linked_alert_ids
                                    ]

                                    if rows_to_insert:
                                        (
                                            supabase.table("maintenance_alerts")
                                            .insert(rows_to_insert)
                                            .execute()
                                        )

                                        print(
                                            f"[ALERT] Linked {len(rows_to_insert)} alerts "
                                            f"to maintenance schedule {sched_db_id}"
                                        )

                            except Exception as _e:
                                print(f"[ALERT] maintenance_alerts mapping: {_e}")
            except Exception as _e:
                print(f"[ALERT] confirm_schedule DB error: {_e}")

        # ── Update local store — all alerts for the same engine ──────
        # (runs unconditionally now — see note above)
        if sched_db_id:
            clicked_engine = alerts_data[idx].get("engine_id") if idx < len(alerts_data) else None
            for i, a in enumerate(alerts_data):
                same_engine = (a.get("engine_id") == clicked_engine) if clicked_engine else (i == idx)
                if same_engine and (a.get("maintenance_status") or "maintenance_required") \
                        not in ("completed", "follow_up_required"):
                    alerts_data[i]["maintenance_status"]      = "scheduled"
                    alerts_data[i]["scheduled_date"]          = sel_date
                    alerts_data[i]["maintenance_schedule_id"] = sched_db_id
        else:
            # No schedule created — at minimum update the clicked row in the store
            alerts_data[idx]["maintenance_status"]    = "scheduled"
            alerts_data[idx]["scheduled_date"]        = sel_date

        alerts = [_alert_from_store(a) for a in alerts_data]
        report = (alerts[idx].get("report")) if idx < len(alerts) else None
        detail = alert_detail_panel(alerts[idx], report=report)
        rows   = [alert_table_row(i, a, is_selected=(i == idx)) for i, a in enumerate(alerts)]
        current_schedule = {"status": "scheduled", "scheduled_date": sel_date} if sched_db_id else None
        badge, btn_children, btn_style = _engine_status_bar_contents(alerts, current_schedule=current_schedule)
        return hidden, "", alerts_data, badge, btn_children, btn_style, detail, rows

    # ── 5. Close schedule modal ───────────────────────────────────────
    @app.callback(
        Output("al-sched-modal-overlay", "style", allow_duplicate=True),
        Input("al-sched-modal-cancel",   "n_clicks"),
        Input("al-sched-modal-close",    "n_clicks"),
        prevent_initial_call=True,
    )
    def close_sched_modal(cancel, close):
        return {"display": "none", "position": "fixed", "top": "0", "left": "0",
                "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.80)",
                "zIndex": "1200", "alignItems": "center", "justifyContent": "center"}


    # ── 6. Save Progress ──────────────────────────────────────────────
    @app.callback(
        Output("al-report-msg", "children", allow_duplicate=True),
        Input("al-report-save-btn",          "n_clicks"),
        State("al-report-actions",           "value"),
        State("al-report-components-inspected","value"),
        State("al-report-components-repaired", "value"),
        State("al-report-findings",          "value"),
        State("al-report-fault-confirmed",   "value"),
        State("al-report-ai-usefulness",     "value"),
        State("al-report-technician-notes",  "value"),
        State("al-report-schedule-id-store", "data"),
        State("al-report-id-store",          "data"),
        State("session-store",               "data"),
        prevent_initial_call=True,
    )

    def save_report_progress(n_clicks, actions, comp_insp, comp_rep, findings, notes, fault, ai_use, schedule_id, report_id, session):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "actions_performed":         actions or "",
            "components_inspected":      comp_insp or "",
            "components_repaired":       comp_rep or "",
            "inspection_findings":       findings or "",
            "fault_confirmed":           fault,
            "ai_recommendation_usefulness": ai_use,
            "technician_notes":          notes or "",
            "outcome":                   "in_progress",
            "updated_at":                now,
        }
        if session and session.get("user_id"):
            payload["user_id"] = session["user_id"]

        if supabase:
            try:
                if report_id:
                    supabase.table("maintenance_reports").update(payload).eq("id", report_id).execute()
                elif schedule_id:
                    payload["maintenance_schedule_id"] = schedule_id
                    payload["started_at"] = now
                    supabase.table("maintenance_reports").insert(payload).execute()
            except Exception as _e:
                print(f"[ALERT] save progress: {_e}")
                return html.Span("⚠ Save failed. Please try again.",
                                 style={"color": "#ff6b6b", "fontSize": "12px"})

        return html.Span("✓ Progress saved.",
                         style={"color": "#00c875", "fontSize": "12px", "fontWeight": "700"})

    # ── 7. Follow-up Required button → show reason field ──────────────
    @app.callback(
        Output("al-report-followup-reason-row", "style", allow_duplicate=True),
        Input("al-report-followup-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def show_followup_reason_row(n_clicks):
        return {"marginBottom": "14px", "display": "block"}

    # ── 8. Complete / Follow-up → open confirm modal ──────────────────
    @app.callback(
        Output("al-confirm-modal-overlay", "style",    allow_duplicate=True),
        Output("al-confirm-modal-title",   "children", allow_duplicate=True),
        Output("al-confirm-modal-body",    "children", allow_duplicate=True),
        Input("al-report-complete-btn",    "n_clicks"),
        Input("al-report-followup-btn",    "n_clicks"),
        prevent_initial_call=True,
    )
    def open_confirm_modal(complete_clicks, followup_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        trigger = ctx.triggered[0]["prop_id"].split(".")[0]
        shown = {"display": "flex", "position": "fixed", "top": "0", "left": "0",
                 "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.85)",
                 "zIndex": "1500", "alignItems": "center", "justifyContent": "center"}
        if trigger == "al-report-complete-btn":
            return shown, "Complete Maintenance?", \
                "This will finalise the report. The status will be set to Completed."
        return shown, "Mark Follow-up Required?", \
            "The current report will be saved and the status set to Follow-up Required."

    @app.callback(
        Output("al-confirm-modal-overlay", "style", allow_duplicate=True),
        Input("al-confirm-cancel-btn",     "n_clicks"),
        prevent_initial_call=True,
    )
    def close_confirm_modal(n):
        return {"display": "none", "position": "fixed", "top": "0", "left": "0",
                "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.85)",
                "zIndex": "1500", "alignItems": "center", "justifyContent": "center"}

    # ── 9. Confirm Complete / Follow-up → write to DB ─────────────────
    # Same "al-engine-status-bar" split as callback #4 — see its note above.
    @app.callback(
        Output("al-confirm-modal-overlay", "style",    allow_duplicate=True),
        Output("al-report-modal-overlay",  "style",    allow_duplicate=True),
        Output("al-report-msg",            "children", allow_duplicate=True),
        Output("alerts-data",              "data",     allow_duplicate=True),
        Output("al-engine-status-badge",   "children", allow_duplicate=True),
        Output("al-engine-action-btn",     "children", allow_duplicate=True),
        Output("al-engine-action-btn",     "style",    allow_duplicate=True),
        Output("alert-detail-container",   "children", allow_duplicate=True),
        Output("alert-table-body",         "children", allow_duplicate=True),
        Input("al-confirm-ok-btn",                   "n_clicks"),
        State("al-confirm-modal-title",              "children"),
        State("al-report-actions",                   "value"),
        State("al-report-components-inspected",      "value"),
        State("al-report-components-repaired",       "value"),
        State("al-report-findings",                  "value"),
        State("al-report-fault-confirmed",           "value"),
        State("al-report-ai-usefulness",             "value"),
        State("al-report-technician-notes",          "value"),
        State("al-report-followup-reason",           "value"),
        State("al-report-schedule-id-store",            "data"),
        State("al-report-id-store",                  "data"),
        State("alerts-data",                         "data"),
        State("selected-alert-idx",                  "data"),
        State("session-store",                       "data"),
        prevent_initial_call=True,
    )
    def confirm_outcome(n_clicks, modal_title, actions, comp_insp, comp_rep, findings,
                        fault, ai_use, notes, followup_reason,
                        maintenance_schedule_id, report_id, alerts_data, selected_idx, session):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        confirm_hidden = {"display": "none", "position": "fixed", "top": "0", "left": "0",
                          "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.85)",
                          "zIndex": "1500", "alignItems": "center", "justifyContent": "center"}
        report_hidden  = {"display": "none", "position": "fixed", "top": "0", "left": "0",
                          "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.88)",
                          "zIndex": "1300", "alignItems": "flex-start", "justifyContent": "center",
                          "overflowY": "auto", "paddingTop": "20px", "paddingBottom": "40px"}

        is_followup = "Follow-up" in (modal_title or "")
        new_status  = "follow_up_required" if is_followup else "completed"
        now         = datetime.now(timezone.utc).isoformat()

        payload = {
            "actions_performed":         actions or "",
            "components_inspected":      comp_insp or "",
            "components_repaired":       comp_rep or "",
            "inspection_findings":       findings or "",
            "fault_confirmed":           fault,
            "ai_recommendation_usefulness": ai_use,
            "technician_notes":          notes or "",
            "outcome":                   new_status,
            "follow_up_reason":          followup_reason or "" if is_followup else "",
            "completed_at":              now,
            "updated_at":                now,
        }
        if session and session.get("user_id"):
            payload["user_id"] = session["user_id"]

        if supabase:
            try:
                if report_id:
                    supabase.table("maintenance_reports").update(payload).eq("id", report_id).execute()

                elif maintenance_schedule_id:
                    payload["maintenance_schedule_id"] = maintenance_schedule_id
                    payload["started_at"] = now

                    supabase.table("maintenance_reports").insert(payload).execute()
                schedule_upd = {
                    "status": new_status,
                    "completed_at": now,
                }

                supabase.table("maintenance_schedules").update(schedule_upd).eq("id", maintenance_schedule_id).execute()
            except Exception as _e:
                print(f"[ALERT] confirm outcome: {_e}")

        # Update local store
        idx = selected_idx or 0
        if idx < len(alerts_data):
            alerts_data[idx]["maintenance_status"] = new_status
            if is_followup:
                alerts_data[idx]["follow_up_reason"] = followup_reason

        alerts  = [_alert_from_store(a) for a in alerts_data]
        report  = _fetch_report(supabase, maintenance_schedule_id) if supabase else None
        detail  = alert_detail_panel(alerts[idx], report=report) if idx < len(alerts) else []
        rows    = [alert_table_row(i, a, is_selected=(i == idx)) for i, a in enumerate(alerts)]
        badge, btn_children, btn_style = _engine_status_bar_contents(alerts)
        return confirm_hidden, report_hidden, "", alerts_data, badge, btn_children, btn_style, detail, rows

    # ── 10. Close report modal ────────────────────────────────────────
    @app.callback(
        Output("al-report-modal-overlay", "style", allow_duplicate=True),
        Input("al-report-modal-close",    "n_clicks"),
        prevent_initial_call=True,
    )
    def close_report_modal(n):
        return {"display": "none", "position": "fixed", "top": "0", "left": "0",
                "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.88)",
                "zIndex": "1300", "alignItems": "flex-start", "justifyContent": "center",
                "overflowY": "auto", "paddingTop": "20px", "paddingBottom": "40px"}



    # ── 12. Sidebar toggle (re-registered here for this page) ─────────
    @app.callback(
        Output("sidebar",       "style",  allow_duplicate=True),
        Output("sidebar-state", "data",   allow_duplicate=True),
        Input("sidebar-toggle", "n_clicks"),
        State("sidebar-state",  "data"),
        prevent_initial_call=True,
    )
    def toggle_sidebar(n, is_open):
        if not n or n == 0:
            raise dash.exceptions.PreventUpdate
        is_open = not is_open
        base = {
            "flexShrink": "0", "height": "calc(100vh - 60px)",
            "maxHeight": "calc(100vh - 60px)",
            "background": "#0d1e3a",
            "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex", "flexDirection": "column",
            "overflow": "hidden", "transition": "width 0.3s ease",
        }
        return ({**base, "width": "210px"}, True) if is_open else ({**base, "width": "0px"}, False)


if __name__ == "__main__":
    _app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                     suppress_callback_exceptions=True)
    _app.layout = html.Div([
        dcc.Store(id="sidebar-state", data=True),
        dcc.Store(id="session-store", data=None),
        create_alert_log_layout(),
    ])
    register_alert_log_callbacks(_app)
    _app.run(debug=True)
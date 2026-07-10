import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import base64
import numpy as np
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────────
#  SVG ICON HELPERS  (shared style with overview.py / sensor_trends.py)
# ─────────────────────────────────────────────

def _svg_img(svg_str, size="22px"):
    b64 = base64.b64encode(svg_str.strip().encode("utf-8")).decode("utf-8")
    return html.Img(src=f"data:image/svg+xml;base64,{b64}",
                    style={"width": size, "height": size, "flexShrink": "0"})

def icon_dashboard():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
      <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
    </svg>''')

def icon_overview():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="7"/><line x1="16.5" y1="16.5" x2="21" y2="21"/>
    </svg>''')

def icon_sensor():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="3 17 7 11 11 14 15 8 21 8"/>
      <line x1="3" y1="21" x2="21" y2="21"/>
    </svg>''')

def icon_shap():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 2v3M12 19v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12
               M2 12h3M19 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/>
    </svg>''')

def icon_alert():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>''')

def icon_sidebar():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <line x1="9" y1="3" x2="9" y2="21"/>
    </svg>''', size="26px")

def icon_logout():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#ff4d4d" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>''', size="22px")


# ─────────────────────────────────────────────
#  SIDEBAR  (shared layout pattern)
# ─────────────────────────────────────────────

def build_sidebar(active_page="alert", engine_db_id=None):
    nav_item_base = {
        "display": "flex", "alignItems": "center", "gap": "10px",
        "padding": "10px 14px", "borderRadius": "10px", "cursor": "pointer",
        "fontSize": "14px", "fontWeight": "500", "color": "#a8d4ff",
        "marginBottom": "4px", "whiteSpace": "nowrap",
    }

    def nav_link(icon_fn, label, page_key, href="/"):
        style = {**nav_item_base}
        if active_page == page_key:
            style.update({
                "background": "rgba(74,158,255,0.18)", "color": "white",
                "fontWeight": "700", "borderLeft": "3px solid #4a9eff", "paddingLeft": "11px",
            })
        return html.A(href=href, style={"textDecoration": "none"},
                      children=[html.Div(style=style, children=[icon_fn(), html.Span(label)])])

    # Build navigation links with engine_db_id if available
    overview_href = f"/overview/{engine_db_id}" if engine_db_id else "/dashboard"
    sensor_href = f"/sensor-trends/{engine_db_id}" if engine_db_id else "/sensor-trends"
    degradation_analysis_href = f"/degradation-analysis/{engine_db_id}" if engine_db_id else "/degradation-analysis"
    alert_href = f"/alert-log/{engine_db_id}" if engine_db_id else "/alert-log"

    return html.Div(
        id="sidebar",
        style={
            "width": "210px", "flexShrink": "0", "height": "100%",
            "background": "#0d1e3a", "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex", "flexDirection": "column",
            "overflow": "hidden", "transition": "width 0.3s ease",
        },
        children=[
            html.A(href="/dashboard", style={"textDecoration": "none"}, children=[
                html.Div(style={
                    "padding": "20px 20px 18px",
                    "borderBottom": "1px solid rgba(74,158,255,0.12)",
                    "display": "flex", "alignItems": "center", "gap": "10px", "cursor": "pointer",
                }, children=[
                    icon_dashboard(),
                    html.Span("Dashboard", style={"color": "#a8d4ff", "fontWeight": "700",
                                                   "fontSize": "15px", "whiteSpace": "nowrap"}),
                ])
            ]),
            html.Div(style={"padding": "18px 12px 0"}, children=[
                html.Div("NAVIGATION", style={
                    "color": "rgba(168,212,255,0.5)", "fontSize": "10px", "fontWeight": "700",
                    "letterSpacing": "1.5px", "padding": "0 6px", "marginBottom": "10px",
                }),
                nav_link(icon_overview, "Overview",         "overview",      overview_href),
                nav_link(icon_sensor,   "Sensor Trends",    "sensor",        sensor_href),
                nav_link(icon_shap,     "Degradation Analysis","degradation_analysis",degradation_analysis_href),
                nav_link(icon_alert,    "Alert Log",        "alert",         alert_href),
            ]),
            html.Div(style={"flex": "1"}),
            html.Div(style={
                "padding": "16px 20px", "borderTop": "1px solid rgba(74,158,255,0.12)",
                "display": "flex", "alignItems": "center", "justifyContent": "space-between",
            }, children=[
                html.Div(children=[
                    html.Div("LOGGED IN AS", style={"color": "rgba(168,212,255,0.5)", "fontSize": "9px",
                                                     "fontWeight": "700", "letterSpacing": "1.2px",
                                                     "marginBottom": "2px"}),
                    html.Div("admin_ds", style={"color": "white", "fontWeight": "700", "fontSize": "13px"}),
                    html.Div("Admin", style={"color": "rgba(168,212,255,0.6)", "fontSize": "11px"}),
                ]),
                html.Div(id="logout-btn", n_clicks=0, style={"cursor": "pointer"},
                         children=[icon_logout()])
            ])
        ]
    )


# ─────────────────────────────────────────────
#  TOPBAR
# ─────────────────────────────────────────────

def build_topbar():
    return html.Div(
        style={
            "background": "linear-gradient(90deg, #0d2045 0%, #071530 100%)",
            "borderBottom": "1px solid rgba(74,158,255,0.18)",
            "padding": "0 28px", "height": "60px", "minHeight": "60px",
            "flexShrink": "0", "display": "flex", "alignItems": "center",
            "justifyContent": "space-between", "zIndex": "200",
        },
        children=[
            html.H1("ENGINE PROGNOSTIC MONITORING SYSTEM", style={
                "margin": "0", "fontSize": "18px", "fontWeight": "700",
                "color": "white", "letterSpacing": "1.2px",
            }),
            html.Div(id="sidebar-toggle", n_clicks=0, style={"cursor": "pointer"},
                     children=[icon_sidebar()]),
        ]
    )


# ─────────────────────────────────────────────
#  SAMPLE / FALLBACK ALERT DATA
# ─────────────────────────────────────────────

def _sample_alerts(engine_id="09"):
    base_time = datetime(2026, 4, 26, 14, 36)
    rows = [
        {"alert_no": "05", "timestamp": base_time, "severity": "critical", "rul": 20,
         "fault_type": "HPC Degradation",
         "shap": [("T30", -0.54), ("phi", -0.42), ("P30", -0.30), ("Nf", 0.15)],
         "rul_progression": [80, 60, 45, 30, 20]},
        {"alert_no": "05", "timestamp": base_time, "severity": "warning", "rul": 45,
         "fault_type": "HPC Degradation",
         "shap": [("T30", -0.41), ("phi", -0.31), ("P30", -0.22), ("Nf", 0.10)],
         "rul_progression": [90, 75, 60, 45]},
        {"alert_no": "05", "timestamp": base_time, "severity": "warning", "rul": 50,
         "fault_type": "HPC Degradation",
         "shap": [("T30", -0.38), ("phi", -0.28), ("P30", -0.20), ("Nf", 0.09)],
         "rul_progression": [95, 80, 65, 50]},
        {"alert_no": "05", "timestamp": base_time, "severity": "warning", "rul": 55,
         "fault_type": "HPC Degradation",
         "shap": [("T30", -0.35), ("phi", -0.26), ("P30", -0.18), ("Nf", 0.08)],
         "rul_progression": [100, 85, 70, 55]},
        {"alert_no": "05", "timestamp": base_time, "severity": "warning", "rul": 60,
         "fault_type": "HPC Degradation",
         "shap": [("T30", -0.33), ("phi", -0.24), ("P30", -0.16), ("Nf", 0.07)],
         "rul_progression": [105, 90, 75, 60]},
    ]
    return rows


# ─────────────────────────────────────────────
#  SUMMARY STAT CARD
# ─────────────────────────────────────────────

def summary_card(value, label, color="white", border=None):
    return html.Div(
        style={
            "flex": "1", "textAlign": "center", "padding": "18px 0",
            "borderRight": "2px solid rgba(74,158,255)" if border != "last" else "none",
        },
        children=[
            html.Div(str(value), style={"color": color, "fontSize": "28px", "fontWeight": "800",
                                         "lineHeight": "1"}),
            html.Div(label.upper(), style={"color": "rgba(168,212,255,0.6)", "fontSize": "11px",
                                            "fontWeight": "700", "letterSpacing": "1px",
                                            "marginTop": "4px"}),
        ]
    )


# ─────────────────────────────────────────────
#  SEVERITY BADGE
# ─────────────────────────────────────────────

def severity_badge(severity):
    cfg = {
        "critical": ("rgba(255,77,77,0.12)", "#ff4d4d", "#ff4d4d"),
        "warning":  ("rgba(255,217,61,0.10)", "#ffd93d", "#ffd93d"),
        "resolved": ("rgba(0,200,100,0.12)",  "#00c875", "#00c875"),
    }
    c = cfg.get(severity, cfg["warning"])
    return html.Span(
        severity.upper(),
        style={
            "display": "inline-block",
            "background": c[0], "color": c[1], "border": f"1.5px solid {c[2]}",
            "borderRadius": "4px", "padding": "2px 8px",
            "fontSize": "10px", "fontWeight": "700", "letterSpacing": "0.5px",
            "lineHeight": "1.4",
        }
    )


# ─────────────────────────────────────────────
#  ALERT TABLE ROW
# ─────────────────────────────────────────────

def alert_table_row(idx, alert, is_selected=False):
    ts = alert["timestamp"].strftime("%Y/%m/%d %H:%M")
    status = alert.get("status", "active")

    # Action button based on status
    _btn_style = {
        "background": "linear-gradient(90deg, #1a6fd4 0%, #2a85f0 100%)",
        "color": "white", "border": "none", "borderRadius": "4px",
        "padding": "4px 10px", "fontSize": "10px", "fontWeight": "700",
        "cursor": "pointer", "letterSpacing": "0.3px",
        "boxShadow": "0 1px 4px rgba(42,133,240,0.3)",
    }
    if status == "active":
        action_btn = html.Button("Acknowledge", id={"type": "ack-btn", "index": idx},
                                  n_clicks=0, style=_btn_style)
    elif status == "acknowledged":
        action_btn = html.Button("Resolve", id={"type": "resolve-btn", "index": idx},
                                  n_clicks=0, style=_btn_style)
    else:
        action_btn = html.Span("Resolved", style={"color": "#00c875", "fontSize": "10px", "fontWeight": "700"})

    row_style = {
        "display": "grid",
        "gridTemplateColumns": "40px 1fr 80px 50px 90px",
        "alignItems": "center",
        "padding": "14px 18px",
        "borderLeft": "3px solid #4a9eff" if is_selected else "3px solid transparent",
        "background": "rgba(74,158,255,0.08)" if is_selected else "transparent",
        "borderBottom": "1px solid rgba(74,158,255,0.08)",
    }

    return html.Div(style=row_style, children=[
        # Clickable zone: everything except the action cell
        html.Div(
            id={"type": "alert-row", "index": idx}, n_clicks=0,
            style={"display": "contents", "cursor": "pointer"},
            children=[
                html.Span(alert["alert_no"], style={"color": "white", "fontSize": "13px", "fontWeight": "600"}),
                html.Span(ts, style={"color": "#a8d4ff", "fontSize": "13px"}),
                html.Div(style={"textAlign": "center"}, children=[severity_badge(alert["severity"])]),
                html.Span(str(alert["rul"]), style={"color": "white", "fontSize": "13px",
                                                     "fontWeight": "700", "textAlign": "center"}),
            ]
        ),
        # Action cell lives OUTSIDE the clickable div — no bubbling
        html.Div(style={"display": "flex", "justifyContent": "center"}, children=[action_btn]),
    ])


# ─────────────────────────────────────────────
#  RUL PROGRESSION SPARKLINE
# ─────────────────────────────────────────────

def build_rul_sparkline(progression, crit_thresh=30, warn_thresh=62):
    """RUL progression chart. X-axis starts at cycle 45 (like overview.py)."""
    x = list(range(45, 45 + len(progression)))
    y = progression

    fig = go.Figure()

    # Single blue line, thin, no markers
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(color="#4a9eff", width=1.5),
        hovertemplate="Cycle %{x}<br>RUL: %{y:.1f}<extra></extra>",
    ))

    # Threshold lines
    x_end = x[-1] if x else 50
    x_start = x[0] if x else 45
    fig.add_shape(type="line", x0=x_start, x1=x_end, y0=warn_thresh, y1=warn_thresh,
                  line=dict(color="#ffd93d", width=1, dash="dot"))
    fig.add_shape(type="line", x0=x_start, x1=x_end, y0=crit_thresh, y1=crit_thresh,
                  line=dict(color="#ff4d4d", width=1, dash="dot"))

    # Threshold value labels
    fig.add_annotation(x=x_end, y=warn_thresh, text=f"  {warn_thresh}",
                       showarrow=False, font=dict(color="#ffd93d", size=9), xanchor="left")
    fig.add_annotation(x=x_end, y=crit_thresh, text=f"  {crit_thresh}",
                       showarrow=False, font=dict(color="#ff4d4d", size=9), xanchor="left")

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=40, t=10, b=28),
        height=160,
        xaxis=dict(
            showgrid=False, color="#a8d4ff", tickfont=dict(size=9),
            zeroline=False,
            range=[x_start, x_end] if len(x) > 1 else None,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(74,158,255,0.08)",
            color="#a8d4ff", tickfont=dict(size=9), zeroline=False,
            title=dict(text="RUL", font=dict(size=9, color="#a8d4ff")),
        ),
        showlegend=False,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0d1e3a", bordercolor="rgba(74,158,255,0.4)",
            font=dict(color="white", size=11),
        ),
    )

    return fig


# ─────────────────────────────────────────────
#  SHAP MINI BAR
# ─────────────────────────────────────────────

def shap_mini_bars(shap_values):
    max_abs = max(abs(v) for _, v in shap_values) or 1
    rows = []
    for name, val in shap_values:
        pct = min(100, int(abs(val) / max_abs * 100))
        color = "#ff4d4d" if val < -0.4 else "#7b61ff" if val < -0.2 else "#f5a623" if val < 0 else "#00c875"
        rows.append(
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "8px"},
                children=[
                    html.Span(name, style={"color": "#a8d4ff", "fontSize": "12px",
                                            "width": "32px", "flexShrink": "0"}),
                    html.Div(
                        style={"flex": "1", "background": "rgba(255,255,255,0.05)",
                               "borderRadius": "4px", "height": "8px", "position": "relative"},
                        children=[
                            html.Div(style={
                                "width": f"{pct}%", "height": "100%", "borderRadius": "4px",
                                "background": color,
                            })
                        ]
                    ),
                    html.Span(f"{val:+.2f}", style={
                        "color": color, "fontSize": "12px", "fontWeight": "700",
                        "width": "42px", "textAlign": "right", "flexShrink": "0",
                    }),
                ]
            )
        )
    return rows


# ─────────────────────────────────────────────
#  ALERT DETAIL PANEL
# ─────────────────────────────────────────────

def alert_detail_panel(alert):
    ts = alert["timestamp"].strftime("%Y/%m/%d %H:%M")

    children = [
        html.Div(
            style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "6px"},
            children=[
                html.H3(f"ALERT #{alert['alert_no']}",
                        style={"margin": "0", "color": "white", "fontSize": "18px", "fontWeight": "800"}),
            ]
        ),
        html.Div(
            style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "20px"},
            children=[
                html.Span(ts, style={"color": "#a8d4ff", "fontSize": "13px"}),
                severity_badge(alert["severity"]),
            ]
        ),

        html.Div("RUL PROGRESSION", style={
            "color": "#4a9eff", "fontSize": "11px", "fontWeight": "700",
            "letterSpacing": "1px", "marginBottom": "8px",
        }),
        html.Div(
            style={
                "background": "rgba(10,20,45,0.5)", "borderRadius": "10px",
                "border": "1px solid rgba(74,158,255,0.1)", "marginBottom": "22px",
            },
            children=[
                dcc.Graph(
                    figure=build_rul_sparkline(
                        alert["rul_progression"],
                        crit_thresh=alert.get("crit_thresh", 30),
                        warn_thresh=alert.get("warn_thresh", 62),
                    ),
                    config={"displayModeBar": False},
                    style={"height": "160px"},
                )
            ]
        ),

        html.Div("ALERT DETAILS", style={
            "color": "#4a9eff", "fontSize": "11px", "fontWeight": "700",
            "letterSpacing": "1px", "marginBottom": "10px",
        }),
        html.Div(
            style={"display": "flex", "justifyContent": "space-between",
                   "padding": "8px 0", "borderBottom": "1px solid rgba(74,158,255,0.08)"},
            children=[
                html.Span("Predicted RUL", style={"color": "#a8d4ff", "fontSize": "13px"}),
                html.Span(f"{alert['rul']} cycles", style={"color": "#ff6b6b", "fontSize": "13px",
                                                             "fontWeight": "700"}),
            ]
        ),
        html.Div(
            style={"display": "flex", "justifyContent": "space-between",
                   "padding": "8px 0", "marginBottom": "22px"},
            children=[
                html.Span("Fault Type", style={"color": "#a8d4ff", "fontSize": "13px"}),
                html.Span(alert["fault_type"], style={"color": "white", "fontSize": "13px",
                                                        "fontWeight": "700"}),
            ]
        ),
    ]

    # Only render SHAP section if data is present
    if alert.get("shap"):
        children += [
            html.Div("SHAP AT TRIGGER", style={
                "color": "#4a9eff", "fontSize": "11px", "fontWeight": "700",
                "letterSpacing": "1px", "marginBottom": "12px",
            }),
            html.Div(shap_mini_bars(alert["shap"])),
        ]

    return html.Div(
        style={
            "background": "transparent",
            "border": "1px solid rgba(74,158,255,0.18)",
            "borderRadius": "0px",
            "padding": "22px",
            "height": "100%",
            "overflowY": "auto",
        },
        children=children
    )


# ─────────────────────────────────────────────
#  MAIN PAGE BODY
# ─────────────────────────────────────────────

def build_alert_log_body(engine_id="09", alerts=None, selected_idx=0):
    if alerts is None:
        alerts = _sample_alerts(engine_id)

    total = len(alerts)
    active = sum(1 for a in alerts if a.get("status") == "active")
    acknowledged = sum(1 for a in alerts if a.get("status") == "acknowledged")
    resolved = sum(1 for a in alerts if a.get("status") == "resolved")

    selected_idx = max(0, min(selected_idx, total - 1)) if total else 0
    selected_alert = alerts[selected_idx] if alerts else None

    return [
        # ── Engine title ──
        html.Div(
            style={
                "background": "transparent", "borderBottom": "2px solid rgba(74,158,255,0.5)",
                "padding": "24px 22px", "marginBottom": "0px",
            },
            children=[
                html.H2(f"ENGINE-{engine_id}",
                        style={"margin": "0", "color": "white", "fontSize": "20px", "fontWeight": "800"}),
            ]
        ),

        # ── Summary stats row ──
        html.Div(
            id="alert-summary-row",
            style={
                "display": "flex", "background": "transparent",
                "border": "2px solid rgba(74,158,255,0.5)", "borderRadius": "0px",
                "marginBottom": "0px",
            },
            children=[
                summary_card(total, "Total Alerts", "white"),
                summary_card(active, "Active", "#ff4d4d"),
                summary_card(acknowledged, "Acknowledged", "#ffd93d"),
                summary_card(resolved, "Resolved", "#00c875", border="last"),
            ]
        ),

        # ── Table + detail panel ──
        html.Div(
            style={"display": "flex", "gap": "0px", "flex": "1", "minHeight": "0"},
            children=[

                # Alert table
                html.Div(
                    style={
                        "flex": "1.4", "background": "transparent",
                        "borderRight": "2px solid rgba(74,158,255,0.5)",
                        "borderRadius": "0px", "overflow": "hidden",
                        "display": "flex", "flexDirection": "column",
                    },
                    children=[
                        # Filter bar: search + dropdown
                        html.Div(
                            style={
                                "display": "flex", "alignItems": "center",
                                "justifyContent": "space-between",
                                "padding": "10px 18px",
                                "borderBottom": "1px solid rgba(74,158,255,0.15)",
                                "borderRadius": "10px",
                                "gap": "12px",
                            },
                            children=[
                                # Search bar (left)
                                html.Div(
                                    style={
                                        "flex": "1", "display": "flex", "alignItems": "center",
                                        "background": "rgba(10,20,45,0.6)",
                                        "border": "1px solid rgba(74,158,255,0.25)",
                                        "borderRadius": "6px", "padding": "0 10px",
                                    },
                                    children=[
                                        html.Span("\U0001F50D", style={"fontSize": "12px", "marginRight": "6px",
                                                                        "opacity": "0.5"}),
                                        dcc.Input(
                                            id="alert-search-input",
                                            type="text",
                                            placeholder="Search alerts...",
                                            debounce=True,
                                            style={
                                                "background": "transparent", "border": "none",
                                                "color": "white", "fontSize": "12px",
                                                "outline": "none", "width": "100%",
                                                "padding": "6px 0",
                                            },
                                        ),
                                    ]
                                ),
                                # Filter dropdown (right)
                                html.Div(
                                    style={
                                        "width": "140px",
                                        "border": "1px solid rgba(74,158,255,0.15)",
                                        "borderRadius": "6px",
                                    },
                                    children=[
                                        dcc.Dropdown(
                                            id="alert-severity-filter",
                                            options=[
                                                {"label": "All Severity", "value": "all"},
                                                {"label": "Warning", "value": "warning"},
                                                {"label": "Critical", "value": "critical"},
                                            ],
                                            value="all",
                                            clearable=False,
                                            searchable=False,
                                            className="dark-dropdown",
                                            style={"backgroundColor": "transparent", "border": "none", "fontSize": "12px"},
                                        )
                                    ]
                                ),
                            ]
                        ),
                        # Table header
                        html.Div(
                            style={
                                "display": "grid",
                                "gridTemplateColumns": "40px 1fr 80px 50px 90px",
                                "padding": "12px 18px",
                                "borderBottom": "2px solid rgba(74,158,255,0.5)",
                            },
                            children=[
                                html.Span("#", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                                       "fontWeight": "700", "letterSpacing": "0.5px"}),
                                html.Span("TIMESTAMP", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                                               "fontWeight": "700", "letterSpacing": "0.5px"}),
                                html.Span("SEVERITY", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                                              "fontWeight": "700", "letterSpacing": "0.5px",
                                                              "textAlign": "center"}),
                                html.Span("RUL", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                                         "fontWeight": "700", "letterSpacing": "0.5px",
                                                         "textAlign": "center"}),
                                html.Span("ACTION", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                                            "fontWeight": "700", "letterSpacing": "0.5px",
                                                            "textAlign": "center"}),
                            ]
                        ),
                        html.Div(
                            id="alert-table-body",
                            style={"overflowY": "auto", "flex": "1"},
                            children=[
                                alert_table_row(i, a, is_selected=(i == selected_idx))
                                for i, a in enumerate(alerts)
                            ]
                        )
                    ]
                ),

                # Detail panel
                html.Div(
                    id="alert-detail-container",
                    style={"flex": "1", "minWidth": "0"},
                    children=[alert_detail_panel(selected_alert)] if selected_alert else [
                        html.Div("No alerts to display.",
                                 style={"color": "rgba(255,255,255,0.5)", "textAlign": "center",
                                        "padding": "60px 0"})
                    ]
                )
            ]
        ),

        dcc.Store(id="alerts-data", data=[
            {**a, "timestamp": a["timestamp"].isoformat()} for a in alerts
        ]),
        dcc.Store(id="selected-alert-idx", data=selected_idx),
        dcc.Store(id="alert-filter-store", data="all"),
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_alert_log_layout(supabase=None, engine_db_id=None):
    engine_id = "—"
    alerts = []

    try:
        if supabase:
            # Fetch alert thresholds
            warn_thresh, crit_thresh = 62, 30
            try:
                t_resp = supabase.table("alert_thresholds") \
                    .select("warning_threshold, critical_threshold") \
                    .order("updated_at", desc=True) \
                    .limit(1) \
                    .execute()
                if t_resp.data:
                    warn_thresh = int(t_resp.data[0].get("warning_threshold", 62))
                    crit_thresh = int(t_resp.data[0].get("critical_threshold", 30))
            except Exception:
                pass

            # Build base query for alert_logs
            query = supabase.table("alert_logs").select("id, engine_id, triggered_at, status, acknowledged_by, acknowledged_at, resolved_at, severity")

            if engine_db_id is not None:
                query = query.eq("engine_id", engine_db_id)

            logs_resp = query.order("triggered_at", desc=True).execute()
            logs = logs_resp.data or []

            print(f"[DEBUG] alert_logs rows: {logs}")

            # Collect unique engine_ids referenced by these alerts
            engine_ids = list({log["engine_id"] for log in logs if log.get("engine_id") is not None})

            # Fetch engine details for all referenced engines in one query
            engines_lookup = {}
            if engine_ids:
                eng_resp = supabase.table("engines") \
                    .select("id, engine_id, condition_status, current_cycle, degradation_type") \
                    .in_("id", engine_ids) \
                    .execute()
                for e in (eng_resp.data or []):
                    engines_lookup[e["id"]] = e

            print(f"[DEBUG] engines lookup: {engines_lookup}")

            # If a specific engine was requested, set the page title from it
            if engine_db_id is not None and engine_db_id in engines_lookup:
                engine_id = str(engines_lookup[engine_db_id].get("engine_id", "—")).zfill(2)
            elif engines_lookup:
                # fallback: use the first engine found among the alerts
                first_eng = next(iter(engines_lookup.values()))
                engine_id = str(first_eng.get("engine_id", "—")).zfill(2)

            # Build the alerts list by joining each log with its engine row
            for i, log in enumerate(logs):
                eng = engines_lookup.get(log.get("engine_id"), {})

                # Use severity from alert_logs table directly (not engine status)
                severity = (log.get("severity") or "warning").lower().strip()
                if severity not in ("warning", "critical"):
                    severity = "warning"

                # Alert status from the table
                alert_status = (log.get("status") or "active").lower().strip()

                current_cycle = eng.get("current_cycle") or 0
                fault_type = eng.get("degradation_type") or "Unknown"

                triggered_at = log.get("triggered_at")
                try:
                    timestamp = datetime.fromisoformat(triggered_at.replace("Z", "+00:00"))
                except Exception:
                    timestamp = datetime.now()

                # Fetch actual RUL predictions for this engine's progression chart
                rul_progression = []
                latest_rul = 0
                alert_engine_id = log.get("engine_id")
                try:
                    pred_resp = supabase.table("rul_predictions") \
                        .select("cycle, predicted_rul") \
                        .eq("engine_id", alert_engine_id) \
                        .order("cycle", desc=False) \
                        .execute()
                    print(f"[DEBUG] rul_predictions for engine {alert_engine_id}: {len(pred_resp.data or [])} rows")
                    for pred_row in (pred_resp.data or []):
                        if pred_row.get("predicted_rul") is not None:
                            rul_progression.append(float(pred_row["predicted_rul"]))
                    if rul_progression:
                        latest_rul = int(round(rul_progression[-1]))
                except Exception as _e:
                    import traceback
                    print(f"[DEBUG] Failed to fetch rul_predictions: {traceback.format_exc()}")

                if not rul_progression:
                    rul_progression = [current_cycle]
                    latest_rul = current_cycle

                alerts.append({
                    "alert_no": str(i + 1).zfill(2),
                    "alert_id": log.get("id"),
                    "timestamp": timestamp,
                    "severity": severity,
                    "status": alert_status,
                    "rul": latest_rul,
                    "fault_type": fault_type,
                    "shap": [],
                    "rul_progression": rul_progression,
                    "warn_thresh": warn_thresh,
                    "crit_thresh": crit_thresh,
                })

            print(f"[DEBUG] built alerts: {alerts}")

    except Exception as e:
        import traceback
        print(f"[ERROR] alert log fetch: {traceback.format_exc()}")

    return html.Div(
        style={
            "height": "100vh", "display": "flex", "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628", "color": "white", "overflow": "hidden",
        },
        children=[
            dcc.Location(id="url-alert-log", refresh=False),
            build_topbar(),
            html.Div(
                style={"flex": "1", "display": "flex", "flexDirection": "row",
                       "overflow": "hidden", "minHeight": "0"},
                children=[
                    build_sidebar(active_page="alert", engine_db_id=engine_db_id),
                    html.Div(
                        style={"flex": "1", "overflowY": "auto",
                               "minWidth": "0", "display": "flex", "flexDirection": "column"},
                        children=build_alert_log_body(engine_id=engine_id, alerts=alerts),
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def register_alert_log_callbacks(app, supabase=None):

    @app.callback(
        Output("alert-detail-container", "children", allow_duplicate=True),
        Output("alert-table-body", "children", allow_duplicate=True),
        Output("selected-alert-idx", "data", allow_duplicate=True),
        Input({"type": "alert-row", "index": dash.ALL}, "n_clicks"),
        State("alerts-data", "data"),
        State("selected-alert-idx", "data"),
        prevent_initial_call=True,
    )
    def select_alert(n_clicks_list, alerts_data, current_idx):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        import json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        parsed = json.loads(trigger_id)

        # Ignore if the trigger came from a button click bubbling up
        if parsed.get("type") != "alert-row":
            raise dash.exceptions.PreventUpdate

        idx = parsed["index"]

        alerts = []
        for a in alerts_data:
            a = dict(a)
            a["timestamp"] = datetime.fromisoformat(a["timestamp"])
            alerts.append(a)

        selected_alert = alerts[idx]
        detail = alert_detail_panel(selected_alert)
        rows = [alert_table_row(i, a, is_selected=(i == idx)) for i, a in enumerate(alerts)]

        return detail, rows, idx

    # ── Acknowledge button callback ──
    @app.callback(
        Output("alert-table-body", "children", allow_duplicate=True),
        Output("alerts-data", "data", allow_duplicate=True),
        Output("alert-detail-container", "children", allow_duplicate=True),
        Output("alert-summary-row", "children", allow_duplicate=True),
        Output("selected-alert-idx", "data", allow_duplicate=True),
        Input({"type": "ack-btn", "index": dash.ALL}, "n_clicks"),
        State("alerts-data", "data"),
        State("session-store", "data"),
        State("selected-alert-idx", "data"),
        prevent_initial_call=True,
    )
    def acknowledge_alert(n_clicks_list, alerts_data, session, selected_idx):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        import json as _json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        idx = _json.loads(trigger_id)["index"]

        user_id = session.get("user_id") if session else None
        alert_id = alerts_data[idx].get("alert_id")

        if supabase and alert_id:
            now = datetime.now(timezone.utc).isoformat()
            try:
                update_data = {
                    "status": "acknowledged",
                    "acknowledged_at": now,
                }
                if user_id:
                    update_data["acknowledged_by"] = user_id
                supabase.table("alert_logs").update(update_data).eq("id", alert_id).execute()
                print(f"[ALERT] Acknowledged alert {alert_id} by user {user_id}")
            except Exception:
                import traceback
                print(f"[ALERT][ERROR] Failed to acknowledge:\n{traceback.format_exc()}")

        # Update local data
        alerts_data[idx]["status"] = "acknowledged"

        alerts = []
        for a in alerts_data:
            a = dict(a)
            a["timestamp"] = datetime.fromisoformat(a["timestamp"])
            alerts.append(a)

        rows = [alert_table_row(i, a, is_selected=(i == idx)) for i, a in enumerate(alerts)]
        detail = alert_detail_panel(alerts[idx]) if idx < len(alerts) else []

        # Rebuild summary
        total = len(alerts)
        active_count = sum(1 for a in alerts if a.get("status") == "active")
        ack_count = sum(1 for a in alerts if a.get("status") == "acknowledged")
        res_count = sum(1 for a in alerts if a.get("status") == "resolved")
        summary = [
            summary_card(total, "Total Alerts", "white"),
            summary_card(active_count, "Active", "#ff4d4d"),
            summary_card(ack_count, "Acknowledged", "#ffd93d"),
            summary_card(res_count, "Resolved", "#00c875", border="last"),
        ]
        return rows, alerts_data, detail, summary, idx

    # ── Resolve button callback ──
    @app.callback(
        Output("alert-table-body", "children", allow_duplicate=True),
        Output("alerts-data", "data", allow_duplicate=True),
        Output("alert-detail-container", "children", allow_duplicate=True),
        Output("alert-summary-row", "children", allow_duplicate=True),
        Output("selected-alert-idx", "data", allow_duplicate=True),
        Input({"type": "resolve-btn", "index": dash.ALL}, "n_clicks"),
        State("alerts-data", "data"),
        State("session-store", "data"),
        State("selected-alert-idx", "data"),
        prevent_initial_call=True,
    )
    def resolve_alert(n_clicks_list, alerts_data, session, selected_idx):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        import json as _json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        idx = _json.loads(trigger_id)["index"]

        alert_id = alerts_data[idx].get("alert_id")

        if supabase and alert_id:
            now = datetime.now(timezone.utc).isoformat()
            try:
                supabase.table("alert_logs").update({
                    "status": "resolved",
                    "resolved_at": now,
                }).eq("id", alert_id).execute()
                print(f"[ALERT] Resolved alert {alert_id}")
            except Exception:
                import traceback
                print(f"[ALERT][ERROR] Failed to resolve:\n{traceback.format_exc()}")

        # Update local data
        alerts_data[idx]["status"] = "resolved"

        alerts = []
        for a in alerts_data:
            a = dict(a)
            a["timestamp"] = datetime.fromisoformat(a["timestamp"])
            alerts.append(a)

        rows = [alert_table_row(i, a, is_selected=(i == idx)) for i, a in enumerate(alerts)]
        detail = alert_detail_panel(alerts[idx]) if idx < len(alerts) else []

        # Rebuild summary
        total = len(alerts)
        active_count = sum(1 for a in alerts if a.get("status") == "active")
        ack_count = sum(1 for a in alerts if a.get("status") == "acknowledged")
        res_count = sum(1 for a in alerts if a.get("status") == "resolved")
        summary = [
            summary_card(total, "Total Alerts", "white"),
            summary_card(active_count, "Active", "#ff4d4d"),
            summary_card(ack_count, "Acknowledged", "#ffd93d"),
            summary_card(res_count, "Resolved", "#00c875", border="last"),
        ]
        return rows, alerts_data, detail, summary, idx

    # ── Filter by severity dropdown + search ──
    @app.callback(
        Output("alert-table-body", "children", allow_duplicate=True),
        Input("alert-severity-filter", "value"),
        Input("alert-search-input", "value"),
        State("alerts-data", "data"),
        State("selected-alert-idx", "data"),
        prevent_initial_call=True,
    )
    def filter_alerts(severity_filter, search_text, alerts_data, selected_idx):
        alerts = []
        for a in alerts_data:
            a = dict(a)
            a["timestamp"] = datetime.fromisoformat(a["timestamp"])
            alerts.append(a)

        # Filter by severity
        if severity_filter and severity_filter != "all":
            alerts = [a for a in alerts if a.get("severity") == severity_filter]

        # Filter by search text
        if search_text:
            search_lower = search_text.lower()
            alerts = [a for a in alerts if (
                search_lower in a.get("alert_no", "").lower() or
                search_lower in a["timestamp"].strftime("%Y/%m/%d %H:%M").lower() or
                search_lower in a.get("severity", "").lower() or
                search_lower in str(a.get("rul", "")).lower()
            )]

        rows = [alert_table_row(i, a, is_selected=(i == selected_idx)) for i, a in enumerate(alerts)]
        if not rows:
            rows = [html.Div("No alerts matching filter.",
                             style={"color": "rgba(168,212,255,0.5)", "textAlign": "center",
                                    "padding": "30px 0", "fontSize": "13px"})]
        return rows

    @app.callback(
        Output("sidebar", "style"),
        Output("sidebar-state", "data"),
        Input("sidebar-toggle", "n_clicks"),
        State("sidebar-state", "data"),
        prevent_initial_call=True,
    )
    def toggle_sidebar(n, is_open):
        is_open = not is_open
        base = {
            "flexShrink": "0", "height": "100%", "background": "#0d1e3a",
            "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex", "flexDirection": "column",
            "overflow": "hidden", "transition": "width 0.3s ease",
        }
        return ({**base, "width": "210px"}, True) if is_open else ({**base, "width": "0px"}, False)


# ─────────────────────────────────────────────
#  STANDALONE RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True)
    app.layout = html.Div([
        dcc.Store(id="sidebar-state", data=True),
        create_alert_log_layout()
    ])
    register_alert_log_callbacks(app)
    app.run(debug=True)
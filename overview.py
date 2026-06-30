import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import base64
import numpy as np

# ─────────────────────────────────────────────
#  SVG ICON HELPERS
# ─────────────────────────────────────────────

def _svg_img(svg_str, size="22px"):
    b64 = base64.b64encode(svg_str.strip().encode("utf-8")).decode("utf-8")
    return html.Img(
        src=f"data:image/svg+xml;base64,{b64}",
        style={"width": size, "height": size, "flexShrink": "0"},
    )


def icon_dashboard():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1"/>
      <rect x="14" y="3" width="7" height="7" rx="1"/>
      <rect x="3" y="14" width="7" height="7" rx="1"/>
      <rect x="14" y="14" width="7" height="7" rx="1"/>
    </svg>''')


def icon_overview():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="7"/>
      <line x1="16.5" y1="16.5" x2="21" y2="21"/>
    </svg>''')


def icon_sensor():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="3 17 7 11 11 14 15 8 21 8"/>
      <line x1="3" y1="21" x2="21" y2="21"/>
    </svg>''')


def icon_shap():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 2v3M12 19v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12
               M2 12h3M19 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/>
    </svg>''')


def icon_alert():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>''')


def icon_sidebar():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <line x1="9" y1="3" x2="9" y2="21"/>
    </svg>''', size="26px")


def icon_logout():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#ff4d4d" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>''', size="22px")


# ─────────────────────────────────────────────
#  RUL LINE CHART
# ─────────────────────────────────────────────

def build_rul_chart(rul_value: int = 120, total_cycles: int = 142):
    """
    Actual RUL counts down from ~125 to rul_value over total_cycles.
    Predicted line slightly deviates then converges at the endpoint.
    """
    x = np.linspace(0, total_cycles, total_cycles + 1)
    start = 125
    actual = np.linspace(start, rul_value, len(x))
    noise = np.random.RandomState(42).normal(0, 1.2, len(x))
    predicted = actual + noise
    predicted[-1] = rul_value  # converge at end

    warn_thresh = 62
    crit_thresh = 30

    fig = go.Figure()

    # Actual line
    fig.add_trace(go.Scatter(
        x=x, y=actual,
        mode="lines",
        name="Actual",
        line=dict(color="#4a9eff", width=2),
    ))

    # Predicted line (dashed)
    fig.add_trace(go.Scatter(
        x=x, y=predicted,
        mode="lines",
        name="Predicted",
        line=dict(color="#ffffff", width=1.5, dash="dash"),
    ))

    # Endpoint marker
    fig.add_trace(go.Scatter(
        x=[total_cycles], y=[rul_value],
        mode="markers",
        showlegend=False,
        marker=dict(color="#f5a623", size=9, symbol="circle"),
    ))

    # Warning threshold line
    fig.add_shape(type="line", x0=0, x1=total_cycles, y0=warn_thresh, y1=warn_thresh,
                  line=dict(color="#ffd93d", width=1, dash="dot"))
    fig.add_annotation(x=total_cycles, y=warn_thresh, text="warn",
                       font=dict(color="#ffd93d", size=10), showarrow=False, xanchor="left", xshift=4)

    # Critical threshold line
    fig.add_shape(type="line", x0=0, x1=total_cycles, y0=crit_thresh, y1=crit_thresh,
                  line=dict(color="#ff4d4d", width=1, dash="dot"))
    fig.add_annotation(x=total_cycles, y=crit_thresh, text="crit",
                       font=dict(color="#ff4d4d", size=10), showarrow=False, xanchor="left", xshift=4)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=50, t=10, b=10),
        height=200,
        legend=dict(
            orientation="h", x=0, y=1.15,
            font=dict(color="#a8d4ff", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=False,
            color="#a8d4ff",
            tickfont=dict(size=10),
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(74,158,255,0.1)",
            color="#a8d4ff",
            tickfont=dict(size=10),
            zeroline=False,
            range=[0, 135],
        ),
        hovermode="x unified",
    )
    return fig


# ─────────────────────────────────────────────
#  TOP DRIVERS (SHAP) BAR CHART
# ─────────────────────────────────────────────

def build_shap_chart():
    sensors = ["T30", "phi", "P30", "Nf", "W31", "BPR"]
    values = [-0.42, -0.33, -0.28, 0.20, 0.14, 0.09]

    colors = [
        "#ff6b6b" if v < -0.3 else
        "#f5a623" if v < 0 else
        "#4a9eff" if v < 0.15 else
        "#00c875"
        for v in values
    ]

    fig = go.Figure(go.Bar(
        x=values,
        y=sensors,
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.2f}" for v in values],
        textposition="outside",
        textfont=dict(color="#a8d4ff", size=11),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=40, t=10, b=10),
        height=220,
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(74,158,255,0.1)",
            zeroline=True,
            zerolinecolor="rgba(74,158,255,0.3)",
            color="#a8d4ff",
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=False,
            color="#a8d4ff",
            tickfont=dict(size=12, color="white"),
            autorange="reversed",
        ),
    )
    return fig


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────

def build_sidebar(active_page="overview"):
    nav_item_base = {
        "display": "flex",
        "alignItems": "center",
        "gap": "10px",
        "padding": "10px 14px",
        "borderRadius": "10px",
        "cursor": "pointer",
        "fontSize": "14px",
        "fontWeight": "500",
        "color": "#a8d4ff",
        "marginBottom": "4px",
        "transition": "background 0.2s",
    }

    def nav_link(icon_fn, label, page_key, href="/"):
        is_active = active_page == page_key
        style = {**nav_item_base}
        if is_active:
            style.update({
                "background": "rgba(74,158,255,0.18)",
                "color": "white",
                "fontWeight": "700",
                "borderLeft": "3px solid #4a9eff",
                "paddingLeft": "11px",
            })
        return html.A(
            href=href,
            style={"textDecoration": "none"},
            children=[
                html.Div(style=style, children=[icon_fn(), html.Span(label)])
            ]
        )

    return html.Div(
        id="sidebar",
        style={
            "width": "210px",
            "flexShrink": "0",
            "minHeight": "100vh",
            "background": "#0d1e3a",
            "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex",
            "flexDirection": "column",
            "padding": "0",
            "overflow": "hidden",
            "transition": "width 0.3s ease",
        },
        children=[
            # ── Dashboard top link ──
            html.A(
                href="/dashboard",
                style={"textDecoration": "none"},
                children=[
                    html.Div(
                        style={
                            "padding": "20px 20px 18px",
                            "borderBottom": "1px solid rgba(74,158,255,0.12)",
                            "display": "flex",
                            "alignItems": "center",
                            "gap": "10px",
                            "cursor": "pointer",
                        },
                        children=[
                            icon_dashboard(),
                            html.Span(
                                "Dashboard",
                                style={
                                    "color": "#a8d4ff",
                                    "fontWeight": "700",
                                    "fontSize": "15px",
                                    "whiteSpace": "nowrap",
                                }
                            ),
                        ]
                    )
                ]
            ),

            # ── Navigation links ──
            html.Div(
                style={"padding": "18px 12px 0"},
                children=[
                    html.Div(
                        "NAVIGATION",
                        style={
                            "color": "rgba(168,212,255,0.5)",
                            "fontSize": "10px",
                            "fontWeight": "700",
                            "letterSpacing": "1.5px",
                            "padding": "0 6px",
                            "marginBottom": "10px",
                            "whiteSpace": "nowrap",
                        }
                    ),
                    nav_link(icon_overview, "Overview",        "overview",     "/overview"),
                    nav_link(icon_sensor,   "Sensor Trends",   "sensor",       "/sensor-trends"),
                    nav_link(icon_shap,     "Explainability AI","explainability","/explainability"),
                    nav_link(icon_alert,    "Alert Log",       "alert",        "/alert-log"),
                ]
            ),

            # ── Spacer ──
            html.Div(style={"flex": "1"}),

            # ── Logged-in user + logout ──
            html.Div(
                style={
                    "padding": "16px 20px",
                    "borderTop": "1px solid rgba(74,158,255,0.12)",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "gap": "8px",
                },
                children=[
                    html.Div(
                        style={"minWidth": "0"},
                        children=[
                            html.Div(
                                "LOGGED IN AS",
                                style={
                                    "color": "rgba(168,212,255,0.5)",
                                    "fontSize": "9px",
                                    "fontWeight": "700",
                                    "letterSpacing": "1.2px",
                                    "marginBottom": "2px",
                                    "whiteSpace": "nowrap",
                                }
                            ),
                            html.Div(
                                "admin_ds",
                                style={
                                    "color": "white",
                                    "fontWeight": "700",
                                    "fontSize": "13px",
                                    "whiteSpace": "nowrap",
                                    "overflow": "hidden",
                                    "textOverflow": "ellipsis",
                                }
                            ),
                            html.Div(
                                "Administrator",
                                style={
                                    "color": "rgba(168,212,255,0.6)",
                                    "fontSize": "11px",
                                    "whiteSpace": "nowrap",
                                }
                            ),
                        ]
                    ),
                    html.Div(
                        id="logout-btn",
                        n_clicks=0,
                        style={"cursor": "pointer", "flexShrink": "0"},
                        children=[icon_logout()]
                    )
                ]
            )
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
            "padding": "0 28px",
            "height": "60px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "flexShrink": "0",
        },
        children=[
            html.H1(
                "ENGINE PROGNOSTIC MONITORING SYSTEM",
                style={
                    "margin": "0",
                    "fontSize": "18px",
                    "fontWeight": "700",
                    "color": "white",
                    "letterSpacing": "1.2px",
                }
            ),
            html.Div(
                id="sidebar-toggle",
                n_clicks=0,
                style={"cursor": "pointer"},
                children=[icon_sidebar()]
            ),
        ]
    )


# ─────────────────────────────────────────────
#  STATUS BADGE
# ─────────────────────────────────────────────

def status_badge(status: str):
    cfg = {
        "healthy":  {"bg": "rgba(0,200,100,0.18)", "border": "#00c875", "color": "#00c875"},
        "warning":  {"bg": "rgba(255,217,61,0.18)", "border": "#ffd93d", "color": "#ffd93d"},
        "critical": {"bg": "rgba(255,77,77,0.18)",  "border": "#ff4d4d", "color": "#ff4d4d"},
    }
    c = cfg.get(status.lower(), cfg["healthy"])
    return html.Span(
        status.upper(),
        style={
            "background": c["bg"],
            "color": c["color"],
            "border": f"1px solid {c['border']}",
            "borderRadius": "20px",
            "padding": "3px 12px",
            "fontSize": "11px",
            "fontWeight": "700",
            "letterSpacing": "0.8px",
        }
    )


# ─────────────────────────────────────────────
#  CARD WRAPPER
# ─────────────────────────────────────────────

def card(children, style_extra=None):
    base = {
        "background": "#101e36",
        "border": "1px solid rgba(74,158,255,0.18)",
        "borderRadius": "14px",
        "padding": "20px 22px",
    }
    if style_extra:
        base.update(style_extra)
    return html.Div(style=base, children=children)


def card_title(text):
    return html.Div(
        text,
        style={"color": "white", "fontWeight": "700", "fontSize": "16px", "marginBottom": "14px"}
    )


# ─────────────────────────────────────────────
#  MAIN CONTENT: OVERVIEW PAGE
# ─────────────────────────────────────────────

def build_overview_content(engine_id="01", status="healthy", rul=120, degradation=80):
    degrade_color = (
        "#00c875" if degradation >= 70 else
        "#ffd93d" if degradation >= 40 else
        "#ff4d4d"
    )

    if degradation >= 70:
        degrade_label = ("No Degradation Detected", "#00c875", "rgba(0,200,117,0.12)", "#00c875")
    elif degradation >= 40:
        degrade_label = ("Moderate Degradation", "#ffd93d", "rgba(255,217,61,0.12)", "#ffd93d")
    else:
        degrade_label = ("Severe Degradation", "#ff4d4d", "rgba(255,77,77,0.12)", "#ff4d4d")

    sensor_list = [
        ("T30", "HPC outlet temperature"),
        ("P30", "HPC outlet pressure"),
        ("Nf",  "Fan speed"),
        ("phi", "Fuel-air ratio"),
        ("W31", "HPT coolant bleed"),
    ]

    return html.Div(
        style={
            "flex": "1",
            "display": "flex",
            "flexDirection": "column",
            "minWidth": "0",
            "height": "100vh",       # ← full viewport height
            "overflow": "hidden",    # ← prevent outer scroll
        },
        children=[
            # ── Fixed topbar (stays at top always) ──
            html.Div(
                style={
                    "background": "linear-gradient(90deg, #0d2045 0%, #071530 100%)",
                    "borderBottom": "1px solid rgba(74,158,255,0.18)",
                    "padding": "0 28px",
                    "height": "60px",
                    "minHeight": "60px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "flexShrink": "0",   # ← never shrink
                    "zIndex": "100",
                },
                children=[
                    html.H1(
                        "ENGINE PROGNOSTIC MONITORING SYSTEM",
                        style={
                            "margin": "0",
                            "fontSize": "18px",
                            "fontWeight": "700",
                            "color": "white",
                            "letterSpacing": "1.2px",
                        }
                    ),
                    html.Div(
                        id="sidebar-toggle",
                        n_clicks=0,
                        style={"cursor": "pointer"},
                        children=[icon_sidebar()]
                    ),
                ]
            ),

            # ── Scrollable content below topbar ──
            html.Div(
                style={
                    "flex": "1",
                    "overflowY": "auto",   # ← only this scrolls
                    "padding": "24px 28px",
                },
                children=[
                    # Engine title row
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "14px", "marginBottom": "22px"},
                        children=[
                            html.H2(
                                f"ENGINE-{engine_id}",
                                style={"margin": "0", "color": "white", "fontSize": "22px", "fontWeight": "800"}
                            ),
                            status_badge(status),
                        ]
                    ),

                    # Row 1: RUL Chart + RUL Panel
                    html.Div(
                        style={"display": "flex", "gap": "20px", "marginBottom": "20px"},
                        children=[
                            card(
                                style_extra={"flex": "3"},
                                children=[
                                    card_title("Predicted RUL"),
                                    dcc.Graph(
                                        figure=build_rul_chart(rul_value=rul),
                                        config={"displayModeBar": False},
                                        style={"height": "200px"},
                                    )
                                ]
                            ),
                            card(
                                style_extra={"flex": "1", "display": "flex", "flexDirection": "column",
                                             "alignItems": "center", "justifyContent": "center", "gap": "16px"},
                                children=[
                                    html.Div("Remaining Useful Life",
                                             style={"color": "#a8d4ff", "fontSize": "13px", "fontWeight": "600",
                                                    "textAlign": "center", "letterSpacing": "0.4px"}),
                                    html.Div(
                                        style={"textAlign": "center"},
                                        children=[
                                            html.Div(str(rul),
                                                     style={"color": "#00c875", "fontSize": "58px",
                                                            "fontWeight": "800", "lineHeight": "1"}),
                                            html.Div("cycles", style={"color": "#a8d4ff", "fontSize": "14px",
                                                                       "marginTop": "4px"})
                                        ]
                                    ),
                                    html.Div(
                                        style={"width": "100%", "borderTop": "1px solid rgba(74,158,255,0.18)",
                                               "paddingTop": "14px", "display": "flex",
                                               "justifyContent": "space-between", "alignItems": "center"},
                                        children=[
                                            html.Span("Degradation", style={"color": "#a8d4ff", "fontSize": "12px"}),
                                            html.Span(f"{degradation}%", style={"color": degrade_color,
                                                                                  "fontWeight": "700", "fontSize": "14px"})
                                        ]
                                    ),
                                    html.Div(
                                        degrade_label[0],
                                        style={
                                            "width": "100%", "textAlign": "center",
                                            "background": degrade_label[2],
                                            "border": f"1.5px solid {degrade_label[3]}",
                                            "borderRadius": "10px", "color": degrade_label[1],
                                            "fontSize": "12px", "fontWeight": "700", "padding": "8px 0",
                                        }
                                    )
                                ]
                            )
                        ]
                    ),

                    # Row 2: Sensor Trends + Top Drivers
                    html.Div(
                        style={"display": "flex", "gap": "20px"},
                        children=[
                            card(
                                style_extra={"flex": "1"},
                                children=[
                                    card_title("Sensor Trends"),
                                    html.Div(
                                        style={"display": "flex", "flexDirection": "column", "gap": "0"},
                                        children=[
                                            html.Div(
                                                style={
                                                    "display": "flex", "alignItems": "center",
                                                    "justifyContent": "space-between",
                                                    "padding": "10px 0",
                                                    "borderBottom": "1px solid rgba(74,158,255,0.1)",
                                                    "cursor": "pointer",
                                                },
                                                children=[
                                                    html.Span(f"{code} ({label})",
                                                              style={"color": "#a8d4ff", "fontSize": "13px"}),
                                                    html.Span("→", style={"color": "rgba(74,158,255,0.5)", "fontSize": "14px"}),
                                                ]
                                            )
                                            for code, label in sensor_list
                                        ]
                                    )
                                ]
                            ),
                            card(
                                style_extra={"flex": "1"},
                                children=[
                                    card_title("Top Drivers"),
                                    dcc.Graph(
                                        figure=build_shap_chart(),
                                        config={"displayModeBar": False},
                                        style={"height": "220px"},
                                    )
                                ]
                            ),
                        ]
                    )
                ]
            )
        ]
    )

def build_overview_body(engine_id="01", status="healthy", rul=120, degradation=80):
    """Returns just the scrollable inner content children (a list)."""
    degrade_color = (
        "#00c875" if degradation >= 70 else
        "#ffd93d" if degradation >= 40 else
        "#ff4d4d"
    )
    if degradation >= 70:
        degrade_label = ("No Degradation Detected", "#00c875", "rgba(0,200,117,0.12)", "#00c875")
    elif degradation >= 40:
        degrade_label = ("Moderate Degradation", "#ffd93d", "rgba(255,217,61,0.12)", "#ffd93d")
    else:
        degrade_label = ("Severe Degradation", "#ff4d4d", "rgba(255,77,77,0.12)", "#ff4d4d")

    sensor_list = [
        ("T30", "HPC outlet temperature"),
        ("P30", "HPC outlet pressure"),
        ("Nf",  "Fan speed"),
        ("phi", "Fuel-air ratio"),
        ("W31", "HPT coolant bleed"),
    ]

    return [
        # Engine title row
        html.Div(
            style={"display": "flex", "alignItems": "center", "gap": "14px", "marginBottom": "22px"},
            children=[
                html.H2(f"ENGINE-{engine_id}",
                        style={"margin": "0", "color": "white", "fontSize": "22px", "fontWeight": "800"}),
                status_badge(status),
            ]
        ),

        # Row 1: RUL Chart + RUL Panel
        html.Div(
            style={"display": "flex", "gap": "20px", "marginBottom": "20px"},
            children=[
                card(
                    style_extra={"flex": "3"},
                    children=[
                        card_title("Predicted RUL"),
                        dcc.Graph(
                            figure=build_rul_chart(rul_value=rul),
                            config={"displayModeBar": False},
                            style={"height": "200px"},
                        )
                    ]
                ),
                card(
                    style_extra={"flex": "1", "display": "flex", "flexDirection": "column",
                                 "alignItems": "center", "justifyContent": "center", "gap": "16px"},
                    children=[
                        html.Div("Remaining Useful Life",
                                 style={"color": "#a8d4ff", "fontSize": "13px", "fontWeight": "600",
                                        "textAlign": "center"}),
                        html.Div(style={"textAlign": "center"}, children=[
                            html.Div(str(rul), style={"color": "#00c875", "fontSize": "58px",
                                                       "fontWeight": "800", "lineHeight": "1"}),
                            html.Div("cycles", style={"color": "#a8d4ff", "fontSize": "14px", "marginTop": "4px"})
                        ]),
                        html.Div(
                            style={"width": "100%", "borderTop": "1px solid rgba(74,158,255,0.18)",
                                   "paddingTop": "14px", "display": "flex",
                                   "justifyContent": "space-between", "alignItems": "center"},
                            children=[
                                html.Span("Degradation", style={"color": "#a8d4ff", "fontSize": "12px"}),
                                html.Span(f"{degradation}%", style={"color": degrade_color,
                                                                      "fontWeight": "700", "fontSize": "14px"})
                            ]
                        ),
                        html.Div(degrade_label[0], style={
                            "width": "100%", "textAlign": "center",
                            "background": degrade_label[2],
                            "border": f"1.5px solid {degrade_label[3]}",
                            "borderRadius": "10px", "color": degrade_label[1],
                            "fontSize": "12px", "fontWeight": "700", "padding": "8px 0",
                        })
                    ]
                )
            ]
        ),

        # Row 2: Sensor Trends + Top Drivers
        html.Div(
            style={"display": "flex", "gap": "20px"},
            children=[
                card(
                    style_extra={"flex": "1"},
                    children=[
                        card_title("Sensor Trends"),
                        html.Div(
                            style={"display": "flex", "flexDirection": "column"},
                            children=[
                                html.Div(
                                    style={"display": "flex", "alignItems": "center",
                                           "justifyContent": "space-between", "padding": "10px 0",
                                           "borderBottom": "1px solid rgba(74,158,255,0.1)",
                                           "cursor": "pointer"},
                                    children=[
                                        html.Span(f"{code} ({label})",
                                                  style={"color": "#a8d4ff", "fontSize": "13px"}),
                                        html.Span("→", style={"color": "rgba(74,158,255,0.5)", "fontSize": "14px"}),
                                    ]
                                )
                                for code, label in sensor_list
                            ]
                        )
                    ]
                ),
                card(
                    style_extra={"flex": "1"},
                    children=[
                        card_title("Top Drivers"),
                        dcc.Graph(
                            figure=build_shap_chart(),
                            config={"displayModeBar": False},
                            style={"height": "220px"},
                        )
                    ]
                ),
            ]
        )
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_overview_layout(supabase, engine_db_id=None):
    # Defaults
    engine_id   = "01"
    status      = "healthy"
    rul         = 120
    degradation = 80

    try:
        if supabase and engine_db_id is not None:
            # Fetch engine row by PK
            eng_resp = supabase.table("engines") \
                .select("*") \
                .eq("id", engine_db_id) \
                .single() \
                .execute()
            engine = eng_resp.data or {}

            # Fetch latest RUL prediction for this engine
            pred_resp = supabase.table("rul_predictions") \
                .select("*") \
                .eq("engine_id", engine_db_id) \
                .order("predicted_at", desc=True) \
                .limit(1) \
                .execute()
            pred = pred_resp.data[0] if pred_resp.data else {}

            engine_id   = str(engine.get("engine_id", "01")).zfill(2)
            status      = (engine.get("condition_status") or "healthy").lower().strip()
            if status not in ("healthy", "warning", "critical"):
                status = "healthy"

            rul         = float(pred.get("predicted_rul", 120))
            max_life    = 130
            degradation = max(0, min(100, int((rul / max_life) * 100)))

            print(f"[DEBUG] Overview engine={engine}, pred={pred}")

    except Exception as e:
        import traceback
        print(f"[ERROR] overview fetch: {traceback.format_exc()}")

    return html.Div(
        style={
            "height": "100vh",
            "display": "flex",
            "flexDirection": "column",   # ← topbar on top, row below
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628",
            "color": "white",
            "overflow": "hidden",
        },
        children=[
            dcc.Location(id="url-overview", refresh=False),

            # ── Topbar: full width, always fixed at top ──
            html.Div(
                style={
                    "background": "linear-gradient(90deg, #0d2045 0%, #071530 100%)",
                    "borderBottom": "1px solid rgba(74,158,255,0.18)",
                    "padding": "0 28px",
                    "height": "60px",
                    "minHeight": "60px",
                    "flexShrink": "0",        # ← never shrink
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "zIndex": "200",
                    "width": "100%",
                },
                children=[
                    html.H1(
                        "ENGINE PROGNOSTIC MONITORING SYSTEM",
                        style={
                            "margin": "0",
                            "fontSize": "18px",
                            "fontWeight": "700",
                            "color": "white",
                            "letterSpacing": "1.2px",
                        }
                    ),
                    html.Div(
                        id="sidebar-toggle",
                        n_clicks=0,
                        style={"cursor": "pointer"},
                        children=[icon_sidebar()]
                    ),
                ]
            ),

            # ── Body: sidebar + content side by side, below topbar ──
            html.Div(
                style={
                    "flex": "1",
                    "display": "flex",
                    "flexDirection": "row",   # ← sidebar | content
                    "overflow": "hidden",
                    "minHeight": "0",         # ← critical for flex children to scroll
                },
                children=[
                    # Sidebar
                    build_sidebar(active_page="overview"),

                    # Scrollable content
                    html.Div(
                        style={
                            "flex": "1",
                            "overflowY": "auto",
                            "padding": "24px 28px",
                            "minWidth": "0",
                        },
                        children=build_overview_body(
                            engine_id=engine_id,
                            status=status,
                            rul=int(rul),
                            degradation=degradation,
                        )
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  STANDALONE RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
    )
    app.layout = create_overview_layout()
    app.run(debug=True)
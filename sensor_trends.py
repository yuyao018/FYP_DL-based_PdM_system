import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import base64
import numpy as np

# ─────────────────────────────────────────────
#  SENSOR DEFINITIONS
# ─────────────────────────────────────────────

SENSORS = {
    "TEMPERATURE": [
        {"id": "T2",  "label": "T2",  "unit": "°R", "desc": "Fan inlet temperature",       "color": "#ff6b6b"},
        {"id": "T24", "label": "T24", "unit": "°R", "desc": "LPC outlet temperature",      "color": "#f5a623"},
        {"id": "T30", "label": "T30", "unit": "°R", "desc": "HPC outlet temperature",      "color": "#ff4d4d"},
        {"id": "T50", "label": "T50", "unit": "°R", "desc": "LPT outlet temperature",      "color": "#ff8c69"},
    ],
    "PRESSURE": [
        {"id": "P2",  "label": "P2",  "unit": "psia", "desc": "Fan inlet pressure",        "color": "#4a9eff"},
        {"id": "P15", "label": "P15", "unit": "psia", "desc": "Bypass duct pressure",      "color": "#00c8ff"},
        {"id": "P30", "label": "P30", "unit": "psia", "desc": "HPC outlet pressure",       "color": "#7b61ff"},
    ],
    "SPEED / FLOW": [
        {"id": "Nf",  "label": "Nf",  "unit": "rpm", "desc": "Fan speed",                  "color": "#00c875"},
        {"id": "Nc",  "label": "Nc",  "unit": "rpm", "desc": "Core speed",                 "color": "#00e5a0"},
        {"id": "Ps30","label": "Ps30","unit": "psia", "desc": "HPC static pressure",       "color": "#a0f0c0"},
        {"id": "phi", "label": "phi", "unit": "pps",  "desc": "Fuel-air ratio",            "color": "#ffd93d"},
        {"id": "BPR", "label": "BPR", "unit": "—",   "desc": "Bypass ratio",               "color": "#ff9f43"},
        {"id": "NRf", "label": "NRf", "unit": "rpm", "desc": "Corrected fan speed",        "color": "#c0d0ff"},
        {"id": "NRc", "label": "NRc", "unit": "rpm", "desc": "Corrected core speed",       "color": "#90a8e0"},
    ],
}

# Flat list for lookup
ALL_SENSORS = {s["id"]: s for group in SENSORS.values() for s in group}

# Default selected sensors (matching screenshot)
DEFAULT_SELECTED = ["T30", "P30", "Nf", "phi"]


# ─────────────────────────────────────────────
#  SVG ICON HELPERS  (shared with overview.py)
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
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
#  SIDEBAR
# ─────────────────────────────────────────────

def build_sidebar(active_page="sensor", engine_db_id=None):
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
    explainability_href = f"/explainability/{engine_db_id}" if engine_db_id else "/explainability"
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
                nav_link(icon_shap,     "Explainability AI","explainability",explainability_href),
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
#  SENSOR CHART
# ─────────────────────────────────────────────

def build_sensor_chart(selected_ids, normalize=True, total_cycles=100):
    """Generate multi-line sensor trend chart."""
    fig = go.Figure()
    x = np.linspace(0, total_cycles, total_cycles + 1)

    rng = np.random.RandomState(99)

    for sid in selected_ids:
        if sid not in ALL_SENSORS:
            continue
        s = ALL_SENSORS[sid]

        # Simulate degradation-aware signal per sensor
        base = rng.uniform(0.2, 0.5)
        trend = rng.uniform(-0.003, 0.005)
        noise = rng.normal(0, 0.01, len(x))
        raw = base + trend * x + noise
        # Add a subtle inflection around cycle 60
        inflection = 0.15 * np.exp(-((x - 60) ** 2) / 500) * rng.choice([-1, 1])
        raw += inflection

        if normalize:
            mn, mx = raw.min(), raw.max()
            y = (raw - mn) / (mx - mn + 1e-9)
            y_axis_label = "Normalised Value"
        else:
            y = raw * rng.uniform(80, 400)   # scale to realistic units
            y_axis_label = "Raw Value"

        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="lines",
            name=s["label"],
            line=dict(color=s["color"], width=2),
            hovertemplate=f"<b>{s['label']}</b><br>Cycle: %{{x}}<br>Value: %{{y:.3f}}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,20,45,0.6)",
        margin=dict(l=10, r=20, t=30, b=40),
        height=420,
        legend=dict(
            orientation="h", x=0, y=-0.18,
            font=dict(color="#a8d4ff", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            title=dict(text="Operational Cycles", font=dict(color="#a8d4ff", size=11)),
            showgrid=True, gridcolor="rgba(74,158,255,0.08)",
            color="#a8d4ff", tickfont=dict(size=10), zeroline=False,
            range=[0, total_cycles],
        ),
        yaxis=dict(
            title=dict(text="Normalised Value" if normalize else "Raw Value",
                       font=dict(color="#a8d4ff", size=11)),
            showgrid=True, gridcolor="rgba(74,158,255,0.08)",
            color="#a8d4ff", tickfont=dict(size=10), zeroline=False,
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0d1e3a", font_color="white", bordercolor="rgba(74,158,255,0.4)"),
    )

    # Cycle label top-right
    fig.add_annotation(
        x=total_cycles, y=1.06, xref="x", yref="paper",
        text=f"Cycle {total_cycles}", font=dict(color="#a8d4ff", size=10),
        showarrow=False, xanchor="right",
    )

    return fig

# ─────────────────────────────────────────────
#  SENSOR CHECKLIST
# ─────────────────────────────────────────────

def build_sensor_checklist():
    children = []
    for group_name, sensors in SENSORS.items():
        children.append(
            html.Div(group_name, style={
                "color": "rgba(168,212,255,0.45)", "fontSize": "10px",
                "fontWeight": "700", "letterSpacing": "1px",
                "padding": "8px 4px 4px", "marginTop": "4px",
            })
        )
        for s in sensors:
            children.append(
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "8px",
                           "padding": "5px 4px", "borderRadius": "6px", "marginBottom": "2px"},
                    children=[
                        dcc.Checklist(
                            id={"type": "sensor-check", "index": s["id"]},
                            options=[{"label": "", "value": s["id"]}],
                            value=[s["id"]] if s["id"] in DEFAULT_SELECTED else [],
                            style={"display": "inline"},
                            inputStyle={
                                "width": "14px", "height": "14px",
                                "accentColor": "#4a9eff", "cursor": "pointer",
                            },
                        ),
                        html.Div(style={
                            "width": "10px", "height": "10px", "borderRadius": "50%",
                            "background": s["color"], "flexShrink": "0",
                        }),
                        html.Span(s["label"], style={"color": "white", "fontSize": "13px",
                                                      "fontWeight": "500", "minWidth": "36px"}),
                        html.Span(s["unit"], style={"color": "rgba(168,212,255,0.45)", "fontSize": "11px"}),
                    ]
                )
            )
    return children


# ─────────────────────────────────────────────
#  RAW / NORMALIZE TOGGLE
# ─────────────────────────────────────────────

def normalize_toggle():
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "10px"},
        children=[
            html.Span("Raw", style={"color": "#a8d4ff", "fontSize": "13px", "fontWeight": "500"}),
            # Toggle switch
            html.Div(
                id="normalize-toggle",
                n_clicks=1,   # start as Normalize (active)
                style={
                    "width": "44px", "height": "24px", "borderRadius": "12px",
                    "background": "#4a9eff", "position": "relative",
                    "cursor": "pointer", "transition": "background 0.2s",
                    "border": "1px solid rgba(74,158,255,0.6)",
                },
                children=[
                    html.Div(style={
                        "width": "18px", "height": "18px", "borderRadius": "50%",
                        "background": "white", "position": "absolute",
                        "top": "2px", "right": "3px",
                        "transition": "left 0.2s",
                        "boxShadow": "0 1px 4px rgba(0,0,0,0.3)",
                    })
                ]
            ),
            html.Span("Normalize", style={"color": "white", "fontSize": "13px", "fontWeight": "600"}),
        ]
    )


# ─────────────────────────────────────────────
#  MAIN PAGE BODY
# ─────────────────────────────────────────────

def build_sensor_trends_body(engine_id="01", status="healthy"):

    status_cfg = {
        "healthy":  ("rgba(0,200,100,0.18)",  "#00c875", "#00c875"),
        "warning":  ("rgba(255,217,61,0.18)", "#ffd93d", "#ffd93d"),
        "critical": ("rgba(255,77,77,0.18)",  "#ff4d4d", "#ff4d4d"),
    }
    sc = status_cfg.get(status, status_cfg["healthy"])

    return [
        dcc.Store(id="normalize-state", data=True),

        # ── Engine header ──
        html.Div(
            style={"display": "flex", "alignItems": "center",
                   "justifyContent": "space-between", "marginBottom": "20px"},
            children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "14px"}, children=[
                    html.H2(f"ENGINE-{engine_id}",
                            style={"margin": "0", "color": "white",
                                   "fontSize": "22px", "fontWeight": "800"}),
                    html.Span(status.upper(), style={
                        "background": sc[0], "color": sc[1], "border": f"1px solid {sc[2]}",
                        "borderRadius": "20px", "padding": "3px 12px",
                        "fontSize": "11px", "fontWeight": "700",
                    }),
                ]),
                # Raw / Normalize toggle
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "10px"}, children=[
                    html.Span("Raw", id="raw-label",
                            style={"color": "#a8d4ff", "fontSize": "13px", "fontWeight": "500"}),
                    html.Div(
                        id="normalize-toggle",
                        n_clicks=1,
                        style={
                            "width": "44px", "height": "24px", "borderRadius": "12px",
                            "background": "#4a9eff", "position": "relative",
                            "cursor": "pointer", "flexShrink": "0",
                            "border": "1px solid rgba(74,158,255,0.6)",
                        },
                        children=[
                            html.Div(id="toggle-knob", style={
                                "width": "18px", "height": "18px", "borderRadius": "50%",
                                "background": "white", "position": "absolute",
                                "top": "2px", "right": "3px",
                                "transition": "right 0.2s",
                                "boxShadow": "0 1px 4px rgba(0,0,0,0.3)",
                            })
                        ]
                    ),
                    html.Span("Normalize", id="norm-label",
                            style={"color": "white", "fontSize": "13px", "fontWeight": "700"}),
                ]),
            ]
        ),

        # ── Two-column layout ──
        html.Div(
            style={"display": "flex", "gap": "0", "flex": "1", "minHeight": "500px"},
            children=[

                # Left: sensor panel
                html.Div(
                    style={
                        "width": "210px", "flexShrink": "0",
                        "background": "#0d1e3a",
                        "border": "1px solid rgba(74,158,255,0.15)",
                        "borderRadius": "14px 0 0 14px",
                        "padding": "14px 12px",
                        "overflowY": "auto",
                    },
                    children=[
                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between",
                                   "alignItems": "center", "marginBottom": "10px", "padding": "0 4px"},
                            children=[
                                html.Span("SENSORS", style={"color": "rgba(168,212,255,0.5)",
                                                              "fontSize": "10px", "fontWeight": "700",
                                                              "letterSpacing": "1.5px"}),
                                html.Span("Select all", id="select-all-btn", n_clicks=0,
                                          style={"color": "#4a9eff", "fontSize": "11px",
                                                 "cursor": "pointer", "fontWeight": "600"}),
                            ]
                        ),
                        *build_sensor_checklist(),
                    ]
                ),

                # Right: chart
                html.Div(
                    style={
                        "flex": "1", "minWidth": "0",
                        "background": "#101e36",
                        "border": "1px solid rgba(74,158,255,0.15)",
                        "borderLeft": "none",
                        "borderRadius": "0 14px 14px 0",
                        "padding": "16px 16px 8px",
                        "display": "flex", "flexDirection": "column",
                    },
                    children=[
                        dcc.Graph(
                            id="sensor-chart",
                            figure=build_sensor_chart(DEFAULT_SELECTED, normalize=True),
                            config={"displayModeBar": False},
                            style={"flex": "1"},
                        ),
                        html.Div(id="chart-legend",
                                 style={"display": "flex", "flexWrap": "wrap", "gap": "16px",
                                        "padding": "8px 4px 0",
                                        "borderTop": "1px solid rgba(74,158,255,0.1)"},
                                 children=[
                                     html.Div(
                                         style={"display": "flex", "alignItems": "center", "gap": "6px"},
                                         children=[
                                             html.Div(style={"width": "24px", "height": "2px",
                                                             "background": ALL_SENSORS[sid]["color"]}),
                                             html.Span(
                                                 f"{ALL_SENSORS[sid]['label']} — {ALL_SENSORS[sid]['desc']}",
                                                 style={"color": "#a8d4ff", "fontSize": "11px"}
                                             )
                                         ]
                                     )
                                     for sid in DEFAULT_SELECTED
                                 ]),
                    ]
                ),
            ]
        ),
    ]

# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_sensor_trends_layout(supabase=None, engine_db_id=None):
    engine_id = "01"
    status    = "healthy"

    try:
        if supabase and engine_db_id is not None:
            eng_resp = supabase.table("engines") \
                .select("engine_id, condition_status") \
                .eq("id", engine_db_id) \
                .single().execute()
            engine   = eng_resp.data or {}
            engine_id = str(engine.get("engine_id", "01")).zfill(2)
            status    = (engine.get("condition_status") or "healthy").lower().strip()
            if status not in ("healthy", "warning", "critical"):
                status = "healthy"
    except Exception as e:
        import traceback
        print(f"[ERROR] sensor trends fetch: {traceback.format_exc()}")

    return html.Div(
        style={
            "height": "100vh", "display": "flex", "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628", "color": "white", "overflow": "hidden",
        },
        children=[
            dcc.Location(id="url-sensor", refresh=False),

            # ── Fixed topbar ──
            html.Div(
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
            ),

            # ── Sidebar + content ──
            html.Div(
                style={"flex": "1", "display": "flex", "flexDirection": "row",
                       "overflow": "hidden", "minHeight": "0"},
                children=[
                    build_sidebar(active_page="sensor", engine_db_id=engine_db_id),
                    html.Div(
                        style={"flex": "1", "overflowY": "auto", "padding": "24px 28px",
                               "minWidth": "0", "display": "flex", "flexDirection": "column"},
                        children=build_sensor_trends_body(engine_id=engine_id, status=status),
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS  (register on the app object)
# ─────────────────────────────────────────────

def register_sensor_callbacks(app):
    all_ids = list(ALL_SENSORS.keys())

    # ── Toggle visual state (knob position + label colours) ──
    @app.callback(
        Output("normalize-toggle", "style"),
        Output("toggle-knob", "style"),
        Output("raw-label", "style"),
        Output("norm-label", "style"),
        Input("normalize-toggle", "n_clicks"),
    )
    def update_toggle_style(n_clicks):
        is_norm = (n_clicks % 2 == 1)   # odd clicks = Normalize on

        toggle_style = {
            "width": "44px", "height": "24px", "borderRadius": "12px",
            "background": "#4a9eff" if is_norm else "rgba(74,158,255,0.25)",
            "position": "relative", "cursor": "pointer", "flexShrink": "0",
            "border": "1px solid rgba(74,158,255,0.6)",
        }
        knob_style = {
            "width": "18px", "height": "18px", "borderRadius": "50%",
            "background": "white", "position": "absolute",
            "top": "2px",
            "right": "3px" if is_norm else "auto",
            "left": "auto" if is_norm else "3px",
            "transition": "left 0.2s, right 0.2s",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.3)",
        }
        raw_style = {
            "color": "white" if not is_norm else "#a8d4ff",
            "fontSize": "13px",
            "fontWeight": "700" if not is_norm else "500",
        }
        norm_style = {
            "color": "white" if is_norm else "#a8d4ff",
            "fontSize": "13px",
            "fontWeight": "700" if is_norm else "500",
        }
        return toggle_style, knob_style, raw_style, norm_style

    # ── Select all / deselect all checkboxes ──
    @app.callback(
        [Output({"type": "sensor-check", "index": sid}, "value") for sid in all_ids],
        Input("select-all-btn", "n_clicks"),
        State("select-all-btn", "children"),
        prevent_initial_call=True,
    )
    def toggle_select_all(n_clicks, label):
        # Odd clicks = select all, even = deselect all
        if n_clicks % 2 == 1:
            return [[sid] for sid in all_ids]   # all checked
        else:
            return [[] for _ in all_ids]         # all unchecked

    # ── Update "Select all" label text ──
    @app.callback(
        Output("select-all-btn", "children"),
        Input("select-all-btn", "n_clicks"),
    )
    def update_select_label(n_clicks):
        return "Deselect all" if n_clicks % 2 == 1 else "Select all"

    # ── Update chart when sensors or toggle changes ──
    @app.callback(
        Output("sensor-chart", "figure"),
        Output("chart-legend", "children"),
        Input({"type": "sensor-check", "index": dash.ALL}, "value"),
        Input("normalize-toggle", "n_clicks"),
    )
    def update_chart(check_values, n_clicks):
        is_norm = (n_clicks % 2 == 1)

        selected = [
            all_ids[i]
            for i, vals in enumerate(check_values)
            if vals
        ]
        if not selected:
            selected = [all_ids[0]]

        fig = build_sensor_chart(selected, normalize=is_norm)

        legend = [
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "6px"},
                children=[
                    html.Div(style={"width": "24px", "height": "2px",
                                    "background": ALL_SENSORS[sid]["color"]}),
                    html.Span(
                        f"{ALL_SENSORS[sid]['label']} — {ALL_SENSORS[sid]['desc']}",
                        style={"color": "#a8d4ff", "fontSize": "11px"}
                    )
                ]
            )
            for sid in selected if sid in ALL_SENSORS
        ]
        return fig, legend

    # ── Sidebar toggle ──
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
    app.layout = create_sensor_trends_layout()
    register_sensor_callbacks(app)
    app.run(debug=True)
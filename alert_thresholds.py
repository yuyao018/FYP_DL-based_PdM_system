import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import base64

# ─────────────────────────────────────────────
#  SVG ICON HELPERS
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

def icon_users():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="9" cy="8" r="3.2"/>
      <path d="M3 20c0-3.6 2.7-6 6-6s6 2.4 6 6"/>
      <circle cx="17" cy="8" r="2.4"/>
      <path d="M21 20c0-2.8-1.6-5-4-5.7"/>
    </svg>''')

def icon_engine():
    return _svg_img('''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="48" fill="none" stroke="#a8d4ff" stroke-width="1.5"/>
        <circle cx="50" cy="50" r="18" fill="none" stroke="#a8d4ff" stroke-width="2"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#a8d4ff" stroke-width="1.8" transform="rotate(0 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#a8d4ff" stroke-width="1.8" transform="rotate(90 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#a8d4ff" stroke-width="1.8" transform="rotate(180 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#a8d4ff" stroke-width="1.8" transform="rotate(270 50 50)"/>
        <circle cx="50" cy="50" r="4" fill="#a8d4ff"/>
    </svg>''', size="22px")

def icon_upload():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 16V4M12 4l-4 4M12 4l4 4"/>
      <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>
    </svg>''')

def icon_threshold():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <line x1="4" y1="6" x2="20" y2="6"/><circle cx="14" cy="6" r="2" fill="#0d1e3a"/>
      <line x1="4" y1="12" x2="20" y2="12"/><circle cx="8" cy="12" r="2" fill="#0d1e3a"/>
      <line x1="4" y1="18" x2="20" y2="18"/><circle cx="16" cy="18" r="2" fill="#0d1e3a"/>
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

def icon_sliders():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/>
      <line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>
      <line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>
      <circle cx="4" cy="12" r="2"/><circle cx="12" cy="10" r="2"/><circle cx="20" cy="14" r="2"/>
    </svg>''')


# ─────────────────────────────────────────────
#  SIDEBAR  (Admin Panel variant — shared pattern)
# ─────────────────────────────────────────────

def build_admin_sidebar(active_page="threshold"):
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
        return dcc.Link(href=href, style={"textDecoration": "none"},
                children=[html.Div(style=style, children=[icon_fn(), html.Span(label)])])

    return html.Div(
        id="sidebar",
        style={
            "width": "210px", "flexShrink": "0", "height": "100%",
            "background": "#0d1e3a", "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex", "flexDirection": "column",
            "overflow": "hidden", "transition": "width 0.3s ease",
        },
        children=[
            dcc.Link(href="/dashboard", style={"textDecoration": "none"}, children=[
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
                html.Div("ADMIN PANEL", style={
                    "color": "rgba(168,212,255,0.5)", "fontSize": "10px", "fontWeight": "700",
                    "letterSpacing": "1.5px", "padding": "0 6px", "marginBottom": "10px",
                }),
                nav_link(icon_engine,    "Engine Management", "engines",   "/engine-management"),
                nav_link(icon_users,     "User Management",  "users",     "/user-management"),
                nav_link(icon_threshold, "Alert Thresholds", "threshold", "/alert-thresholds"),
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
#  THRESHOLD INPUT CARD
# ─────────────────────────────────────────────

def stepper_button(symbol, button_id, color):
    return html.Div(
        id=button_id,
        n_clicks=0,
        style={
            "width": "30px", "height": "30px", "borderRadius": "6px",
            "background": "rgba(74,158,255,0.12)",
            "border": f"1px solid {color}40",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "cursor": "pointer", "color": color, "fontSize": "16px", "fontWeight": "700",
            "userSelect": "none", "flexShrink": "0",
        },
        children=symbol
    )


def threshold_input(label, dot_color, input_id, value, helper_text):
    return html.Div(
        style={"flex": "1"},
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "10px"},
                children=[
                    html.Span("●", style={"color": dot_color, "fontSize": "12px"}),
                    html.Span(label.upper(), style={"color": "#4a9eff", "fontSize": "11px",
                                                      "fontWeight": "700", "letterSpacing": "0.8px"}),
                ]
            ),
            html.Div(
                style={
                    "display": "flex", "alignItems": "center", "gap": "8px",
                    "background": "rgba(10,20,45,0.6)",
                    "border": f"1.5px solid {dot_color}55",
                    "borderRadius": "8px", "padding": "6px 10px",
                },
                children=[
                    stepper_button("−", f"{input_id}-minus", dot_color),
                    dcc.Input(
                        id=f"{input_id}-display",
                        type="text",
                        value=str(value),
                        pattern="[0-9]*",
                        inputMode="numeric",
                        style={
                            "flex": "1", "textAlign": "center", "color": dot_color,
                            "fontSize": "24px", "fontWeight": "800", "fontFamily": "inherit",
                            "background": "transparent", "border": "none", "outline": "none",
                            "width": "100%",
                        }
                    ),
                    stepper_button("+", f"{input_id}-plus", dot_color),
                    html.Div("cycles", style={
                        "background": "rgba(74,158,255,0.1)", "color": "#a8d4ff",
                        "fontSize": "12px", "fontWeight": "600", "padding": "6px 12px",
                        "borderRadius": "6px", "whiteSpace": "nowrap",
                    }),
                ]
            ),
            html.Div(helper_text, style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                          "marginTop": "6px"}),
            dcc.Store(id=input_id, data=value),   # holds the actual numeric value
        ]
    )


def max_rul_input(input_id, value):
    return html.Div(
        style={"flex": "1"},
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "8px", "marginBottom": "10px"},
                children=[
                    html.Span("●", style={"color": "#7b9aff", "fontSize": "12px"}),
                    html.Span("MAX RUL CAP", style={"color": "#4a9eff", "fontSize": "11px",
                                                      "fontWeight": "700", "letterSpacing": "0.8px"}),
                ]
            ),
            html.Div(
                style={
                    "display": "flex", "alignItems": "center", "gap": "8px",
                    "background": "rgba(10,20,45,0.6)",
                    "border": "1.5px solid rgba(74,158,255,0.3)",
                    "borderRadius": "8px", "padding": "6px 10px",
                },
                children=[
                    stepper_button("−", f"{input_id}-minus", "#7b9aff"),
                    dcc.Input(
                        id=f"{input_id}-display",
                        type="text",
                        value=str(value),
                        pattern="[0-9]*",
                        inputMode="numeric",
                        style={
                            "flex": "1", "textAlign": "center", "color": "white",
                            "fontSize": "24px", "fontWeight": "800", "fontFamily": "inherit",
                            "background": "transparent", "border": "none", "outline": "none",
                            "width": "100%",
                        }
                    ),
                    stepper_button("+", f"{input_id}-plus", "#7b9aff"),
                    html.Div("cycles", style={
                        "background": "rgba(74,158,255,0.1)", "color": "#a8d4ff",
                        "fontSize": "12px", "fontWeight": "600", "padding": "6px 12px",
                        "borderRadius": "6px", "whiteSpace": "nowrap",
                    }),
                ]
            ),
            dcc.Store(id=input_id, data=value),
        ]
    )


# ─────────────────────────────────────────────
#  THRESHOLD VISUALIZATION BAR
# ─────────────────────────────────────────────

def build_threshold_bar(crit, warn, max_rul):
    crit = max(0, min(crit, max_rul))
    warn = max(crit, min(warn, max_rul))

    crit_pct = (crit / max_rul) * 100 if max_rul else 0
    warn_pct = (warn / max_rul) * 100 if max_rul else 0

    return html.Div(
        children=[
            html.Div("Threshold Visualization", style={"color": "white", "fontSize": "13px",
                                                          "fontWeight": "700", "marginBottom": "10px"}),
            html.Div(
                style={
                    "position": "relative", "height": "36px", "borderRadius": "18px",
                    "overflow": "hidden", "display": "flex",
                },
                children=[
                    html.Div(
                        style={"width": f"{crit_pct}%", "background": "linear-gradient(90deg, #8b0000, #ff4d4d)",
                               "display": "flex", "alignItems": "center", "justifyContent": "center"},
                        children=[html.Span("CRITICAL", style={"color": "white", "fontSize": "10px",
                                                                 "fontWeight": "700"})] if crit_pct > 8 else []
                    ),
                    html.Div(
                        style={"width": f"{warn_pct - crit_pct}%", "background": "linear-gradient(90deg, #b8860b, #ffd93d)",
                               "display": "flex", "alignItems": "center", "justifyContent": "center"},
                        children=[html.Span("WARNING", style={"color": "#3a2a00", "fontSize": "10px",
                                                                "fontWeight": "700"})] if (warn_pct - crit_pct) > 8 else []
                    ),
                    html.Div(
                        style={"width": f"{100 - warn_pct}%", "background": "linear-gradient(90deg, #00c875, #00a85e)",
                               "display": "flex", "alignItems": "center", "justifyContent": "center"},
                        children=[html.Span("HEALTHY", style={"color": "white", "fontSize": "10px",
                                                                "fontWeight": "700"})] if (100 - warn_pct) > 8 else []
                    ),
                ]
            ),
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "marginTop": "6px", "position": "relative"},
                children=[
                    html.Span("0", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "position": "absolute", "left": "0"}),
                    html.Span(str(crit), style={
                        "color": "#ff4d4d", "fontSize": "11px", "fontWeight": "700",
                        "position": "absolute", "left": f"{crit_pct}%", 
                        "transform": "translateX(-50%)"
                    }),
                    html.Span(str(warn), style={
                        "color": "#ffd93d", "fontSize": "11px", "fontWeight": "700",
                        "position": "absolute", "left": f"{warn_pct}%",
                        "transform": "translateX(-50%)"
                    }),
                    html.Span(str(max_rul), style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "position": "absolute", "right": "0"}),
                ]
            ),
        ]
    )


# ─────────────────────────────────────────────
#  STATUS PREVIEW CARDS
# ─────────────────────────────────────────────

def status_preview_card(label, range_text, sub_text, color, bg, border):
    return html.Div(
        style={
            "flex": "1", "background": bg, "border": f"1.5px solid {border}",
            "borderRadius": "10px", "padding": "16px",
        },
        children=[
            html.Div(label.upper(), style={"color": color, "fontSize": "11px",
                                            "fontWeight": "700", "letterSpacing": "0.8px", "marginBottom": "8px"}),
            html.Div(range_text, style={"color": color, "fontSize": "18px", "fontWeight": "800",
                                         "marginBottom": "6px"}),
            html.Div(sub_text, style={"color": f"{color}cc", "fontSize": "11px"}),
        ]
    )


def build_status_preview(crit, warn):
    return html.Div(
        children=[
            html.Div("Status Preview", style={"color": "white", "fontSize": "13px",
                                               "fontWeight": "700", "marginBottom": "10px"}),
            html.Div(
                style={"display": "flex", "gap": "14px"},
                children=[
                    status_preview_card(
                        "Critical", f"RUL ≤ {crit} cycles", "Immediate maintenance required",
                        "#ff6b6b", "rgba(255,77,77,0.1)", "rgba(255,77,77,0.4)"
                    ),
                    status_preview_card(
                        "Warning", f"{crit + 1} – {warn} cycles", "Schedule maintenance soon",
                        "#ffd93d", "rgba(255,217,61,0.1)", "rgba(255,217,61,0.4)"
                    ),
                    status_preview_card(
                        "Healthy", f"RUL > {warn} cycles", "Normal operations",
                        "#00c875", "rgba(0,200,117,0.1)", "rgba(0,200,117,0.4)"
                    ),
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  MAIN PAGE BODY
# ─────────────────────────────────────────────

def build_threshold_body(warn=80, crit=30, max_rul=125):
    return [
        html.Div(style={"marginBottom": "8px"}, children=[
            html.H2("ALERT THRESHOLDS", style={"margin": "0", "color": "white",
                                                "fontSize": "22px", "fontWeight": "800"}),
        ]),
        html.Div(style={"height": "1px", "background": "rgba(74,158,255,0.15)", "margin": "16px 0 20px"}),

        html.Div(
            id="threshold-panel-container",
            style={
                "background": "#101e36", "border": "1px solid rgba(74,158,255,0.18)",
                "borderRadius": "14px", "padding": "24px",
            },
            children=[
                # Header
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "22px"},
                    children=[icon_sliders(), html.Span("GLOBAL THRESHOLD", style={
                        "color": "white", "fontSize": "14px", "fontWeight": "700", "letterSpacing": "0.5px",
                    })]
                ),

                # Inputs row
                html.Div(
                    style={"display": "flex", "gap": "20px", "marginBottom": "26px"},
                    children=[
                        threshold_input("Warning Threshold", "#ffd93d", "warn-threshold-input", warn,
                                       "Alert fires when RUL ≤ this value"),
                        threshold_input("Critical Threshold", "#ff4d4d", "crit-threshold-input", crit,
                                       "Alert fires when RUL ≤ this value"),
                        max_rul_input("max-rul-input", max_rul),
                    ]
                ),

                # Threshold visualization
                html.Div(id="threshold-bar-container", style={"marginBottom": "26px"},
                         children=[build_threshold_bar(crit, warn, max_rul)]),

                # Status preview
                html.Div(id="status-preview-container", style={"marginBottom": "26px"},
                         children=[build_status_preview(crit, warn)]),

                # Save button
                html.Div(
                    style={"display": "flex", "justifyContent": "flex-end"},
                    children=[
                        html.Button("Save Threshold", id="save-threshold-btn", n_clicks=0, style={
                            "background": "linear-gradient(90deg, #1a6fd4 0%, #2a85f0 100%)",
                            "border": "none", "borderRadius": "8px", "color": "white",
                            "padding": "12px 28px", "fontSize": "14px", "fontWeight": "700",
                            "cursor": "pointer", "boxShadow": "0 2px 10px rgba(42,133,240,0.3)",
                        }),
                    ]
                ),
                html.Div(id="save-threshold-status", style={"marginTop": "10px", "textAlign": "right"}),
            ]
        ),

        dcc.Store(id="threshold-current-values", data={"warn": warn, "crit": crit, "max_rul": max_rul}),
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_alert_thresholds_layout(supabase=None):
    warn, crit, max_rul = 80, 30, 125

    try:
        if supabase:
            resp = supabase.table("alert_thresholds") \
                .select("*") \
                .order("updated_at", desc=True) \
                .limit(1) \
                .execute()
            if resp.data:
                t = resp.data[0]
                warn = t.get("warning_threshold", warn)
                crit = t.get("critical_threshold", crit)
                max_rul = t.get("max_rul_cap", max_rul)
    except Exception as e:
        import traceback
        print(f"[ERROR] alert thresholds fetch: {traceback.format_exc()}")

    return html.Div(
        style={
            "minHeight": "100vh", "display": "flex", "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628", "color": "white",
        },
        children=[
            html.Div(style={"position": "sticky", "top": "0", "zIndex": "200"},
                     children=[build_topbar()]),
            html.Div(
                style={"flex": "1", "display": "flex", "flexDirection": "row"},
                children=[
                    build_admin_sidebar(active_page="threshold"),
                    html.Div(
                        style={"flex": "1", "padding": "24px 28px", "minWidth": "0"},
                        children=build_threshold_body(warn=warn, crit=crit, max_rul=max_rul),
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def register_alert_thresholds_callbacks(app, supabase=None):

    # ── Warning threshold stepper ──
    @app.callback(
        Output("warn-threshold-input", "data"),
        Output("warn-threshold-input-display", "value"),
        Input("warn-threshold-input-plus", "n_clicks"),
        Input("warn-threshold-input-minus", "n_clicks"),
        Input("warn-threshold-input-display", "value"),
        State("warn-threshold-input", "data"),
        prevent_initial_call=True,
    )
    def step_warn(plus_clicks, minus_clicks, input_value, current):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        trigger = ctx.triggered[0]["prop_id"]
        
        if "plus" in trigger:
            new_val = current + 1
        elif "minus" in trigger:
            new_val = max(0, current - 1)
        else:  # direct input
            try:
                new_val = max(0, int(input_value)) if input_value and str(input_value).strip() else current
            except (ValueError, TypeError):
                new_val = current
        
        return new_val, str(new_val)

    # ── Critical threshold stepper ──
    @app.callback(
        Output("crit-threshold-input", "data"),
        Output("crit-threshold-input-display", "value"),
        Input("crit-threshold-input-plus", "n_clicks"),
        Input("crit-threshold-input-minus", "n_clicks"),
        Input("crit-threshold-input-display", "value"),
        State("crit-threshold-input", "data"),
        prevent_initial_call=True,
    )
    def step_crit(plus_clicks, minus_clicks, input_value, current):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        trigger = ctx.triggered[0]["prop_id"]
        
        if "plus" in trigger:
            new_val = current + 1
        elif "minus" in trigger:
            new_val = max(0, current - 1)
        else:  # direct input
            try:
                new_val = max(0, int(input_value)) if input_value and str(input_value).strip() else current
            except (ValueError, TypeError):
                new_val = current
        
        return new_val, str(new_val)

    # ── Max RUL cap stepper ──
    @app.callback(
        Output("max-rul-input", "data"),
        Output("max-rul-input-display", "value"),
        Input("max-rul-input-plus", "n_clicks"),
        Input("max-rul-input-minus", "n_clicks"),
        Input("max-rul-input-display", "value"),
        State("max-rul-input", "data"),
        prevent_initial_call=True,
    )
    def step_max_rul(plus_clicks, minus_clicks, input_value, current):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        trigger = ctx.triggered[0]["prop_id"]
        
        if "plus" in trigger:
            new_val = current + 1
        elif "minus" in trigger:
            new_val = max(1, current - 1)
        else:  # direct input
            try:
                new_val = max(1, int(input_value)) if input_value and str(input_value).strip() else current
            except (ValueError, TypeError):
                new_val = current
        
        return new_val, str(new_val)

    # ── Live-update visualization + status preview whenever any value changes ──
    @app.callback(
        Output("threshold-bar-container", "children"),
        Output("status-preview-container", "children"),
        Input("warn-threshold-input", "data"),
        Input("crit-threshold-input", "data"),
        Input("max-rul-input", "data"),
        prevent_initial_call=True,
    )
    def update_preview(warn, crit, max_rul):
        warn = warn or 0
        crit = crit or 0
        max_rul = max_rul or 1
        bar = build_threshold_bar(crit, warn, max_rul)
        preview = build_status_preview(crit, warn)
        return bar, preview

    # ── Save thresholds to Supabase ──
    @app.callback(
        Output("save-threshold-status", "children"),
        Input("save-threshold-btn", "n_clicks"),
        State("warn-threshold-input", "data"),
        State("crit-threshold-input", "data"),
        State("max-rul-input", "data"),
        State("session-store", "data"),
        prevent_initial_call=True,
    )
    def save_thresholds(n_clicks, warn, crit, max_rul, session_data):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        if crit >= warn:
            return html.Span("Critical threshold must be lower than warning threshold.",
                            style={"color": "#ff6b6b", "fontSize": "13px"})

        if not supabase:
            return html.Span("Supabase not connected.", style={"color": "#ff6b6b", "fontSize": "13px"})

        # Get user_id from session
        user_id = None
        if session_data:
            user_id = session_data.get("user_id")

        try:
            # Fetch the most recent threshold settings
            resp = supabase.table("alert_thresholds") \
                .select("*") \
                .order("updated_at", desc=True) \
                .limit(1) \
                .execute()
            
            # Check if current values match the previous saved values
            if resp.data:
                previous = resp.data[0]
                prev_warn = previous.get("warning_threshold")
                prev_crit = previous.get("critical_threshold")
                prev_max_rul = previous.get("max_rul_cap")
                
                if prev_warn == warn and prev_crit == crit and prev_max_rul == max_rul:
                    return html.Span("No changes detected. Threshold values are the same as previously saved.",
                                    style={"color": "#ffa500", "fontSize": "13px"})
            
            threshold_data = {
                "warning_threshold": warn,
                "critical_threshold": crit,
                "max_rul_cap": max_rul,
                "updated_at": "now()",
            }
            
            # Add updated_by if user_id is available
            if user_id:
                threshold_data["updated_by"] = user_id
            
            supabase.table("alert_thresholds").insert(threshold_data).execute()
            return html.Span("Thresholds saved successfully!", style={"color": "#4aff9e", "fontSize": "13px"})
        except Exception as e:
            print(f"[ERROR] save thresholds: {e}")
            return html.Span(f"Failed to save: {str(e)}", style={"color": "#ff6b6b", "fontSize": "13px"})


# ─────────────────────────────────────────────
#  STANDALONE RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True)
    app.layout = html.Div([
        dcc.Store(id="sidebar-state", data=True),
        create_alert_thresholds_layout()
    ])
    register_alert_thresholds_callbacks(app)
    app.run(debug=True)
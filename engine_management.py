import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import base64
from datetime import datetime

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
        <circle cx="50" cy="50" r="48" fill="none" stroke="#4a9eff" stroke-width="1.5"/>
        <circle cx="50" cy="50" r="18" fill="none" stroke="#4a9eff" stroke-width="2"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(0 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(45 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(90 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(135 50 50)"/>
        <circle cx="50" cy="50" r="4" fill="#4a9eff"/>
    </svg>''', size="22px")

def icon_upload():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 16V4M12 4l-4 4M12 4l4 4"/>
      <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>
    </svg>''')

def icon_threshold():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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


# ─────────────────────────────────────────────
#  SIDEBAR  (Admin Panel variant)
# ─────────────────────────────────────────────

def build_admin_sidebar(active_page="engines"):
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
                html.Div("ADMIN PANEL", style={
                    "color": "rgba(168,212,255,0.5)", "fontSize": "10px", "fontWeight": "700",
                    "letterSpacing": "1.5px", "padding": "0 6px", "marginBottom": "10px",
                }),
                nav_link(icon_engine,    "Engine Management", "engines",   "/engine-management"),
                nav_link(icon_users,     "User Management",  "users",     "/user-management"),
                nav_link(icon_upload,    "Model Upload",     "model",     "/model-upload"),
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
#  STATUS BADGE
# ─────────────────────────────────────────────

def status_badge(status):
    status_lower = status.lower()
    cfg = {
        "healthy":  {"bg": "rgba(0,200,100,0.18)", "border": "#00c875", "text": "#00c875"},
        "warning":  {"bg": "rgba(255,217,61,0.18)", "border": "#ffd93d", "text": "#ffd93d"},
        "critical": {"bg": "rgba(255,77,77,0.18)",  "border": "#ff4d4d", "text": "#ff4d4d"},
    }
    c = cfg.get(status_lower, cfg["healthy"])
    label = status_lower.upper()

    badge = html.Span(label, style={
        "background": c["bg"], "color": c["text"], "border": f"1px solid {c['border']}",
        "borderRadius": "6px", "padding": "3px 10px", "fontSize": "11px", "fontWeight": "700",
        "whiteSpace": "nowrap", "display": "inline-block",
    })
    return html.Div(style={"display": "flex", "justifyContent": "flex-start"}, children=[badge])


# ─────────────────────────────────────────────
#  ENGINES TABLE
# ─────────────────────────────────────────────

def engine_table_row(engine, idx):
    return html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "0.8fr 1.2fr 0.8fr 1fr 0.8fr 1fr",
            "alignItems": "center",
            "padding": "12px 24px",
            "borderBottom": "1px solid rgba(74,158,255,0.08)",
        },
        children=[
            html.Span(f"ENGINE-{str(engine['engine_id']).zfill(2)}", 
                     style={"color": "white", "fontSize": "13px", "fontWeight": "600"}),
            html.Span(engine.get("model_type", "—"), 
                     style={"color": "#a8d4ff", "fontSize": "13px"}),
            status_badge(engine.get("condition_status", "healthy")),
            html.Span(f"{engine.get('current_cycle', 0)} cycles", 
                     style={"color": "#a8d4ff", "fontSize": "12px"}),
            html.Span(engine.get("created_at", "—"), 
                     style={"color": "#a8d4ff", "fontSize": "12px"}),
            html.Div(style={"display": "flex", "gap": "8px"}, children=[
                dcc.Link(
                    href=f"/overview/{engine['id']}",
                    style={"textDecoration": "none"},
                    children=[
                        html.Button("View", n_clicks=0, style={
                            "background": "rgba(74,158,255,0.18)", "border": "1px solid rgba(74,158,255,0.4)",
                            "color": "#a8d4ff", "borderRadius": "6px", "padding": "5px 12px",
                            "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                        })
                    ]
                ),
                html.Button("Edit", id={"type": "edit-engine-btn", "index": engine["id"]}, n_clicks=0, style={
                    "background": "rgba(74,158,255,0.18)", "border": "1px solid rgba(74,158,255,0.4)",
                    "color": "#a8d4ff", "borderRadius": "6px", "padding": "5px 12px",
                    "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                }),
                html.Button("Remove", id={"type": "remove-engine-btn", "index": engine["id"]}, n_clicks=0, style={
                    "background": "rgba(255,77,77,0.15)", "border": "1px solid rgba(255,77,77,0.4)",
                    "color": "#ff6b6b", "borderRadius": "6px", "padding": "5px 12px",
                    "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                }),
            ])
        ]
    )


def build_engines_table(engines):
    total = len(engines)
    healthy = sum(1 for e in engines if e.get("condition_status", "healthy").lower() == "healthy")
    warning = sum(1 for e in engines if e.get("condition_status", "healthy").lower() == "warning")
    critical = sum(1 for e in engines if e.get("condition_status", "healthy").lower() == "critical")

    return html.Div(
        style={
            "background": "#101e36", "border": "1px solid rgba(74,158,255,0.15)",
            "borderRadius": "14px", "overflow": "hidden",
        },
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "justifyContent": "space-between",
                       "padding": "16px 24px 12px"},
                children=[
                    html.Span("Engines", style={"color": "white", "fontSize": "15px", "fontWeight": "700"}),
                    html.Span(f"{total} total · {healthy} healthy · {warning} warning · {critical} critical",
                              style={"color": "rgba(168,212,255,0.5)", "fontSize": "12px"}),
                ]
            ),
            html.Div(
                style={
                    "display": "grid", "gridTemplateColumns": "0.8fr 1.2fr 0.8fr 1fr 0.8fr 1fr",
                    "padding": "10px 24px",
                    "background": "rgba(74,158,255,0.06)",
                    "borderTop": "1px solid rgba(74,158,255,0.12)",
                    "borderBottom": "1px solid rgba(74,158,255,0.12)",
                },
                children=[
                    html.Span("ENGINE ID",    style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("MODEL TYPE",   style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("STATUS",       style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("CURRENT CYCLE",style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("CREATED",      style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("ACTIONS",      style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                ]
            ),
            html.Div(id="engines-table-body",
                     children=[engine_table_row(e, i) for i, e in enumerate(engines)]),
        ]
    )

# ─────────────────────────────────────────────
#  MAIN PAGE BODY
# ─────────────────────────────────────────────

def build_engine_management_body(engines=None):
    if engines is None:
        engines = []

    return [
        # Header row: title + Add Engine button
        html.Div(
            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between",
                   "marginBottom": "8px"},
            children=[
                html.H2("ENGINE MANAGEMENT", style={"margin": "0", "color": "white",
                                                     "fontSize": "22px", "fontWeight": "800"}),
                dcc.Link(href="/add-engine", style={"textDecoration": "none"}, children=[
                    html.Button(
                        "+ Add Engine", id="add-engine-btn", n_clicks=0,
                        style={
                            "background": "linear-gradient(90deg, #1a6fd4 0%, #2a85f0 100%)",
                            "border": "none", "borderRadius": "8px", "color": "white",
                            "padding": "10px 20px", "fontSize": "13px", "fontWeight": "700",
                            "cursor": "pointer", "boxShadow": "0 2px 10px rgba(42,133,240,0.3)",
                        }
                    )
                ]),
            ]
        ),
        html.Div(style={"height": "1px", "background": "rgba(74,158,255,0.15)", "marginBottom": "20px"}),

        build_engines_table(engines),

        dcc.Store(id="engines-data", data=engines),
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_engine_management_layout(supabase=None, org_id=None):
    engines = []

    if not supabase:
        print("[WARN] Supabase not connected - no engine data available")
    else:
        try:
            query = supabase.table("engines") \
                .select("id, engine_id, model_type, condition_status, current_cycle, created_at")

            # Filter to this organization only
            if org_id:
                query = query.eq("organization_id", org_id)

            resp = query.order("engine_id").execute()
            
            if resp.data:
                for e in resp.data:
                    created_at = e.get("created_at")
                    if created_at:
                        try:
                            created_at = datetime.fromisoformat(
                                created_at.replace("Z", "+00:00")
                            ).strftime("%Y-%m-%d")
                        except Exception:
                            created_at = str(created_at)[:10]
                    else:
                        created_at = "—"

                    engines.append({
                        "id": str(e.get("id")),
                        "engine_id": e.get("engine_id", 0),
                        "model_type": e.get("model_type", "—"),
                        "condition_status": (e.get("condition_status") or "healthy").lower(),
                        "current_cycle": e.get("current_cycle", 0),
                        "created_at": created_at,
                    })
                    
                print(f"[OK] Loaded {len(engines)} engines from database")
            else:
                print("[INFO] No engines found in database")
                
        except Exception as e:
            import traceback
            print(f"[ERROR] engine management fetch: {traceback.format_exc()}")

    return html.Div(
        style={
            "minHeight": "100vh",
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628",
            "color": "white",
        },
        children=[
            dcc.Location(id="url-engine-mgmt", refresh=False),

            html.Div(
                style={
                    "position": "sticky",
                    "top": "0",
                    "zIndex": "200",
                },
                children=[build_topbar()]
            ),

            html.Div(
                style={
                    "flex": "1",
                    "display": "flex",
                    "flexDirection": "row",
                },
                children=[
                    build_admin_sidebar(active_page="engines"),
                    html.Div(
                        style={
                            "flex": "1",
                            "padding": "24px 28px",
                            "minWidth": "0",
                        },
                        children=build_engine_management_body(engines=engines),
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def register_engine_management_callbacks(app, supabase=None):

    @app.callback(
        Output("engines-table-body", "children"),
        Output("engines-data", "data"),
        Input({"type": "remove-engine-btn", "index": dash.ALL}, "n_clicks"),
        State("engines-data", "data"),
        prevent_initial_call=True,
    )
    def remove_engine(n_clicks_list, engines_data):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        import json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        engine_id = json.loads(trigger_id)["index"]

        # Remove from Supabase if connected
        if supabase:
            try:
                supabase.table("engines").delete().eq("id", engine_id).execute()
            except Exception as e:
                print(f"[ERROR] remove engine: {e}")

        updated = [e for e in engines_data if e["id"] != engine_id]
        rows = [engine_table_row(e, i) for i, e in enumerate(updated)]
        return rows, updated

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
        create_engine_management_layout()
    ])
    register_engine_management_callbacks(app)
    app.run(debug=True)

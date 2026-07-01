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
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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

def build_admin_sidebar(active_page="users"):
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
#  ROLE PERMISSION MATRIX DATA
# ─────────────────────────────────────────────

PERMISSION_MATRIX = [
    {"page": "Overview", "desc": "Engine status, RUL cards, alerts", "sme": True, "admin": True},
    {"page": "Sensor Trends", "desc": "Multi-sensor chart, normalize toggle", "sme": True, "admin": True},
    {"page": "Explainability AI", "desc": "SHAP charts, fault mode detection", "sme": True, "admin": True},
    {"page": "Alert Log", "desc": "View alerts", "sme": True, "admin": True},
    {"page": "Acknowledge / Resolve Alerts", "desc": "Change alert status", "sme": True, "admin": True},
    {"page": "Upload .h5 Model", "desc": "Replace active prediction model", "sme": False, "admin": True},
    {"page": "Admin Panel", "desc": "User management, permissions", "sme": False, "admin": True},
]


def permission_cell(allowed: bool):
    cell = html.Div("✓" if allowed else "X", style={
        "width": "26px", "height": "26px", "borderRadius": "6px",
        "background": "rgba(0,200,100,0.2)" if allowed else "rgba(255,255,255,0.04)",
        "border": f"1px solid {'#00c875' if allowed else 'rgba(255,255,255,0.1)'}",
        "color": "#00c875" if allowed else "rgba(255,255,255,0.3)",
        "fontWeight": "700", "fontSize": "13px" if allowed else "12px",
        "display": "flex", "alignItems": "center", "justifyContent": "center",
    })
    # Wrap in a centering container since parent is a grid cell
    return html.Div(style={"display": "flex", "justifyContent": "center"}, children=[cell])


def build_permission_matrix():
    rows = []
    for i, p in enumerate(PERMISSION_MATRIX):
        rows.append(
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "2fr 0.6fr 0.6fr",   # ← fractional, not fixed px
                    "alignItems": "center",
                    "padding": "14px 24px",
                    "borderBottom": "1px solid rgba(74,158,255,0.08)" if i < len(PERMISSION_MATRIX) - 1 else "none",
                },
                children=[
                    html.Div(children=[
                        html.Div(p["page"], style={"color": "white", "fontSize": "14px", "fontWeight": "700"}),
                        html.Div(p["desc"], style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                                    "marginTop": "2px"}),
                    ]),
                    permission_cell(p["sme"]),
                    permission_cell(p["admin"]),
                ]
            )
        )

    return html.Div(
        style={
            "background": "#101e36", "border": "1px solid rgba(74,158,255,0.15)",
            "borderRadius": "14px", "overflow": "hidden", "marginBottom": "24px",
        },
        children=[
            html.Div("Role Permission Matrix", style={
                "color": "#4a9eff", "fontSize": "15px", "fontWeight": "700",
                "padding": "16px 24px 12px",
            }),
            html.Div(
                style={
                    "display": "grid", "gridTemplateColumns": "2fr 0.6fr 0.6fr",
                    "padding": "10px 24px",
                    "background": "rgba(74,158,255,0.06)",
                    "borderTop": "1px solid rgba(74,158,255,0.12)",
                    "borderBottom": "1px solid rgba(74,158,255,0.12)",
                },
                children=[
                    html.Span("PAGE / ACTION", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                                        "fontWeight": "700", "letterSpacing": "0.5px"}),
                    html.Span("USER", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                                       "fontWeight": "700", "letterSpacing": "0.5px",
                                                       "textAlign": "center"}),
                    html.Span("ADMIN", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                                                 "fontWeight": "700", "letterSpacing": "0.5px",
                                                                 "textAlign": "center"}),
                ]
            ),
            html.Div(rows),
        ]
    )


# ─────────────────────────────────────────────
#  USERS TABLE
# ─────────────────────────────────────────────

def role_badge(role):
    role_lower = role.lower()
    is_admin = role_lower in ("admin", "administrator")

    cfg = {
        True:  ("rgba(74,158,255,0.18)",  "#4a9eff", "#4a9eff"),
        False: ("rgba(0,200,100,0.18)",   "#00c875", "#00c875"),
    }
    c = cfg[is_admin]
    label = "Admin" if is_admin else "User"

    badge = html.Span(label, style={
        "background": c[0], "color": c[1], "border": f"1px solid {c[2]}",
        "borderRadius": "6px", "padding": "3px 10px", "fontSize": "11px", "fontWeight": "700",
        "whiteSpace": "nowrap",
        "display": "inline-block",
    })

    return html.Div(style={"display": "flex", "justifyContent": "flex-start"}, children=[badge])


def status_dot(status):
    is_active = status.lower() == "active"
    color = "#00c875" if is_active else "rgba(168,212,255,0.4)"
    return html.Span(
        style={"display": "flex", "alignItems": "center", "gap": "6px"},
        children=[
            html.Span("●" if is_active else "○", style={"color": color, "fontSize": "10px"}),
            html.Span(status.capitalize(), style={"color": color, "fontSize": "12px"}),
        ]
    )


def user_table_row(user, idx):
    role_lower = user["role"].lower()
    is_admin = role_lower in ("admin", "administrator")

    return html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1.4fr 0.7fr 1fr 0.7fr 1fr",
            "alignItems": "center",
            "padding": "12px 24px",
            "borderBottom": "1px solid rgba(74,158,255,0.08)",
        },
        children=[
            html.Span(user["username"], style={"color": "white", "fontSize": "13px", "fontWeight": "600"}),
            html.Span(user["full_name"], style={"color": "#a8d4ff", "fontSize": "13px"}),
            role_badge(user["role"]),
            html.Span(user["last_login"], style={"color": "#a8d4ff", "fontSize": "12px"}),
            status_dot(user["status"]),
            html.Div(style={"display": "flex", "gap": "8px"}, children=[
                html.Button("Edit", id={"type": "edit-user-btn", "index": user["id"]}, n_clicks=0, style={
                    "background": "rgba(74,158,255,0.18)", "border": "1px solid rgba(74,158,255,0.4)",
                    "color": "#a8d4ff", "borderRadius": "6px", "padding": "5px 12px",
                    "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                }),
                html.Button("Remove", id={"type": "remove-user-btn", "index": user["id"]}, n_clicks=0, style={
                    "background": "rgba(255,77,77,0.15)", "border": "1px solid rgba(255,77,77,0.4)",
                    "color": "#ff6b6b", "borderRadius": "6px", "padding": "5px 12px",
                    "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                    "display": "none" if is_admin else "inline-block",   # ← fixed check
                }),
            ])
        ]
    )


def build_users_table(users):
    total = len(users)
    active = sum(1 for u in users if u["status"].lower() == "active")

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
                    html.Span("Users", style={"color": "white", "fontSize": "15px", "fontWeight": "700"}),
                    html.Span(f"{total} accounts · {active} active sessions",
                              style={"color": "rgba(168,212,255,0.5)", "fontSize": "12px"}),
                ]
            ),
            html.Div(
                style={
                    "display": "grid", "gridTemplateColumns": "1fr 1.4fr 0.7fr 1fr 0.7fr 1fr",   # ← match rows
                    "padding": "10px 24px",
                    "background": "rgba(74,158,255,0.06)",
                    "borderTop": "1px solid rgba(74,158,255,0.12)",
                    "borderBottom": "1px solid rgba(74,158,255,0.12)",
                },
                children=[
                    html.Span("USERNAME",   style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("FULL NAME",  style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("ROLE",       style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("LAST LOGIN", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("STATUS",     style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("ACTIONS",    style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                ]
            ),
            html.Div(id="users-table-body",
                     children=[user_table_row(u, i) for i, u in enumerate(users)]),
        ]
    )


# ─────────────────────────────────────────────
#  SAMPLE / FALLBACK USER DATA
# ─────────────────────────────────────────────

def _sample_users():
    return [
        {"id": "1", "username": "admin_ds",   "full_name": "Dr. Lim Wei",    "role": "admin",
         "last_login": "2025-05-26 14:00", "status": "active"},
        {"id": "2", "username": "user_01","full_name": "Ahmad Razif",    "role": "user",
         "last_login": "2025-05-26 09:14", "status": "active"},
        {"id": "3", "username": "user_02","full_name": "Nurul Ain",      "role": "user",
         "last_login": "2025-05-25 17:30", "status": "offline"},
        {"id": "4", "username": "user_03","full_name": "Hafiz Zain",     "role": "user",
         "last_login": "2025-05-24 11:00", "status": "offline"},
    ]


# ─────────────────────────────────────────────
#  MAIN PAGE BODY
# ─────────────────────────────────────────────

def build_user_management_body(users=None):
    if users is None:
        users = _sample_users()

    return [
        # Header row: title + Add User button
        html.Div(
            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between",
                   "marginBottom": "8px"},
            children=[
                html.H2("USER MANAGEMENT", style={"margin": "0", "color": "white",
                                                    "fontSize": "22px", "fontWeight": "800"}),
                dcc.Link(href="/add-user", style={"textDecoration": "none"}, children=[
                    html.Button(
                        "+ Add User", id="add-user-btn", n_clicks=0,
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

        build_permission_matrix(),
        build_users_table(users),

        dcc.Store(id="users-data", data=users),
        html.Div(id="add-user-modal-container"),
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_user_management_layout(supabase=None):
    users = None
    try:
        if supabase:
            resp = supabase.table("users") \
                .select("id, username, first_name, last_name, role, status, last_login_at") \
                .execute()
            if resp.data:
                users = []
                for u in resp.data:
                    last_login = u.get("last_login_at")
                    if last_login:
                        try:
                            last_login = datetime.fromisoformat(
                                last_login.replace("Z", "+00:00")
                            ).strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            last_login = str(last_login)
                    else:
                        last_login = "—"

                    full_name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or "—"

                    users.append({
                        "id": str(u.get("id")),
                        "username": u.get("username", "—"),
                        "full_name": full_name,
                        "role": (u.get("role") or "user").lower(),
                        "last_login": last_login,
                        "status": (u.get("status") or "offline").lower(),
                    })
    except Exception as e:
        import traceback
        print(f"[ERROR] user management fetch: {traceback.format_exc()}")

    if not users:
        users = _sample_users()

    return html.Div(
        style={
            "minHeight": "100vh",            # ← was height: 100vh + overflow hidden
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628",
            "color": "white",
        },
        children=[
            dcc.Location(id="url-user-mgmt", refresh=False),

            # Topbar stays sticky at top instead of flex-fixed
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
                    build_admin_sidebar(active_page="users"),
                    html.Div(
                        style={
                            "flex": "1",
                            "padding": "24px 28px",
                            "minWidth": "0",
                        },
                        children=build_user_management_body(users=users),
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def register_user_management_callbacks(app, supabase=None):

    @app.callback(
        Output("users-table-body", "children"),
        Output("users-data", "data"),
        Input({"type": "remove-user-btn", "index": dash.ALL}, "n_clicks"),
        State("users-data", "data"),
        prevent_initial_call=True,
    )
    def remove_user(n_clicks_list, users_data):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        import json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        user_id = json.loads(trigger_id)["index"]

        # Remove from Supabase if connected
        if supabase:
            try:
                supabase.table("users").delete().eq("id", user_id).execute()
            except Exception as e:
                print(f"[ERROR] remove user: {e}")

        updated = [u for u in users_data if u["id"] != user_id]
        rows = [user_table_row(u, i) for i, u in enumerate(updated)]
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
        create_user_management_layout()
    ])
    register_user_management_callbacks(app)
    app.run(debug=True)
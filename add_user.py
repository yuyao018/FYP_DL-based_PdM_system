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

def icon_person_outline():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="8" r="3.5"/>
      <path d="M5 21c0-4 3-7 7-7s7 3 7 7"/>
    </svg>''', size="20px")

def icon_lock_outline():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="5" y="11" width="14" height="9" rx="2"/>
      <path d="M8 11V8a4 4 0 0 1 8 0v3"/>
    </svg>''', size="20px")

def icon_shield():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 3l7 3v6c0 5-3.5 8-7 9-3.5-1-7-4-7-9V6z"/>
    </svg>''', size="20px")

def icon_eye():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>''', size="20px")

def icon_user_role(active=False):
    color = "white" if active else "rgba(168,212,255,0.5)"
    return _svg_img(f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M3 18a9 9 0 0 1 18 0"/>
      <circle cx="12" cy="9" r="3.5"/>
      <path d="M9 4l3-2 3 2"/>
    </svg>''', size="34px")

def icon_admin_role(active=False):
    color = "white" if active else "rgba(168,212,255,0.4)"
    return _svg_img(f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 3l7 3v6c0 5-3.5 8-7 9-3.5-1-7-4-7-9V6z"/>
      <circle cx="12" cy="11" r="2"/>
    </svg>''', size="34px")

def icon_check_circle():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#00c875" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="20 6 9 17 4 12"/>
    </svg>''', size="16px")


# ─────────────────────────────────────────────
#  SIDEBAR  (Admin Panel variant — shared with user_management.py)
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
#  PERMISSION PREVIEW DATA  (mirrors PERMISSION_MATRIX)
# ─────────────────────────────────────────────

ACCESS_PREVIEW = [
    ("Overview",             "overview"),
    ("Sensor Trends",        "sensor"),
    ("Degradation Analysis", "degradation_analysis"),
    ("Alert Log",            "alert_log"),
    ("Acknowledge Alerts",   "acknowledge"),
    ("Upload .h5 Model",     "model_upload"),
    ("Admin Panel",          "admin_panel"),
]

# Which features each role gets, by key
ROLE_ACCESS = {
    "user":  {"overview", "sensor", "degradation_analysis", "alert_log", "acknowledge"},
    "admin": {"overview", "sensor", "degradation_analysis", "alert_log", "acknowledge",
              "model_upload", "admin_panel"},
}


# ─────────────────────────────────────────────
#  FORM FIELD HELPERS
# ─────────────────────────────────────────────

def form_label(text):
    return html.Label(text.upper(), style={
        "color": "#4a9eff", "fontSize": "11px", "fontWeight": "700",
        "letterSpacing": "0.8px", "marginBottom": "6px", "display": "block",
    })


def text_input(input_id, placeholder="", value="", input_type="text", icon=None):
    inner = []
    if icon:
        inner.append(html.Div(style={"display": "flex", "alignItems": "center",
                                      "paddingLeft": "12px"}, children=[icon]))
    inner.append(
        dcc.Input(
            id=input_id,
            type=input_type,
            placeholder=placeholder,
            value=value,
            style={
                "flex": "1", "background": "transparent", "border": "none",
                "outline": "none", "color": "white", "fontSize": "14px",
                "fontFamily": "inherit", "padding": "10px 12px",
            }
        )
    )
    return html.Div(
        style={
            "display": "flex", "alignItems": "center",
            "background": "rgba(10,20,45,0.6)",
            "border": "1.5px solid rgba(74,158,255,0.25)",
            "borderRadius": "8px",
        },
        children=inner
    )


def form_field(label_text, input_id, placeholder="", value="", input_type="text", icon=None):
    return html.Div(style={"flex": "1"}, children=[
        form_label(label_text),
        text_input(input_id, placeholder, value, input_type, icon),
    ])


# ─────────────────────────────────────────────
#  ROLE SELECTOR CARD
# ─────────────────────────────────────────────

def role_card(role_key, label, icon_fn, is_active):
    return html.Div(
        id={"type": "role-card", "index": role_key},
        n_clicks=0,
        style={
            "flex": "1",
            "border": f"2px solid {'#4a9eff' if is_active else 'rgba(74,158,255,0.2)'}",
            "background": "rgba(74,158,255,0.12)" if is_active else "rgba(74,158,255,0.04)",
            "borderRadius": "10px",
            "padding": "26px 16px",
            "display": "flex", "flexDirection": "column", "alignItems": "center", "gap": "10px",
            "cursor": "pointer", "transition": "all 0.2s",
        },
        children=[
            icon_fn(active=is_active),
            html.Span(label, style={
                "color": "white" if is_active else "rgba(168,212,255,0.5)",
                "fontSize": "13px", "fontWeight": "700", "letterSpacing": "1px",
            }),
        ]
    )


def build_role_selector(selected_role="user"):
    return html.Div(
        id="role-selector-container",
        style={"display": "flex", "gap": "14px"},
        children=[
            role_card("user",  "USER",  icon_user_role,  selected_role == "user"),
            role_card("admin", "ADMIN", icon_admin_role, selected_role == "admin"),
        ]
    )


# ─────────────────────────────────────────────
#  ACCESS PREVIEW LIST
# ─────────────────────────────────────────────

def access_preview_row(label, key, allowed):
    return html.Div(
        style={
            "display": "flex", "alignItems": "center", "justifyContent": "space-between",
            "padding": "9px 0", "borderBottom": "1px solid rgba(74,158,255,0.08)",
        },
        children=[
            html.Span(label, style={"color": "white", "fontSize": "13px"}),
            html.Div(
                style={
                    "width": "22px", "height": "22px", "borderRadius": "6px",
                    "background": "rgba(0,200,100,0.18)" if allowed else "rgba(255,255,255,0.04)",
                    "border": f"1px solid {'#00c875' if allowed else 'rgba(255,255,255,0.1)'}",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                },
                children=[icon_check_circle()] if allowed else []
            )
        ]
    )


def build_access_preview(selected_role="user"):
    allowed_keys = ROLE_ACCESS.get(selected_role, ROLE_ACCESS["user"])
    return html.Div(
        id="access-preview-list",
        children=[
            access_preview_row(label, key, key in allowed_keys)
            for label, key in ACCESS_PREVIEW
        ]
    )


# ─────────────────────────────────────────────
#  PANEL WRAPPER
# ─────────────────────────────────────────────

def panel(title, icon_fn, children, subtitle=None):
    header_children = [
        icon_fn(),
        html.Span(title, style={"color": "white", "fontSize": "16px", "fontWeight": "700"}),
    ]
    return html.Div(
        style={
            "background": "#101e36", "border": "1px solid rgba(74,158,255,0.18)",
            "borderRadius": "14px", "padding": "20px 22px", "marginBottom": "16px",
        },
        children=[
            html.Div(style={"display": "flex", "alignItems": "center", "gap": "10px",
                            "marginBottom": "4px" if subtitle else "16px"},
                     children=header_children),
            html.Div(subtitle, style={"color": "rgba(168,212,255,0.5)", "fontSize": "12px",
                                       "marginBottom": "16px"}) if subtitle else None,
            *children,
        ]
    )


# ─────────────────────────────────────────────
#  MAIN PAGE BODY
# ─────────────────────────────────────────────

def build_add_user_body():
    return [
        # Page title
        html.Div(
            style={"marginBottom": "8px"},
            children=[
                html.H2("ADD NEW USER", style={"margin": "0", "color": "white",
                                                "fontSize": "22px", "fontWeight": "800"}),
                html.Div("Create a new account and assign a role",
                         style={"color": "rgba(168,212,255,0.6)", "fontSize": "13px", "marginTop": "4px"}),
            ]
        ),
        html.Div(style={"height": "1px", "background": "rgba(74,158,255,0.15)",
                        "margin": "16px 0 20px"}),

        # Two-column layout
        html.Div(
            style={"display": "flex", "gap": "20px", "alignItems": "flex-start"},
            children=[

                # Left column: Personal Info + Account Credentials
                html.Div(
                    style={"flex": "1.3"},
                    children=[
                        panel("Personal Information", icon_person_outline, [
                            html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "16px"}, children=[
                                form_field("First Name", "new-user-first-name", "John"),
                                form_field("Last Name",  "new-user-last-name",  "Doe"),
                            ]),
                            html.Div(style={"marginBottom": "16px"}, children=[
                                form_field("Email Address", "new-user-email", "doe@example.com", input_type="email"),
                            ]),
                            html.Div(children=[
                                form_field("Department", "new-user-department", "R&D"),
                            ]),
                        ]),

                        panel("Account Credentials", icon_lock_outline, [
                            html.Div(style={"marginBottom": "16px"}, children=[
                                form_field("Username", "new-user-username", "John01"),
                            ]),
                            html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "14px"}, children=[
                                form_field("Password", "new-user-password", "", input_type="password",
                                          icon=icon_lock_outline()),
                                form_field("Confirm Password", "new-user-confirm-password", "", input_type="password",
                                          icon=icon_lock_outline()),
                            ]),
                            html.Div(
                                "User will be prompted to change password on first login",
                                style={
                                    "color": "#4a9eff", "fontSize": "12px", "textAlign": "center",
                                    "background": "rgba(74,158,255,0.06)",
                                    "border": "1px solid rgba(74,158,255,0.15)",
                                    "borderRadius": "8px", "padding": "10px",
                                }
                            ),
                        ], subtitle=None),
                    ]
                ),

                # Right column: Assign Role + Access Preview
                html.Div(
                    style={"flex": "1"},
                    children=[
                        panel("Assign Role", icon_shield, [
                            build_role_selector(selected_role="user"),
                        ]),
                        panel("Access Preview", icon_eye, [
                            build_access_preview(selected_role="user"),
                        ]),
                    ]
                ),
            ]
        ),

        # Footer action buttons
        html.Div(
            style={"display": "flex", "justifyContent": "flex-end", "gap": "12px", "marginTop": "8px"},
            children=[
                dcc.Link(href="/user-management", style={"textDecoration": "none"}, children=[
                    html.Button("Cancel", id="cancel-add-user-btn", n_clicks=0, style={
                        "background": "rgba(74,158,255,0.08)", "border": "1px solid rgba(74,158,255,0.25)",
                        "color": "rgba(168,212,255,0.7)", "borderRadius": "8px",
                        "padding": "12px 28px", "fontSize": "14px", "fontWeight": "600", "cursor": "pointer",
                    })
                ]),
                html.Button("Create Account", id="create-user-btn", n_clicks=0, style={
                    "background": "linear-gradient(90deg, #1a6fd4 0%, #2a85f0 100%)",
                    "border": "none", "borderRadius": "8px", "color": "white",
                    "padding": "12px 28px", "fontSize": "14px", "fontWeight": "700",
                    "cursor": "pointer", "boxShadow": "0 2px 10px rgba(42,133,240,0.3)",
                }),
            ]
        ),

        dcc.Store(id="selected-role-store", data="user"),
        html.Div(id="add-user-status", style={"marginTop": "12px", "textAlign": "right"}),
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_add_user_layout(supabase=None):
    return html.Div(
        style={
            "minHeight": "100vh",
            "display": "flex", "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628", "color": "white",
        },
        children=[
            dcc.Location(id="url-add-user", refresh=False),

            html.Div(style={"position": "sticky", "top": "0", "zIndex": "200"},
                     children=[build_topbar()]),

            html.Div(
                style={"flex": "1", "display": "flex", "flexDirection": "row"},
                children=[
                    build_admin_sidebar(active_page="users"),
                    html.Div(
                        style={"flex": "1", "padding": "24px 28px", "minWidth": "0"},
                        children=build_add_user_body(),
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def register_add_user_callbacks(app, supabase=None):

    # Role card selection toggles styling + access preview
    @app.callback(
        Output("role-selector-container", "children"),
        Output("access-preview-list", "children"),
        Output("selected-role-store", "data"),
        Input({"type": "role-card", "index": dash.ALL}, "n_clicks"),
        State("selected-role-store", "data"),
        prevent_initial_call=True,
    )
    def select_role(n_clicks_list, current_role):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        import json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        role_key = json.loads(trigger_id)["index"]

        selector = build_role_selector(selected_role=role_key)
        preview = build_access_preview(selected_role=role_key)

        return selector.children, preview.children, role_key

    # Create account
    @app.callback(
        Output("add-user-status", "children"),
        Output("url-add-user", "pathname"),
        Input("create-user-btn", "n_clicks"),
        State("new-user-first-name", "value"),
        State("new-user-last-name", "value"),
        State("new-user-email", "value"),
        State("new-user-department", "value"),
        State("new-user-username", "value"),
        State("new-user-password", "value"),
        State("new-user-confirm-password", "value"),
        State("selected-role-store", "data"),
        prevent_initial_call=True,
    )
    def create_user(n_clicks, first_name, last_name, email, department,
                    username, password, confirm_password, role):

        if not all([first_name, last_name, email, username, password, confirm_password]):
            return html.Span("Please fill in all required fields.",
                            style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        if password != confirm_password:
            return html.Span("Passwords do not match.",
                            style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        if len(password) < 8:
            return html.Span("Password must be at least 8 characters.",
                            style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        if not supabase:
            return html.Span("Supabase not connected.",
                            style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        try:
            # Step 1: Create auth user
            auth_resp = supabase.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
            })
            user_id = auth_resp.user.id

            # Step 2: Insert profile
            supabase.table("users").insert({
                "id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "email_address": email,
                "department": department,
                "role": "admin" if role == "admin" else "user",
                "status": "inactive",
                "created_at": "now()",
            }).execute()

            return (
                html.Span("Account created successfully!",
                         style={"color": "#4aff9e", "fontSize": "13px"}),
                "/user-management"
            )

        except Exception as e:
            print(f"[ERROR] create user: {e}")
            return html.Span(f"Failed to create account: {str(e)}",
                            style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

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
        create_add_user_layout()
    ])
    register_add_user_callbacks(app)
    app.run(debug=True)
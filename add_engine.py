import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import base64
import os

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
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(90 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(180 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(270 50 50)"/>
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

def icon_settings():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 1v3M12 20v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12
               M1 12h3M20 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/>
    </svg>''', size="20px")

def icon_info():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="16" x2="12" y2="12"/>
      <circle cx="12" cy="8" r="0.5" fill="#a8d4ff"/>
    </svg>''', size="20px")

def icon_hash():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <line x1="4" y1="9" x2="20" y2="9"/>
      <line x1="4" y1="15" x2="20" y2="15"/>
      <line x1="10" y1="3" x2="8" y2="21"/>
      <line x1="16" y1="3" x2="14" y2="21"/>
    </svg>''', size="20px")


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
    
    # Build style dict for input - force text type to avoid spinners
    input_style = {
        "flex": "1", 
        "background": "transparent", 
        "border": "none",
        "outline": "none", 
        "color": "white", 
        "fontSize": "14px",
        "fontFamily": "inherit", 
        "padding": "10px 12px",
        "width": "100%",
        "MozAppearance": "textfield",  # Firefox
        "WebkitAppearance": "none",     # Chrome/Safari
    }
    
    # For number inputs, use text type but with pattern validation
    actual_type = "text" if input_type == "number" else input_type
    extra_props = {}
    if input_type == "number":
        extra_props = {
            "pattern": "[0-9]*",
            "inputMode": "numeric"
        }
    
    inner.append(
        dcc.Input(
            id=input_id,
            type=actual_type,
            placeholder=placeholder,
            value=value,
            style=input_style,
            **extra_props
        )
    )
    return html.Div(
        style={
            "display": "flex", 
            "alignItems": "center",
            "background": "rgba(10,20,45,0.6)",
            "border": "1.5px solid rgba(74,158,255,0.25)",
            "borderRadius": "8px",
        },
        children=inner
    )


def dropdown_input(input_id, options, value=None, placeholder="Select..."):
    return dcc.Dropdown(
        id=input_id,
        options=options,
        value=value,
        placeholder=placeholder,
        clearable=False,
        style={
            "backgroundColor": "transparent",
            "border": "none",
        },
        optionHeight=40,
    )


def form_field(label_text, input_id, placeholder="", value="", input_type="text", icon=None):
    return html.Div(style={"flex": "1"}, children=[
        form_label(label_text),
        text_input(input_id, placeholder, value, input_type, icon),
    ])


def form_field_dropdown(label_text, input_id, options, value=None, placeholder="Select..."):
    return html.Div(style={"flex": "1", "position": "relative", "zIndex": "50"}, children=[
        form_label(label_text),
        html.Div(
            style={
                "background": "rgba(10,20,45,0.6)",
                "border": "1.5px solid rgba(74,158,255,0.25)",
                "borderRadius": "8px",
                "position": "relative",
            },
            children=[
                dcc.Dropdown(
                    id=input_id,
                    options=options,
                    value=value,
                    placeholder=placeholder,
                    clearable=False,
                    searchable=False,
                    style={
                        "backgroundColor": "transparent",
                        "border": "none",
                        "color": "white",
                    },
                    className="dark-dropdown",
                )
            ]
        )
    ])


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

def build_add_engine_body():
    return [
        # Page title
        html.Div(
            style={"marginBottom": "8px"},
            children=[
                html.H2("ADD NEW ENGINE", style={"margin": "0", "color": "white",
                                                  "fontSize": "22px", "fontWeight": "800"}),
                html.Div("Register a new engine to the monitoring system",
                         style={"color": "rgba(168,212,255,0.6)", "fontSize": "13px", "marginTop": "4px"}),
            ]
        ),
        html.Div(style={"height": "1px", "background": "rgba(74,158,255,0.15)",
                        "margin": "16px 0 20px"}),

        # Single column layout
        html.Div(
            style={"maxWidth": "800px", "margin": "0 auto"},
            children=[
                panel("Engine Identification", icon_hash, [
                    html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "16px"}, children=[
                        form_field("Engine ID", "new-engine-id", "1", input_type="number"),
                        form_field_dropdown("Model Type", "new-engine-model", 
                                          options=[
                                              {"label": "FD001", "value": "FD001"},
                                              {"label": "FD002", "value": "FD002"},
                                              {"label": "FD003", "value": "FD003"},
                                              {"label": "FD004", "value": "FD004"},
                                          ],
                                          value="FD001"),
                    ]),
                    html.Div(
                        "Engine ID must be unique within the system",
                        style={
                            "color": "#4a9eff", "fontSize": "12px",
                            "background": "rgba(74,158,255,0.06)",
                            "border": "1px solid rgba(74,158,255,0.15)",
                            "borderRadius": "8px", "padding": "10px",
                        }
                    ),
                ]),

                panel("Initial Configuration", icon_settings, [
                    html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "16px",
                                    "position": "relative", "zIndex": "100"}, children=[
                        form_field_dropdown("Assign To", "new-engine-assign-to",
                                          options=[],  # populated by callback from users table
                                          placeholder="Select user..."),
                    ]),
                    html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "16px"}, children=[
                        html.Div(style={"flex": "1"}, children=[
                            form_label("Name"),
                            text_input("new-engine-assign-name", "", "", "text"),
                        ]),
                        html.Div(style={"flex": "1"}, children=[
                            form_label("Email Address"),
                            text_input("new-engine-assign-email", "", "", "text"),
                        ]),
                    ]),
                    html.Div(style={"display": "flex", "gap": "16px"}, children=[
                        html.Div(style={"flex": "1"}, children=[
                            form_label("Department"),
                            text_input("new-engine-assign-dept", "", "", "text"),
                        ]),
                        form_field("Installation Location", "new-engine-location", "Hangar A"),
                    ]),
                ], subtitle="Assign responsible personnel and set location"),

                panel("Additional Information", icon_info, [
                    html.Div(children=[
                        form_label("Notes"),
                        dcc.Textarea(
                            id="new-engine-notes",
                            placeholder="Add any relevant notes about this engine...",
                            style={
                                "width": "100%", "minHeight": "100px",
                                "background": "rgba(10,20,45,0.6)",
                                "border": "1.5px solid rgba(74,158,255,0.25)",
                                "borderRadius": "8px", "color": "white",
                                "fontSize": "14px", "fontFamily": "inherit",
                                "padding": "10px 12px", "resize": "vertical",
                            }
                        ),
                    ]),
                ], subtitle="Optional: Add any additional information"),
            ]
        ),

        # Footer action buttons
        html.Div(
            style={"display": "flex", "justifyContent": "flex-end", "gap": "12px", "marginTop": "8px"},
            children=[
                dcc.Link(href="/engine-management", style={"textDecoration": "none"}, children=[
                    html.Button("Cancel", id="cancel-add-engine-btn", n_clicks=0, style={
                        "background": "rgba(74,158,255,0.08)", "border": "1px solid rgba(74,158,255,0.25)",
                        "color": "rgba(168,212,255,0.7)", "borderRadius": "8px",
                        "padding": "12px 28px", "fontSize": "14px", "fontWeight": "600", "cursor": "pointer",
                    })
                ]),
                html.Button("Register Engine", id="create-engine-btn", n_clicks=0, style={
                    "background": "linear-gradient(90deg, #1a6fd4 0%, #2a85f0 100%)",
                    "border": "none", "borderRadius": "8px", "color": "white",
                    "padding": "12px 28px", "fontSize": "14px", "fontWeight": "700",
                    "cursor": "pointer", "boxShadow": "0 2px 10px rgba(42,133,240,0.3)",
                }),
            ]
        ),

        html.Div(id="add-engine-status", style={"marginTop": "12px", "textAlign": "right"}),
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_add_engine_layout(supabase=None, org_id=None):
    return html.Div(
        style={
            "height": "100vh",
            "display": "flex", "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628", "color": "white",
            "overflow": "hidden",
        },
        children=[
            dcc.Location(id="url-add-engine", refresh=False),
            # Store org_id so the create callback can access it
            dcc.Store(id="add-engine-org-store", data=org_id),

            build_topbar(),

            html.Div(
                style={"flex": "1", "display": "flex", "flexDirection": "row",
                       "overflow": "hidden", "minHeight": "0"},
                children=[
                    build_admin_sidebar(active_page="engines"),
                    html.Div(
                        style={"flex": "1", "overflowY": "auto", "padding": "24px 28px",
                               "minWidth": "0"},
                        children=build_add_engine_body(),
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def register_add_engine_callbacks(app, supabase=None):

    # ── Populate "Assign To" dropdown with users from the same organization ──
    @app.callback(
        Output("new-engine-assign-to", "options"),
        Input("url-add-engine", "pathname"),
        State("add-engine-org-store", "data"),
    )
    def load_users_dropdown(_, org_id):
        if not supabase:
            return []
        try:
            query = supabase.table("users") \
                .select("id, username, first_name, last_name, email_address, department")
            if org_id:
                query = query.eq("organization_id", org_id)
            resp = query.execute()
            options = []
            for u in (resp.data or []):
                name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()
                label = f"{name} ({u.get('username', '')})" if name else u.get("username", "")
                options.append({"label": label, "value": u["id"]})
            return options
        except Exception:
            return []

    # ── Auto-fill Name, Email, Department when user is selected ──
    @app.callback(
        Output("new-engine-assign-name", "value"),
        Output("new-engine-assign-email", "value"),
        Output("new-engine-assign-dept", "value"),
        Input("new-engine-assign-to", "value"),
        prevent_initial_call=True,
    )
    def autofill_user_info(user_id):
        if not user_id or not supabase:
            return "", "", ""
        try:
            resp = supabase.table("users") \
                .select("first_name, last_name, email_address, department") \
                .eq("id", user_id) \
                .single() \
                .execute()
            u = resp.data or {}
            name = f"{u.get('last_name', '')} {u.get('first_name', '')}".strip()
            email = u.get("email_address", "")
            dept = u.get("department", "")
            return name, email, dept
        except Exception:
            return "", "", ""

    @app.callback(
        Output("add-engine-status", "children"),
        Output("url", "pathname", allow_duplicate=True),
        Input("create-engine-btn", "n_clicks"),
        State("new-engine-id", "value"),
        State("new-engine-model", "value"),
        State("new-engine-assign-to", "value"),
        State("new-engine-location", "value"),
        State("new-engine-notes", "value"),
        State("add-engine-org-store", "data"),
        prevent_initial_call=True,
    )
    def create_engine(n_clicks, engine_id, model_type, assign_to_user_id,
                     location, notes, org_id):
        if not engine_id or not model_type:
            return html.Span("Please fill in required fields (Engine ID and Model Type).",
                            style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        try:
            engine_id = int(engine_id)
        except ValueError:
            return html.Span("Engine ID must be a valid number.",
                            style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        if engine_id < 1:
            return html.Span("Engine ID must be a positive number.",
                            style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        if not supabase:
            return html.Span("Supabase not connected.",
                            style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        try:
            # ── 1. Check uniqueness within the same organization ──
            check_q = supabase.table("engines") \
                .select("engine_id") \
                .eq("engine_id", engine_id)
            if org_id:
                check_q = check_q.eq("organization_id", org_id)
            if check_q.execute().data:
                return html.Span(f"Engine ID {engine_id} already exists in your organization.",
                                style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

            # ── 2. Fetch organization name for folder naming ──
            org_name = "unknown_org"
            if org_id:
                org_resp = supabase.table("organizations") \
                    .select("name") \
                    .eq("id", org_id) \
                    .single() \
                    .execute()
                if org_resp.data:
                    # Sanitize org name for use as folder name
                    raw_name = org_resp.data.get("name", "unknown_org")
                    org_name = raw_name.strip().lower() \
                        .replace(" ", "_") \
                        .replace("/", "_") \
                        .replace("\\", "_")

            # ── 3. Insert engine into database first to get UUID ──
            payload = {
                "engine_id":        engine_id,
                "model_type":       model_type,
                "current_cycle":    0,
                "condition_status": "healthy",
                "created_at":       "now()",
            }
            if org_id:
                payload["organization_id"] = org_id
            if assign_to_user_id:
                payload["responsible_by"] = assign_to_user_id

            result = supabase.table("engines").insert(payload).execute()

            # Get the new engine's UUID (returned by Supabase)
            new_engine_db_id = None
            if result.data:
                new_engine_db_id = str(result.data[0].get("id", ""))

            # ── 4. Create data file: data/[org_name]_[org_id]/engine_<db_id>.json ──
            from data_utils import create_engine_data_file, get_org_folder

            file_path = create_engine_data_file(
                org_name=org_name,
                org_id=org_id or "local",
                engine_id=engine_id,
                model_type=model_type,
                db_id=new_engine_db_id,
            )
            folder_name = get_org_folder(org_name, org_id or "local")
            engine_file = f"engine_{new_engine_db_id}.json" if new_engine_db_id else f"engine_{str(engine_id).zfill(3)}.json"
            # ── Start background simulation if JSON data file already has cycles ──
            if new_engine_db_id and os.path.exists(file_path):
                try:
                    import json as _json
                    with open(file_path) as _f:
                        _d = _json.load(_f)
                    has_cycles = (
                        (isinstance(_d, list) and len(_d) > 0) or
                        (isinstance(_d, dict) and len(_d.get("cycles", [])) > 0)
                    )
                    if has_cycles:
                        from engine_simulation_manager import start_engine_simulation
                        start_engine_simulation(
                            engine_db_id=new_engine_db_id,
                            json_path=file_path,
                            model_type=model_type,
                            supabase=supabase,
                        )
                except Exception as _sim_err:
                    print(f"[WARN] Could not start simulation for engine {engine_id}: {_sim_err}")

            print(f"[OK] Engine {engine_id} registered | file: {file_path}")
            return (
                html.Span(
                    f"Engine registered! Paste sensor data into: data/{folder_name}/{engine_file}",
                    style={"color": "#4aff9e", "fontSize": "13px"}
                ),
                "/engine-management"
            )

        except Exception as e:
            print(f"[ERROR] create engine: {e}")
            return html.Span(f"Failed to register engine: {str(e)}",
                            style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update


# ─────────────────────────────────────────────
#  STANDALONE RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True)
    app.layout = html.Div([
        dcc.Store(id="sidebar-state", data=True),
        create_add_engine_layout()
    ])
    register_add_engine_callbacks(app)
    app.run(debug=True)

"""
Developer - New Organization Page
Form to create a new organization. An admin account is automatically
created for the organization upon successful creation.
"""
import dash
from dash import dcc, html, Input, Output, State
import base64
import bcrypt
from assets.components import (build_dev_sidebar, icon_sidebar, gear_icon, org_icon, activity_icon)

def create_new_organization_layout():
    """Page with a form to create a new organization + default admin account."""

    field_label_style = {
        "color": "rgba(180,210,255,0.7)", "fontSize": "11px",
        "fontWeight": "600", "letterSpacing": "1.5px",
        "marginBottom": "8px", "display": "block",
    }
    field_input_style = {
        "width": "100%", "background": "rgba(10,25,55,0.8)",
        "border": "1px solid rgba(74,158,255,0.3)",
        "borderRadius": "8px", "padding": "10px 14px",
        "color": "rgba(200,220,255,0.9)", "fontSize": "14px",
        "outline": "none", "fontFamily": "inherit",
    }

    return html.Div(
        style={
            "height": "100vh",
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": "'Segoe UI', sans-serif",
            "background": "#0a1628",
            "color": "white",
            "overflow": "hidden",
        },
        children=[
            dcc.Location(id='url-dev-new-org', refresh=False),

            # ── Topbar ──
            html.Div(
                style={
                    "background": "linear-gradient(90deg, #0d2045 0%, #071530 100%)",
                    "borderBottom": "1px solid rgba(74,158,255,0.18)",
                    "padding": "0 28px",
                    "height": "60px", "minHeight": "60px", "flexShrink": "0",
                    "display": "flex", "alignItems": "center", "justifyContent": "space-between",
                    "zIndex": "200", "width": "100%",
                },
                children=[
                    html.H1("NEW ORGANIZATION", style={
                        "margin": "0", "fontSize": "18px", "fontWeight": "700",
                        "color": "white", "letterSpacing": "1.2px",
                    }),
                    html.Div(id="sidebar-toggle", n_clicks=0, style={"cursor": "pointer"}, children=[icon_sidebar()]),
                ]
            ),

            # ── Body: sidebar + content ──
            html.Div(
                style={"flex": "1", "display": "flex", "flexDirection": "row", "overflow": "hidden", "minHeight": "0"},
                children=[
                    build_dev_sidebar(active_page="new_org"),

                    # Content area
                    html.Div(
                        style={"flex": "1", "overflowY": "auto", "padding": "40px 48px", "minWidth": "0"},
                        children=[
                            # Form container
                            html.Div(
                                style={
                                    "maxWidth": "600px", "margin": "0 auto",
                                    "background": "#0d1e3a",
                                    "border": "1px solid rgba(74,158,255,0.2)",
                                    "borderRadius": "16px", "padding": "36px 40px",
                                },
                                children=[
                                    html.H2("Create New Organization", style={
                                        "color": "white", "fontWeight": "700", "fontSize": "22px",
                                        "marginBottom": "6px", "marginTop": "0",
                                    }),
                                    html.P("A default admin account will be created for this organization.", style={
                                        "color": "rgba(168,212,255,0.6)", "fontSize": "13px", "marginBottom": "30px",
                                    }),

                                    # ── Organization Name ──
                                    html.Div(style={"marginBottom": "20px"}, children=[
                                        html.Label("ORGANIZATION NAME", style=field_label_style),
                                        dcc.Input(id="new-org-name", type="text", placeholder="e.g. Acme Corp",
                                                  style=field_input_style),
                                    ]),

                                    # ── Section header: Default Admin Account ──
                                    html.Div(style={
                                        "borderTop": "1px solid rgba(74,158,255,0.15)",
                                        "paddingTop": "20px", "marginTop": "10px", "marginBottom": "20px",
                                    }, children=[
                                        html.H3("Default Admin Account", style={
                                            "color": "#4a9eff", "fontWeight": "700", "fontSize": "16px", "margin": "0 0 4px 0",
                                        }),
                                        html.P("These credentials will be used to log in as admin for this organization.", style={
                                            "color": "rgba(168,212,255,0.5)", "fontSize": "12px", "margin": "0",
                                        }),
                                    ]),

                                    # ── Admin First Name ──
                                    html.Div(style={"marginBottom": "20px"}, children=[
                                        html.Label("FIRST NAME", style=field_label_style),
                                        dcc.Input(id="new-org-admin-firstname", type="text", placeholder="e.g. John",
                                                  style=field_input_style),
                                    ]),

                                    # ── Admin Last Name ──
                                    html.Div(style={"marginBottom": "20px"}, children=[
                                        html.Label("LAST NAME", style=field_label_style),
                                        dcc.Input(id="new-org-admin-lastname", type="text", placeholder="e.g. Doe",
                                                  style=field_input_style),
                                    ]),

                                    # ── Admin Username ──
                                    html.Div(style={"marginBottom": "20px"}, children=[
                                        html.Label("ADMIN USERNAME", style=field_label_style),
                                        dcc.Input(id="new-org-admin-username", type="text", placeholder="e.g. admin_acme",
                                                  style=field_input_style),
                                    ]),

                                    # ── Admin Email ──
                                    html.Div(style={"marginBottom": "20px"}, children=[
                                        html.Label("ADMIN EMAIL", style=field_label_style),
                                        dcc.Input(id="new-org-admin-email", type="email", placeholder="e.g. admin@acme.com",
                                                  style=field_input_style),
                                    ]),

                                    # ── Admin Password ──
                                    html.Div(style={"marginBottom": "28px"}, children=[
                                        html.Label("ADMIN PASSWORD", style=field_label_style),
                                        dcc.Input(id="new-org-admin-password", type="password", placeholder="Minimum 8 characters",
                                                  style=field_input_style),
                                    ]),

                                    # ── Submit button ──
                                    html.Button(
                                        "Create Organization",
                                        id="new-org-submit-btn",
                                        n_clicks=0,
                                        style={
                                            "width": "100%", "padding": "14px",
                                            "background": "linear-gradient(90deg, #1a6fd4 0%, #2a85f0 100%)",
                                            "border": "none", "borderRadius": "8px",
                                            "color": "white", "fontSize": "15px",
                                            "fontWeight": "700", "cursor": "pointer",
                                            "boxShadow": "0 4px 20px rgba(42,133,240,0.35)",
                                            "fontFamily": "inherit", "transition": "all 0.2s",
                                        }
                                    ),

                                    # ── Status message ──
                                    html.Div(id="new-org-status", style={"marginTop": "16px", "minHeight": "24px"}),
                                ]
                            )
                        ]
                    )
                ]
            ),
        ]
    )


# ═════════════════════════════════════════════
#  CALLBACKS
# ═════════════════════════════════════════════

def register_new_organization_callbacks(app, supabase=None, supabase_admin=None):
    """Register the form submission callback for creating a new organization."""

    @app.callback(
        Output("new-org-status", "children"),
        Input("new-org-submit-btn", "n_clicks"),
        State("new-org-name", "value"),
        State("new-org-admin-firstname", "value"),
        State("new-org-admin-lastname", "value"),
        State("new-org-admin-username", "value"),
        State("new-org-admin-email", "value"),
        State("new-org-admin-password", "value"),
        prevent_initial_call=True,
    )
    def create_organization(n_clicks, org_name, first_name, last_name, username, email, password):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        # ── Validation ──
        if not org_name or not org_name.strip():
            return html.Span("Organization name is required.",
                             style={"color": "#ff6b6b", "fontSize": "13px"})
        if not username or not username.strip():
            return html.Span("Admin username is required.",
                             style={"color": "#ff6b6b", "fontSize": "13px"})
        if not email or not email.strip():
            return html.Span("Admin email is required.",
                             style={"color": "#ff6b6b", "fontSize": "13px"})
        if not password or len(password) < 8:
            return html.Span("Password must be at least 8 characters.",
                             style={"color": "#ff6b6b", "fontSize": "13px"})
        if not first_name or not first_name.strip():
            return html.Span("First name is required.",
                             style={"color": "#ff6b6b", "fontSize": "13px"})
        if not last_name or not last_name.strip():
            return html.Span("Last name is required.",
                             style={"color": "#ff6b6b", "fontSize": "13px"})

        if not supabase:
            return html.Span("Database not connected.",
                             style={"color": "#ff6b6b", "fontSize": "13px"})

        try:
            # ── Step 1: Create the organization ──
            org_resp = supabase.table("organizations").insert({
                "name": org_name.strip(),
            }).execute()

            if not org_resp.data:
                return html.Span("Failed to create organization.",
                                 style={"color": "#ff6b6b", "fontSize": "13px"})

            new_org_id = org_resp.data[0]["id"]

            # ── Step 2: Create admin user via Supabase Auth + profile insert ──
            try:
                # Use the admin client for auth user creation
                sb = supabase_admin if supabase_admin else supabase

                # Create auth user
                auth_resp = sb.auth.admin.create_user({
                    "email": email.strip(),
                    "password": password,
                    "email_confirm": True,
                })
                user_id = auth_resp.user.id

                # Insert profile into users table
                hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                supabase.table("users").insert({
                    "id": user_id,
                    "username": username.strip(),
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "email_address": email.strip(),
                    "role": "admin",
                    "status": "active",
                    "organization_id": new_org_id,
                    "password_hash": hashed_pw,
                    "created_at": "now()",
                }).execute()

            except Exception as user_err:
                print(f"[ERROR] Admin user creation: {user_err}")
                return html.Span(
                    f"Organization '{org_name}' created, but admin user failed: {str(user_err)[:80]}",
                    style={"color": "#ffd93d", "fontSize": "13px"}
                )

            # ── Success ──
            return html.Div(children=[
                html.Span("✓ ", style={"color": "#4aff9e", "fontWeight": "700"}),
                html.Span(f"Organization '{org_name}' created successfully!", style={"color": "#4aff9e", "fontSize": "13px"}),
                html.Br(),
                html.Span(f"Admin account: {username.strip()} (role: admin)", style={"color": "rgba(168,212,255,0.7)", "fontSize": "12px"}),
            ])

        except Exception as e:
            print(f"[ERROR] Create org: {e}")
            error_msg = str(e)
            if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
                return html.Span("Organization name or username already exists.",
                                 style={"color": "#ff6b6b", "fontSize": "13px"})
            return html.Span(f"Error: {error_msg[:100]}",
                             style={"color": "#ff6b6b", "fontSize": "13px"})

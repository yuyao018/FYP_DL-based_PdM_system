import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dashboard import create_dashboard_layout
from login_page import create_login_layout, USER_ICON, ADMIN_ICON, PERSON_ICON, LOCK_ICON, GEAR_SVG, feature_icon
from dev_login_page import create_dev_login_layout
from dev_dashboard import create_dev_dashboard_layout
from dev_new_organization import create_new_organization_layout, register_new_organization_callbacks
from overview import create_overview_layout, register_overview_callbacks
from sensor_trends import create_sensor_trends_layout, register_sensor_callbacks
from alert_log import create_alert_log_layout, register_alert_log_callbacks
from user_management import create_user_management_layout, register_user_management_callbacks
from add_user import create_add_user_layout, register_add_user_callbacks
from model_upload import create_model_upload_layout, register_model_upload_callbacks
from alert_thresholds import create_alert_thresholds_layout, register_alert_thresholds_callbacks
from engine_management import create_engine_management_layout, register_engine_management_callbacks
from add_engine import create_add_engine_layout, register_add_engine_callbacks
from degradation_analysis import create_degradation_analysis_layout, register_degradation_analysis_callbacks
from change_password import create_change_password_layout, register_change_password_callbacks
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client (with fallback for development without credentials)
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
SUPABASE_ADMIN_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client | None = None

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY)
# if SUPABASE_URL and SUPABASE_KEY:
#     try:
#         supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
#         print("[OK] Successfully connected to Supabase!")
#     except Exception as e:
#         print(f"[WARN] Error connecting to Supabase: {e}")
#         print("   Note: Make sure your .env file is set up correctly!")
# else:
#     print("[WARN] Supabase credentials not found in .env file")
#     print("   The app will run, but login will be disabled until you add SUPABASE_URL and SUPABASE_KEY to .env")

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server  # Expose Flask server for deployment
register_sensor_callbacks(app)
register_alert_log_callbacks(app, supabase=supabase)
register_user_management_callbacks(app, supabase=supabase)
register_add_user_callbacks(app, supabase=supabase)
register_model_upload_callbacks(app, supabase=supabase)
register_alert_thresholds_callbacks(app, supabase=supabase)
register_engine_management_callbacks(app, supabase=supabase_admin)
register_add_engine_callbacks(app, supabase=supabase)
register_overview_callbacks(app, supabase=supabase)
register_degradation_analysis_callbacks(app, supabase=supabase)
register_new_organization_callbacks(app, supabase=supabase, supabase_admin=supabase_admin)
register_change_password_callbacks(app, supabase=supabase, supabase_admin=supabase_admin)

# Resume simulations for any engines that already have data on disk
from engine_simulation_manager import resume_all_simulations
resume_all_simulations(supabase)

# Start email notification manager (daily report + threshold alerts)
from email_notifications import start_notification_manager
start_notification_manager(supabase)

# Main app layout with routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='sidebar-state', data=True),  # True = open by default
    dcc.Store(id='session-store', data=None, storage_type='session'),
    html.Div(id='page-content')
])

# Routing callback
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    State("session-store", "data"),
)
def display_page(pathname, session):
    if not pathname or pathname == "/":
        return create_login_layout()

    if pathname == "/dev-login":
        return create_dev_login_layout()

    if pathname == "/change-password":
        return create_change_password_layout()

    # ── Force password change: block all other routes if session has must_change_password ──
    if (session or {}).get("must_change_password"):
        return create_change_password_layout()

    if pathname == "/dev-dashboard":
        return create_dev_dashboard_layout(supabase)

    if pathname == "/dev-new-organization":
        return create_new_organization_layout()

    # Extract role and org_id from session
    user_role = (session or {}).get("role", "") or ""
    org_id = (session or {}).get("organization_id", "") or None

    # ── Developer role guard: redirect /dashboard → /dev-dashboard ──
    if pathname == "/dashboard" and user_role == "developer":
        return create_dev_dashboard_layout(supabase)

    # ── Engine-specific pages ──
    if pathname.startswith("/overview/"):
        engine_db_id = pathname.split("/")[-1]
        return create_overview_layout(supabase, engine_db_id=engine_db_id)

    if pathname.startswith("/sensor-trends/"):
        engine_db_id = pathname.split("/")[-1]
        return create_sensor_trends_layout(supabase, engine_db_id=engine_db_id)

    if pathname.startswith("/alert-log/"):
        engine_db_id = pathname.split("/")[-1]
        return create_alert_log_layout(supabase, engine_db_id=engine_db_id)

    if pathname.startswith("/degradation-analysis/"):
        engine_db_id = pathname.split("/")[-1]
        return create_degradation_analysis_layout(supabase, engine_db_id=engine_db_id)

    # ── Exact routes ──
    routes = {
        "/dashboard":         lambda: create_dashboard_layout(supabase, org_id=org_id),
        "/overview":          lambda: create_overview_layout(supabase),
        "/sensor-trends":     lambda: create_sensor_trends_layout(supabase),
        "/alert-log":         lambda: create_alert_log_layout(supabase),
        "/degradation-analysis": lambda: create_degradation_analysis_layout(supabase),
        "/engine-management": lambda: create_engine_management_layout(supabase, org_id=org_id),
        "/add-engine":        lambda: create_add_engine_layout(supabase, org_id=org_id),
        "/user-management":   lambda: create_user_management_layout(supabase),
        "/add-user":          lambda: create_add_user_layout(supabase),
        "/alert-thresholds":  lambda: create_alert_thresholds_layout(supabase),
    }

    # ── Developer-only routes ──
    if pathname == "/model-upload":
        if user_role != "developer":
            return html.Div(
                style={"minHeight": "100vh", "background": "#0a1628", "display": "flex",
                       "alignItems": "center", "justifyContent": "center", "flexDirection": "column"},
                children=[
                    html.H1("403", style={"color": "#ff4d4d", "fontSize": "72px", "fontWeight": "800", "margin": "0"}),
                    html.P("Access Denied", style={"color": "#a8d4ff", "fontSize": "18px"}),
                    html.P("Only developers can access this page.", style={"color": "rgba(168,212,255,0.6)", "fontSize": "14px"}),
                    dcc.Link("← Back to Dashboard", href="/dashboard",
                             style={"color": "#4a9eff", "textDecoration": "none", "marginTop": "12px"}),
                ]
            )
        return create_model_upload_layout(supabase, role=user_role)

    if pathname in routes:
        return routes[pathname]()

    # ── 404 fallback ──
    return html.Div(
        style={"minHeight": "100vh", "background": "#0a1628", "display": "flex",
               "alignItems": "center", "justifyContent": "center", "flexDirection": "column"},
        children=[
            html.H1("404", style={"color": "#4a9eff", "fontSize": "72px", "fontWeight": "800", "margin": "0"}),
            html.P("Page not found", style={"color": "#a8d4ff", "fontSize": "18px"}),
            dcc.Link("← Back to Dashboard", href="/dashboard",
                     style={"color": "#4a9eff", "textDecoration": "none", "marginTop": "12px"}),
        ]
    )

# Sidebar toggle callback
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
        "flexShrink": "0",
        "minHeight": "100vh",
        "background": "#0d1e3a",
        "borderRight": "1px solid rgba(74,158,255,0.15)",
        "display": "flex",
        "flexDirection": "column",
        "padding": "0",
        "overflow": "hidden",
        "transition": "width 0.3s ease",
    }

    if is_open:
        return {**base, "width": "210px"}, True
    else:
        return {**base, "width": "0px"}, False

# Login callback
@app.callback(
    Output("url", "pathname"),
    Output("login-status", "children"),
    Output("session-store", "data"),
    Input("signin-btn", "n_clicks"),
    State("username-input", "value"),
    State("password-input", "value"),
    State("login-role-store", "data"),
    prevent_initial_call=True,
)
def handle_login(n_clicks, username, password, selected_role):
    print(f"[DEBUG] Login attempt: username={username}, selected_role={selected_role}")

    if not username or not password:
        return dash.no_update, html.Span("Please enter your credentials.",
                              style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

    if not supabase:
        return dash.no_update, html.Span("Supabase not connected. Check your .env file.",
                              style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

    try:
        # Step 1: Check if user exists and has password_hash set
        print(f"[DEBUG-V2] Checking users table for {username}...")
        user_check = supabase.table("users") \
            .select("id, username, role, password_hash, email_address, organization_id, first_name, last_name, last_login_at") \
            .eq("username", username) \
            .execute()

        if not user_check.data:
            print(f"[DEBUG-V2] User '{username}' not found in users table")
            return dash.no_update, html.Span("Invalid username or password.",
                                  style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        user_row = user_check.data[0]
        print(f"[DEBUG-V2] Found user. password_hash is {'SET' if user_row.get('password_hash') else 'NULL'}")

        if user_row.get("password_hash") is None:
            # password_hash is NULL — verify via Supabase Auth and backfill
            print(f"[DEBUG] password_hash is NULL for {username}, trying Supabase Auth...")
            email = user_row.get("email_address")
            if not email:
                return dash.no_update, html.Span("Invalid username or password.",
                                      style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update
            try:
                auth_resp = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })
                if not auth_resp or not auth_resp.user:
                    return dash.no_update, html.Span("Invalid username or password.",
                                          style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

                # Auth succeeded — backfill password_hash
                import bcrypt as _bcrypt
                hashed = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
                supabase.table("users") \
                    .update({"password_hash": hashed}) \
                    .eq("username", username) \
                    .execute()
                print(f"[OK] Backfilled password_hash for {username}")

            except Exception as auth_e:
                print(f"[DEBUG] Supabase Auth sign-in failed: {auth_e}")
                return dash.no_update, html.Span("Invalid username or password.",
                                      style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update
        else:
            # password_hash exists — verify with bcrypt in Python
            import bcrypt as _bcrypt
            stored_hash = user_row.get("password_hash")
            try:
                password_valid = _bcrypt.checkpw(
                    password.encode("utf-8"),
                    stored_hash.encode("utf-8")
                )
            except Exception as hash_err:
                print(f"[DEBUG-V2] bcrypt.checkpw failed: {hash_err}")
                # Fallback to RPC for non-bcrypt hashes (e.g., pgcrypto $2a$06$)
                resp = supabase.rpc("verify_login", {
                    "p_username": username,
                    "p_password": password,
                }).execute()
                password_valid = bool(resp.data)

            print(f"[DEBUG-V2] Password valid: {password_valid}")

            if not password_valid:
                return dash.no_update, html.Span("Invalid username or password.",
                                      style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        # Step 2: User is verified — proceed with login
        user_profile = user_row
        user_id = str(user_profile.get("id", ""))
        organization_id = str(user_profile.get("organization_id", "") or "")
        actual_role = user_profile.get("role", "user")
        is_first_login = user_profile.get("last_login_at") is None

        print(f"[DEBUG] User profile: role={actual_role}, selected={selected_role}, is_first_login={is_first_login}")

        # Step 3: Validate selected role matches the user's actual role
        selected = (selected_role or "user").lower()
        if actual_role != selected:
            print(f"[DEBUG] Role mismatch: actual={actual_role}, selected={selected}")
            return dash.no_update, html.Span(
                f"Access denied. Your account is not registered as {'an admin' if selected == 'admin' else 'a user'}.",
                style={"color": "#ff6b6b", "fontSize": "13px"}
            ), dash.no_update

        # Step 4: Update last_login_at
        supabase.table("users") \
            .update({"last_login_at": "now()"}) \
            .eq("username", username) \
            .execute()

        # Step 5: Build session data
        session_data = {
            "user_id":         user_id,
            "username":        user_profile.get("username", username),
            "first_name":      user_profile.get("first_name", ""),
            "last_name":       user_profile.get("last_name", ""),
            "role":            actual_role,
            "organization_id": organization_id,
        }

        # Step 6: Redirect to password change if first login
        if is_first_login:
            session_data["must_change_password"] = True
            print(f"[OK] First login: {username} — redirecting to change password")
            return "/change-password", html.Span("Please update your password.",
                                                 style={"color": "#4a9eff", "fontSize": "13px"}), session_data

        print(f"[OK] Login: {username} | role: {actual_role} | user_id: {user_id} | org_id: {organization_id}")
        return "/dashboard", html.Span("Login successful!",
                                       style={"color": "#4aff9e", "fontSize": "13px"}), session_data

    except Exception as e:
        print(f"[ERROR] Login: {e}")
        return dash.no_update, html.Span("Login failed. Please try again.",
                              style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

# Logout callback
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("session-store", "data", allow_duplicate=True),
    Input("logout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def handle_logout(n_clicks):
    if not n_clicks or n_clicks == 0:
        raise dash.exceptions.PreventUpdate
    print("[OK] User logged out (session cleared)")
    # Clear session and redirect to login
    # NOTE: Do NOT call supabase.auth.sign_out() here — it would invalidate
    # the shared server-side client's auth state, breaking login for everyone.
    return "/", None

# Role toggle callback
@app.callback(
    Output("role-user", "style"),
    Output("role-admin", "style"),
    Output("login-role-store", "data"),
    Input("role-user", "n_clicks"),
    Input("role-admin", "n_clicks"),
)
def toggle_role(user_clicks, admin_clicks):
    ctx = callback_context
    active_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else "role-user"
    if not ctx.triggered:
        active_id = "role-user"

    base = {
        "flex": "1", "padding": "22px 16px", "borderRadius": "10px",
        "cursor": "pointer", "display": "flex", "flexDirection": "column",
        "alignItems": "center", "transition": "all 0.2s",
    }
    active_style = {**base,
        "border": "2px solid #4a9eff", "background": "rgba(74,158,255,0.12)"}
    inactive_style = {**base,
        "border": "2px solid rgba(74,158,255,0.2)", "background": "rgba(74,158,255,0.04)"}

    if active_id == "role-admin":
        return inactive_style, active_style, "admin"
    return active_style, inactive_style, "user"


# Developer login callback
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("dev-login-status", "children"),
    Output("session-store", "data", allow_duplicate=True),
    Input("dev-signin-btn", "n_clicks"),
    State("dev-username-input", "value"),
    State("dev-password-input", "value"),
    prevent_initial_call=True,
)
def handle_dev_login(n_clicks, username, password):
    if not username or not password:
        return dash.no_update, html.Span("Please enter your credentials.",
                              style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

    if not supabase:
        return dash.no_update, html.Span("Supabase not connected. Check your .env file.",
                              style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

    try:
        # Verify credentials via RPC
        resp = supabase.rpc("verify_login", {
            "p_username": username,
            "p_password": password,
        }).execute()

        if not resp.data:
            return dash.no_update, html.Span("Invalid username or password.",
                                  style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        # Fetch user profile
        user_resp = supabase.table("users") \
            .select("id, username, first_name, last_name, role, organization_id, last_login_at") \
            .eq("username", username) \
            .single() \
            .execute()

        user_profile = user_resp.data or {}
        role = user_profile.get("role", "")

        # Verify this is a developer account
        if role != "developer":
            return dash.no_update, html.Span("Access denied. Developer account required.",
                                  style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        is_first_login = user_profile.get("last_login_at") is None

        # Update last_login_at
        supabase.table("users") \
            .update({"last_login_at": "now()"}) \
            .eq("username", username) \
            .execute()

        # Build session data
        session_data = {
            "user_id": str(user_profile.get("id", "")),
            "username": user_profile.get("username", username),
            "first_name": user_profile.get("first_name", ""),
            "last_name": user_profile.get("last_name", ""),
            "role": "developer",
            "organization_id": str(user_profile.get("organization_id", "") or ""),
        }

        # Redirect to password change if first login
        if is_first_login:
            session_data["must_change_password"] = True
            print(f"[OK] First dev login: {username} — redirecting to change password")
            return "/change-password", html.Span("Please update your password.",
                                                 style={"color": "#4a9eff", "fontSize": "13px"}), session_data

        print(f"[OK] Dev Login: {username}")
        return "/dev-dashboard", html.Span("Login successful!",
                                       style={"color": "#4aff9e", "fontSize": "13px"}), session_data

    except Exception as e:
        print(f"[ERROR] Dev Login: {e}")
        return dash.no_update, html.Span("Login failed. Please try again.",
                              style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update


# Developer logout callback
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("session-store", "data", allow_duplicate=True),
    Input("dev-logout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def handle_dev_logout(n_clicks):
    if not n_clicks or n_clicks == 0:
        raise dash.exceptions.PreventUpdate
    return "/dev-login", None


@app.callback(
    Output("engines-grid", "children"),
    Output("filter-all",      "style"),
    Output("filter-healthy",  "style"),
    Output("filter-degrading","style"),
    Output("filter-critical", "style"),
    Input("filter-all",       "n_clicks"),
    Input("filter-healthy",   "n_clicks"),
    Input("filter-degrading", "n_clicks"),
    Input("filter-critical",  "n_clicks"),
    State("engine-data-store","data"),
    prevent_initial_call=True,
)
def filter_engines(all_clicks, healthy_clicks, degrading_clicks, critical_clicks, engine_data):
    ctx = callback_context
    if not ctx.triggered or not engine_data:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    active_style = {
        "background": "#007bff", "border": "none", "color": "white",
        "padding": "6px 14px", "borderRadius": "20px", "fontSize": "12px",
        "fontWeight": "700", "cursor": "pointer",
    }
    inactive_style = {
        "background": "rgba(74,158,255,0.15)", "border": "1px solid rgba(74,158,255,0.4)",
        "color": "#a8d4ff", "padding": "6px 14px", "borderRadius": "20px",
        "fontSize": "12px", "fontWeight": "700", "cursor": "pointer",
    }

    filter_map = {
        "filter-all":      None,
        "filter-healthy":  "healthy",
        "filter-degrading":"warning",
        "filter-critical": "critical",
    }

    selected = filter_map.get(trigger)

    # Filter engine data
    filtered = (
        engine_data if selected is None
        else [e for e in engine_data if e["status"] == selected]
    )

    status_colors = {
        "healthy": {"bg": "rgba(0,255,100,0.15)", "border": "#00ff64", "text": "#00ff64"},
        "warning": {"bg": "rgba(255,217,61,0.15)", "border": "#ffd93d", "text": "#ffd93d"},
        "critical": {"bg": "rgba(255,77,77,0.15)", "border": "#ff4d4d", "text": "#ff4d4d"},
    }

    from dashboard import gear_icon  # import here to avoid circular imports

    def engine_card(engine):
        colors = status_colors[engine["status"]]
        return html.Div(
            dcc.Link(
                href=f"/overview/{engine['db_id']}",
                style={"textDecoration": "none"},
                children=[html.Div(
                    style={
                        "background": "#101a2f",
                        "border": "1px solid rgba(74,158,255,0.2)",
                        "borderRadius": "12px", "padding": "16px",
                        "display": "flex", "flexDirection": "column",
                        "gap": "8px", "cursor": "pointer",
                    },
                    children=[
                        html.Div(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
                                 children=[
                                     html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                              children=[gear_icon(),
                                                        html.Span(f"# ENGINE-{engine['id']}",
                                                                  style={"color": "white", "fontWeight": "700", "fontSize": "14px"})]),
                                     html.Span(engine["status"].upper(), style={
                                         "background": colors["bg"], "color": colors["text"],
                                         "border": f"1px solid {colors['border']}",
                                         "borderRadius": "8px", "padding": "4px 10px",
                                         "fontSize": "10px", "fontWeight": "700",
                                     }),
                                 ]),
                        html.Div(style={"display": "flex", "justifyContent": "space-between"},
                                 children=[
                                     html.Span("Model", style={"color": "rgba(180,210,255,0.7)", "fontSize": "12px"}),
                                     html.Span(engine.get("model_type", "N/A"), style={"color": "rgba(200,220,255,0.9)", "fontWeight": "700", "fontSize": "14px"}),
                                 ]),
                        html.Div(style={"display": "flex", "justifyContent": "space-between"},
                                 children=[
                                     html.Span("Created", style={"color": "rgba(180,210,255,0.7)", "fontSize": "12px"}),
                                     html.Span(engine.get("created_at", "N/A"), style={"color": "rgba(200,220,255,0.9)", "fontWeight": "600", "fontSize": "11px"}),
                                 ]),
                        html.Div(style={"display": "flex", "justifyContent": "space-between"},
                                 children=[
                                     html.Span("Predicted cycles left", style={"color": "rgba(74,158,255,0.7)", "fontSize": "11px"}),
                                     html.Span(f"{engine['rul']}", style={"color": "#4a9eff", "fontWeight": "700", "fontSize": "14px"}),
                                 ]),
                        html.Div(style={"borderTop": "1px solid rgba(74,158,255,0.15)", "paddingTop": "8px",
                                        "display": "flex", "justifyContent": "flex-end", "gap": "4px"},
                                 children=[
                                     html.Span("View details", style={"color": "rgba(74,158,255,0.6)", "fontSize": "11px"}),
                                     html.Span("→", style={"color": "rgba(74,158,255,0.6)", "fontSize": "11px"}),
                                 ]),
                    ]
                )]
            )
        )

    cards = [engine_card(e) for e in filtered] if filtered else [
        html.Div(f"No {selected or 'engine'} found.",
                 style={"color": "rgba(255,255,255,0.5)", "textAlign": "center",
                        "padding": "40px 0", "gridColumn": "1 / -1", "fontSize": "14px"})
    ]

    # Button styles — highlight whichever is active
    styles = [
        active_style if trigger == f"filter-{k}" else inactive_style
        for k in ["all", "healthy", "degrading", "critical"]
    ]

    return cards, *styles


# Developer dashboard: filter organizations by search/dropdown
@app.callback(
    Output("dev-org-list", "children"),
    Input("dev-org-search", "value"),
    Input("dev-org-filter", "value"),
    State("dev-org-data-store", "data"),
    prevent_initial_call=True,
)
def filter_dev_orgs(search_value, filter_value, org_data):
    if not org_data:
        raise dash.exceptions.PreventUpdate

    from dev_dashboard import gear_icon, org_icon

    filtered = org_data

    # Apply dropdown filter
    if filter_value and filter_value != "all":
        filtered = [o for o in filtered if o["id"] == filter_value]

    # Apply search filter
    if search_value:
        search_lower = search_value.lower().strip()
        filtered = [o for o in filtered if search_lower in o["name"].lower()]

    status_colors = {
        "healthy": {"bg": "rgba(0, 255, 100, 0.15)", "border": "#00ff64", "text": "#00ff64"},
        "warning": {"bg": "rgba(255, 217, 61, 0.15)", "border": "#ffd93d", "text": "#ffd93d"},
        "critical": {"bg": "rgba(255, 77, 77, 0.15)", "border": "#ff4d4d", "text": "#ff4d4d"},
    }

    def engine_card(engine):
        colors = status_colors[engine["status"]]
        return html.Div(
            style={"minWidth": "220px", "maxWidth": "240px", "flexShrink": "0"},
            children=[
                dcc.Link(
                    href=f"/overview/{engine['db_id']}",
                    style={"textDecoration": "none"},
                    children=[
                        html.Div(
                            style={
                                "background": "#101a2f",
                                "border": "1px solid rgba(74,158,255,0.2)",
                                "borderRadius": "12px", "padding": "14px",
                                "display": "flex", "flexDirection": "column",
                                "gap": "6px", "cursor": "pointer",
                            },
                            children=[
                                html.Div(
                                    style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
                                    children=[
                                        html.Div(style={"display": "flex", "alignItems": "center", "gap": "6px"},
                                                 children=[gear_icon(), html.Span(f"ENGINE-{engine['id']}", style={"color": "white", "fontWeight": "700", "fontSize": "13px"})]),
                                        html.Span(engine["status"].upper(), style={
                                            "background": colors["bg"], "color": colors["text"],
                                            "border": f"1px solid {colors['border']}",
                                            "borderRadius": "8px", "padding": "3px 8px",
                                            "fontSize": "9px", "fontWeight": "700",
                                        }),
                                    ]
                                ),
                                html.Div(style={"display": "flex", "justifyContent": "space-between"},
                                         children=[
                                             html.Span("Model", style={"color": "rgba(180,210,255,0.7)", "fontSize": "11px"}),
                                             html.Span(engine.get("model_type", "N/A"), style={"color": "rgba(200,220,255,0.9)", "fontWeight": "700", "fontSize": "13px"}),
                                         ]),
                                html.Div(style={"display": "flex", "justifyContent": "space-between"},
                                         children=[
                                             html.Span("Created", style={"color": "rgba(180,210,255,0.7)", "fontSize": "11px"}),
                                             html.Span(engine.get("created_at", "N/A"), style={"color": "rgba(200,220,255,0.9)", "fontWeight": "600", "fontSize": "11px"}),
                                         ]),
                                html.Div(style={"display": "flex", "justifyContent": "space-between"},
                                         children=[
                                             html.Span("Cycles left", style={"color": "rgba(74,158,255,0.7)", "fontSize": "11px"}),
                                             html.Span(f"{engine['rul']}", style={"color": "#4a9eff", "fontWeight": "700", "fontSize": "13px"}),
                                         ]),
                            ]
                        )
                    ]
                )
            ]
        )

    def org_row(org):
        return html.Div(
            style={
                "background": "#0d1e3a",
                "border": "1px solid rgba(74,158,255,0.2)",
                "borderRadius": "14px",
                "padding": "20px",
                "marginBottom": "20px",
            },
            children=[
                html.Div(
                    style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "14px"},
                    children=[
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "gap": "10px"},
                            children=[org_icon(), html.Span(org["name"], style={"color": "white", "fontWeight": "700", "fontSize": "17px"})]
                        ),
                        html.Div(style={"display": "flex", "alignItems": "center", "gap": "16px"}, children=[
                            html.Span(f"{org.get('user_count', 0)} user{'s' if org.get('user_count', 0) != 1 else ''}", style={"color": "rgba(168,212,255,0.7)", "fontSize": "13px", "fontWeight": "600"}),
                            html.Span(f"{org['engine_count']} engine{'s' if org['engine_count'] != 1 else ''}", style={"color": "rgba(168,212,255,0.7)", "fontSize": "13px", "fontWeight": "600"}),
                        ]),
                    ]
                ),
                html.Div(
                    style={"display": "flex", "gap": "14px", "overflowX": "auto", "paddingBottom": "8px"},
                    children=[engine_card(e) for e in org["engines"]] if org.get("engines") else [
                        html.Div("No engines registered.", style={"color": "rgba(255,255,255,0.5)", "fontSize": "13px", "padding": "10px 0"})
                    ]
                ),
            ]
        )

    if filtered:
        return [org_row(o) for o in filtered]
    else:
        return [html.Div("No organizations found.", style={
            "color": "rgba(255,255,255,0.5)", "fontSize": "14px",
            "textAlign": "center", "padding": "40px 0",
        })]


if __name__ == "__main__":
    app.run(debug=False, port=8050)

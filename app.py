from assets import database_integration as db
import dash
from simulation_panel import build_simulation_panel, register_simulation_callbacks
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dashboard import create_dashboard_layout
from login_page import create_login_layout, USER_ICON, ADMIN_ICON, PERSON_ICON, LOCK_ICON, GEAR_SVG, feature_icon
from login_page import validate_login_inputs
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
from schedule_maintenance import create_schedule_maintenance_layout, register_schedule_maintenance_callbacks
from change_password import create_change_password_layout, register_change_password_callbacks
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from flask import session as flask_session
from auth_security import (RequestSupabaseProxy, authenticate_username,
                           configure_flask_session, refresh_auth_session_if_needed,
                           revoke_auth_session, trusted_profile, LoginRejected)

# Load environment variables
load_dotenv()

# Initialize Supabase client 
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
SUPABASE_ADMIN_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client | None = None

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
supabase_admin = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY) if SUPABASE_URL and SUPABASE_ADMIN_KEY else None
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
configure_flask_session(server)
server.before_request(refresh_auth_session_if_needed)
request_supabase = RequestSupabaseProxy()
from maintenance_recommendations import register_response_routes
register_response_routes(server, supabase_admin)
register_sensor_callbacks(app, supabase=request_supabase)
register_alert_log_callbacks(app, supabase=request_supabase)
register_user_management_callbacks(app, supabase=request_supabase)
register_add_user_callbacks(app, supabase=request_supabase, supabase_admin=supabase_admin)
register_model_upload_callbacks(app, supabase=request_supabase, supabase_admin=supabase_admin)
register_alert_thresholds_callbacks(app, supabase=request_supabase)
register_engine_management_callbacks(app, supabase=request_supabase)
register_add_engine_callbacks(app, supabase=request_supabase)
register_overview_callbacks(app, supabase=request_supabase)
register_simulation_callbacks(app, supabase=request_supabase)
register_degradation_analysis_callbacks(app, supabase=request_supabase)
register_new_organization_callbacks(app, supabase=request_supabase, supabase_admin=supabase_admin)
register_change_password_callbacks(app, supabase=request_supabase, supabase_admin=supabase_admin)
register_schedule_maintenance_callbacks(app, supabase=request_supabase)

# Resume simulations for any engines that already have data on disk
from engine_simulation_manager import resume_all_simulations
resume_all_simulations(supabase_admin)

# Start email notification manager (daily report + threshold alerts)
from email_notifications import start_notification_manager
start_notification_manager(supabase_admin)

# Main app layout with routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='sidebar-state', data=True),  # True = open by default
    dcc.Store(id='session-store', data=None, storage_type='session'),
    dcc.Store(id='toast-store', data=None, storage_type='session'),  # success message for toast
    # Global toast notification
    html.Div(
        id='global-toast',
        style={
            "position": "fixed", "top": "-60px", "left": "50%",
            "transform": "translateX(-50%)", "zIndex": "9999",
            "background": "linear-gradient(135deg, #1a6fd4, #00c875)",
            "color": "white", "padding": "14px 28px",
            "borderRadius": "10px", "fontSize": "14px", "fontWeight": "700",
            "boxShadow": "0 4px 20px rgba(0,200,100,0.3)",
            "transition": "top 0.4s ease",
            "whiteSpace": "nowrap",
        },
    ),
    dcc.Loading(
        id="page-navigation-loading",
        target_components={"page-content": "children"},
        type=None,
        fullscreen=True,
        delay_show=150,
        overlay_style={
            "backgroundColor": "#0a1628",
            "visibility": "visible",
            "opacity": "1",
        },
        custom_spinner=html.Div(
            html.Div(className="page-loading-spinner"),
            className="page-loading-screen",
            role="status",
            **{"aria-label": "Loading page"},
        ),
        children=html.Div(id="page-content"),
    ),
    build_simulation_panel(),
])

# Routing callback
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("url", "search"),
    State("session-store", "data"),
)
def display_page(pathname, search, session):
    # dcc.Store is client-editable. Route access uses the signed Flask session.
    session = trusted_profile()
    if not pathname or pathname == "/":
        # Parse ?next= query param for deep-link after login
        next_url = ""
        if search:
            from urllib.parse import parse_qs, urlparse
            qs = parse_qs(search.lstrip("?"))
            next_url = qs.get("next", [""])[0]
        return create_login_layout(next_url=next_url)

    if pathname == "/dev-login":
        return create_dev_login_layout()

    # Check the browser session before constructing any protected page.
    if not session:
        return create_login_layout(next_url=pathname)

    user_role = (session or {}).get("role", "") or ""
    admin_routes = ("/user-management", "/add-user", "/engine-management",
                    "/add-engine", "/alert-thresholds")
    admin_page = pathname in admin_routes or pathname.startswith(("/edit-user/", "/edit-engine/"))
    developer_page = pathname in ("/dev-dashboard", "/dev-new-organization", "/model-upload")
    if ((admin_page and user_role != "admin")
            or (developer_page and user_role != "developer")):
        return html.Div([html.H1("403"), html.P("Access Denied"),
                         dcc.Link("Back to Dashboard", href="/dashboard")])

    if pathname == "/change-password":
        return create_change_password_layout()

    # ── Force password change: block all other routes if session has must_change_password ──
    if (session or {}).get("must_change_password"):
        return create_change_password_layout()

    if pathname == "/dev-dashboard":
        return create_dev_dashboard_layout(supabase_admin)

    if pathname == "/dev-new-organization":
        return create_new_organization_layout()

    # Extract role and org_id from session
    user_role = (session or {}).get("role", "") or ""
    org_id = (session or {}).get("organization_id", "") or None

    # Browser callbacks operate with the authenticated user's JWT; server-only
    # service-role access is kept in narrow privileged operations.
    sb = request_supabase

    # ── Developer role guard: redirect /dashboard → /dev-dashboard ──
    if pathname == "/dashboard" and user_role == "developer":
        return create_dev_dashboard_layout(supabase_admin)

    # ── Engine-specific pages ──
    if pathname.startswith("/overview/"):
        engine_db_id = pathname.split("/")[-1]
        return create_overview_layout(sb, engine_db_id=engine_db_id)

    if pathname.startswith("/sensor-trends/"):
        engine_db_id = pathname.split("/")[-1]
        return create_sensor_trends_layout(sb, engine_db_id=engine_db_id)

    if pathname.startswith("/alert-log/"):
        engine_db_id = pathname.split("/")[-1]
        return create_alert_log_layout(sb, engine_db_id=engine_db_id,
                                       org_id=org_id, role=user_role,
                                       user_id=(session or {}).get("user_id"),
                                       username=(session or {}).get("username"),
                                       first_name=(session or {}).get("first_name"),
                                       last_name=(session or {}).get("last_name"))

    if pathname.startswith("/degradation-analysis/"):
        engine_db_id = pathname.split("/")[-1]
        return create_degradation_analysis_layout(sb, engine_db_id=engine_db_id)

    if pathname.startswith("/schedule-maintenance/"):
        parts = pathname.strip("/").split("/")
        engine_db_id = parts[1]
        proposal = None
        if len(parts) == 4 and parts[2] == "recommendation":
            from maintenance_recommendations import read_proposal, prefill_layout
            try:
                proposal = read_proposal(parts[3])
                from scheduling_agent_service import authorized_engine
                authorized_engine(sb, engine_db_id, session)
                if (proposal["engine_id"] != engine_db_id
                        or proposal["organization_id"] != str(org_id)
                        or (user_role != "admin" and proposal["technician"] != str((session or {}).get("user_id")))):
                    return html.Div("This recommendation is not assigned to your account.")
            except Exception:
                return html.Div("This recommendation has expired. Please open My Schedule to create a booking.")
        layout = create_schedule_maintenance_layout(sb, engine_db_id=engine_db_id,
                                                  org_id=org_id, role=user_role,
                                                  user_id=(session or {}).get("user_id"))
        return prefill_layout(layout, proposal) if proposal else layout

    if pathname.startswith("/edit-user/"):
        user_id = pathname.split("/")[-1]
        return create_add_user_layout(sb, edit_user_id=user_id)

    if pathname.startswith("/edit-engine/"):
        engine_id = pathname.split("/")[-1]
        return create_add_engine_layout(sb, org_id=org_id, edit_engine_id=engine_id)

    # ── Exact routes ──
    routes = {
        "/dashboard":         lambda: create_dashboard_layout(sb, org_id=org_id, role=user_role, username=(session or {}).get("username"), first_name=(session or {}).get("first_name"), user_id=(session or {}).get("user_id")),
        "/overview":          lambda: create_overview_layout(sb),
        "/sensor-trends":     lambda: create_sensor_trends_layout(sb),
        "/alert-log":         lambda: create_alert_log_layout(sb, org_id=org_id, role=user_role,
                                                               user_id=(session or {}).get("user_id"),
                                                               username=(session or {}).get("username"),
                                                               first_name=(session or {}).get("first_name"),
                                                               last_name=(session or {}).get("last_name")),
        "/degradation-analysis": lambda: create_degradation_analysis_layout(sb),
        "/engine-management": lambda: create_engine_management_layout(sb, org_id=org_id),
        "/add-engine":        lambda: create_add_engine_layout(sb, org_id=org_id),
        "/user-management":   lambda: create_user_management_layout(sb, org_id=org_id),
        "/add-user":          lambda: create_add_user_layout(sb),
        "/alert-thresholds":  lambda: create_alert_thresholds_layout(sb),
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
        return create_model_upload_layout(request_supabase, role=user_role)

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

# Toast notification — clientside callback for smooth slide-in/out animation
app.clientside_callback(
    """
    function(data) {
        if (!data) {
            return window.dash_clientside.no_update;
        }
        var msg = data.split('|')[0];
        var el = document.getElementById('global-toast');
        if (el) {
            el.innerText = msg;
            el.style.top = '20px';
            setTimeout(function() { el.style.top = '-60px'; }, 2500);
        }
        return null;
    }
    """,
    Output("toast-store", "data"),
    Input("toast-store", "data"),
    prevent_initial_call=True,
)

# User menu toggle — click to open/close, click outside to close
app.clientside_callback(
    """
    function(n) {
        var menu = document.querySelector('.user-dropdown-menu');
        var trigger = document.getElementById('user-menu-trigger');
        if (!menu) return window.dash_clientside.no_update;

        var isOpen = menu.style.display === 'block';
        menu.style.display = isOpen ? 'none' : 'block';

        if (!isOpen) {
            function handleOutside(e) {
                if (trigger && !trigger.contains(e.target)) {
                    menu.style.display = 'none';
                    document.removeEventListener('click', handleOutside);
                }
            }
            setTimeout(function() {
                document.addEventListener('click', handleOutside);
            }, 0);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("user-menu-trigger", "id"),
    Input("user-menu-trigger", "n_clicks"),
    prevent_initial_call=True,
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
    if not n or n == 0:
        raise dash.exceptions.PreventUpdate

    is_open = not is_open

    base = {
        "flexShrink": "0",
        "height": "calc(100vh - 60px)",
        "maxHeight": "calc(100vh - 60px)",
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
    State("login-next-store", "data"),
    prevent_initial_call=True,
)
def handle_login(n_clicks, username, password, selected_role, next_url):
    validation_error = validate_login_inputs(username, password)
    if validation_error:
        return dash.no_update, html.Span(validation_error, style={"color": "#ff6b6b"}), dash.no_update
    try:
        if not all((supabase_admin, SUPABASE_URL, SUPABASE_KEY)):
            raise RuntimeError("Supabase Auth is not configured")
        profile = authenticate_username(username.strip(), password, selected_role,
                                        supabase_admin, SUPABASE_URL, SUPABASE_KEY)
        route = "/change-password" if profile["must_change_password"] else (
            "/dev-dashboard" if profile["role"] == "developer" else (next_url or "/dashboard"))
        message = "Please update your password." if profile["must_change_password"] else "Login successful!"
        return route, html.Span(message), {k: v for k, v in profile.items() if k != "must_change_password"}
    except LoginRejected as exc:
        return dash.no_update, html.Span(str(exc), style={"color": "#ff6b6b"}), dash.no_update
    except Exception as exc:
        print(f"[AUTH] Login rejected or unavailable ({type(exc).__name__})")
        return dash.no_update, html.Span("Sign-in is temporarily unavailable. Please try again.", style={"color": "#ff6b6b"}), dash.no_update

def mark_logged_out(session):
    """Mark the authenticated profile inactive, then clear its Auth session."""
    profile = trusted_profile()
    user_id = profile.get("user_id") if profile else None
    if not user_id or not supabase_admin:
        return
    try:
        db.update_records(supabase_admin, "users", {"status": "inactive"}, filters=[('eq', "id", user_id)])
    except Exception as exc:
        # A database outage must not prevent clearing the browser session.
        print(f"[WARN] Logout status update failed: {type(exc).__name__}")


# Logout callback
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("session-store", "data", allow_duplicate=True),
    Input("logout-btn", "n_clicks"),
    State("session-store", "data"),
    prevent_initial_call=True,
)
def handle_logout(n_clicks, session):
    if not n_clicks or n_clicks == 0:
        raise dash.exceptions.PreventUpdate
    mark_logged_out(session)
    revoke_auth_session()
    print("[OK] User logged out (session cleared)")
    # Clear session and redirect to login
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
        return dash.no_update, html.Span("Please enter your credentials.", style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update
    try:
        profile = authenticate_username(username.strip(), password, "developer",
                                        supabase_admin, SUPABASE_URL, SUPABASE_KEY)
        path = "/change-password" if profile["must_change_password"] else "/dev-dashboard"
        msg = "Please update your password." if profile["must_change_password"] else "Login successful!"
        return path, html.Span(msg), {k: v for k, v in profile.items() if k != "must_change_password"}
    except LoginRejected as exc:
        return dash.no_update, html.Span(str(exc), style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update
    except Exception as exc:
        print(f"[ERROR] Dev Login: {type(exc).__name__}")
        return dash.no_update, html.Span("Sign-in is temporarily unavailable. Please try again.",
                                          style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update


# Developer logout callback
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("session-store", "data", allow_duplicate=True),
    Input("dev-logout-btn", "n_clicks"),
    State("session-store", "data"),
    prevent_initial_call=True,
)
def handle_dev_logout(n_clicks, session):
    if not n_clicks or n_clicks == 0:
        raise dash.exceptions.PreventUpdate
    mark_logged_out(session)
    revoke_auth_session()
    return "/dev-login", None


@app.callback(
    Output("engines-grid", "children"),
    Output("dashboard-total-count", "children"),
    Output("dashboard-healthy-count", "children"),
    Output("dashboard-warning-count", "children"),
    Output("dashboard-critical-count", "children"),
    Input("engine-status-filter", "value"),
    Input("engine-scope-filter", "value"),
    State("engine-data-store", "data"),
    State("session-store", "data"),
    prevent_initial_call=True,
)
def filter_engines(status_filter, scope, engine_data, session):
    session = trusted_profile()
    if not session:
        raise dash.exceptions.PreventUpdate
    selected = status_filter if status_filter in ("healthy", "warning", "critical") else None
    engine_data = engine_data or []
    if scope != "all":
        user_id = session["user_id"]
        engine_data = [e for e in engine_data if user_id and str(e.get("responsible_by")) == str(user_id)]

    # Filter engine data
    filtered = (
        engine_data if selected is None
        else [e for e in engine_data if e["status"] == selected]
    )

    status_colors = {
        "unknown": {"bg": "rgba(168,212,255,0.1)", "border": "#a8d4ff", "text": "#a8d4ff"},
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
                                     html.Span(f"{engine['rul']}" if engine.get("has_prediction") else "Warming up…", style={"color": "#4a9eff", "fontWeight": "700", "fontSize": "14px"}),
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

    # Counts cover the ownership scope, independently of the status filter.
    return (
        cards,
        str(len(engine_data)),
        str(sum(e["status"] == "healthy" for e in engine_data)),
        str(sum(e["status"] == "warning" for e in engine_data)),
        str(sum(e["status"] == "critical" for e in engine_data)),
    )



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
                "padding": "20px 20px 12px 20px",
                "marginBottom": "20px",
                "minWidth": "0",
                "width": "100%",
                "boxSizing": "border-box",
                "overflow": "hidden",
            },
            children=[
                html.Div(
                    style={
                        "display": "flex", "alignItems": "center",
                        "justifyContent": "space-between",
                        "marginBottom": "12px",
                    },
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
                    className="engine-card-row",
                    style={
                        "display": "flex",
                        "flexWrap": "nowrap",
                        "gap": "14px",
                        "overflowX": "auto",
                        "overflowY": "hidden",
                        "paddingBottom": "8px",
                        "WebkitOverflowScrolling": "touch",
                    },
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
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host="0.0.0.0", port=port)

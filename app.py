import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dashboard import create_dashboard_layout
from login_page import create_login_layout, USER_ICON, ADMIN_ICON, PERSON_ICON, LOCK_ICON, GEAR_SVG, feature_icon
from overview import create_overview_layout, register_overview_callbacks
from sensor_trends import create_sensor_trends_layout, register_sensor_callbacks
from alert_log import create_alert_log_layout, register_alert_log_callbacks
from user_management import create_user_management_layout, register_user_management_callbacks
from add_user import create_add_user_layout, register_add_user_callbacks
from model_upload import create_model_upload_layout, register_model_upload_callbacks
from alert_thresholds import create_alert_thresholds_layout, register_alert_thresholds_callbacks
from engine_management import create_engine_management_layout, register_engine_management_callbacks
from add_engine import create_add_engine_layout, register_add_engine_callbacks
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
register_alert_log_callbacks(app)
register_user_management_callbacks(app, supabase=supabase)
register_add_user_callbacks(app, supabase=supabase)
register_model_upload_callbacks(app, supabase=supabase)
register_alert_thresholds_callbacks(app, supabase=supabase)
register_engine_management_callbacks(app, supabase=supabase)
register_add_engine_callbacks(app, supabase=supabase)
register_overview_callbacks(app, supabase=supabase)

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

    # Extract org_id from session (empty string if not logged in)
    org_id = (session or {}).get("organization_id", "") or None

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

    # ── Exact routes ──
    routes = {
        "/dashboard":         lambda: create_dashboard_layout(supabase, org_id=org_id),
        "/overview":          lambda: create_overview_layout(supabase),
        "/sensor-trends":     lambda: create_sensor_trends_layout(supabase),
        "/alert-log":         lambda: create_alert_log_layout(supabase),
        "/engine-management": lambda: create_engine_management_layout(supabase, org_id=org_id),
        "/add-engine":        lambda: create_add_engine_layout(supabase, org_id=org_id),
        "/user-management":   lambda: create_user_management_layout(supabase),
        "/add-user":          lambda: create_add_user_layout(supabase),
        "/model-upload":      lambda: create_model_upload_layout(supabase),
        "/alert-thresholds":  lambda: create_alert_thresholds_layout(supabase),
    }

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
    prevent_initial_call=True,
)
def handle_login(n_clicks, username, password):
    if not username or not password:
        return "/", html.Span("Please enter your credentials.",
                              style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

    if not supabase:
        return "/", html.Span("Supabase not connected. Check your .env file.",
                              style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

    try:
        # Step 1: Verify credentials via RPC
        resp = supabase.rpc("verify_login", {
            "p_username": username,
            "p_password": password,
        }).execute()

        if not resp.data:
            return "/", html.Span("Invalid username or password.",
                                  style={"color": "#ff6b6b", "fontSize": "13px"}), dash.no_update

        user = resp.data[0]

        # Step 2: Fetch user profile + organization_id from public.users
        user_resp = supabase.table("users") \
            .select("id, username, first_name, last_name, role, organization_id") \
            .eq("username", username) \
            .single() \
            .execute()

        user_profile = user_resp.data or {}
        user_id = str(user_profile.get("id", ""))
        organization_id = str(user_profile.get("organization_id", "") or "")

        # Step 3: Update last_login_at
        supabase.table("users") \
            .update({"last_login_at": "now()"}) \
            .eq("username", username) \
            .execute()

        # Step 4: Build session data
        session_data = {
            "user_id":         user_id,
            "username":        user_profile.get("username", username),
            "first_name":      user_profile.get("first_name", ""),
            "last_name":       user_profile.get("last_name", ""),
            "role":            user_profile.get("role", "operator"),
            "organization_id": organization_id,
        }

        print(f"[OK] Login: {username} | user_id: {user_id} | org_id: {organization_id}")
        return "/dashboard", html.Span("Login successful!",
                                       style={"color": "#4aff9e", "fontSize": "13px"}), session_data

    except Exception as e:
        print(f"[ERROR] Login: {e}")
        return "/", html.Span("Login failed. Please try again.",
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
    if supabase:
        try:
            supabase.auth.sign_out()
            print("[OK] User signed out")
        except Exception:
            pass
    # Clear session and redirect to login
    return "/", None

# Role toggle callback
@app.callback(
    Output("role-user", "style"),
    Output("role-admin", "style"),
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
        return inactive_style, active_style
    return active_style, inactive_style


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
                                     html.Span("Degradation", style={"color": "rgba(180,210,255,0.7)", "fontSize": "12px"}),
                                     html.Span(f"{engine['degradation']}%", style={"color": colors["text"], "fontWeight": "700", "fontSize": "14px"}),
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


if __name__ == "__main__":
    app.run(debug=False, port=8050)

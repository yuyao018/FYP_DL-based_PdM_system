import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dashboard import create_dashboard_layout
from login_page import create_login_layout, USER_ICON, ADMIN_ICON, PERSON_ICON, LOCK_ICON, GEAR_SVG, feature_icon
from overview import create_overview_layout
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client (with fallback for development without credentials)
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
supabase: Client | None = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Successfully connected to Supabase!")
    except Exception as e:
        print(f"[WARN] Error connecting to Supabase: {e}")
        print("   Note: Make sure your .env file is set up correctly!")
else:
    print("[WARN] Supabase credentials not found in .env file")
    print("   The app will run, but login will be disabled until you add SUPABASE_URL and SUPABASE_KEY to .env")

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server  # Expose Flask server for deployment

# Main app layout with routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='sidebar-state', data=True),
    html.Div(id='page-content')
])

# Routing callback
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def display_page(pathname):
    if pathname and pathname.startswith("/overview/"):
        engine_db_id = pathname.split("/")[-1]
        return create_overview_layout(supabase, engine_db_id=int(engine_db_id))
    elif pathname == "/dashboard":
        return create_dashboard_layout(supabase)
    else:
        return create_login_layout()

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
    if is_open:
        style = {
            "width": "210px",          # match overview.py's sidebar width
            "flexShrink": "0",
            "minHeight": "100vh",
            "background": "#0d1e3a",
            "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex",
            "flexDirection": "column",
            "overflow": "hidden",
            "transition": "width 0.3s",
        }
    else:
        style = {
            "width": "0px",
            "overflow": "hidden",
            "padding": "0",
            "transition": "width 0.3s",
        }
    return style, is_open

# Login callback
@app.callback(
    Output("url", "pathname"),
    Output("login-status", "children"),
    Input("signin-btn", "n_clicks"),
    State("username-input", "value"),
    State("password-input", "value"),
    prevent_initial_call=True,
)
def handle_login(n_clicks, username, password):
    if not username or not password:
        return "/", html.Span(
            "Please enter your credentials.",
            style={"color": "#ff6b6b", "fontSize": "13px"}
        )

    if not supabase:
        return "/", html.Span(
            "Supabase not connected. Check your .env file.",
            style={"color": "#ff6b6b", "fontSize": "13px"}
        )

    try:
        # Call RPC function to verify username + password
        resp = supabase.rpc("verify_login", {
            "p_username": username,
            "p_password": password,
        }).execute()

        if not resp.data:
            return "/", html.Span(
                "Invalid username or password.",
                style={"color": "#ff6b6b", "fontSize": "13px"}
            )

        user = resp.data[0]

        # Update last_login_at
        supabase.table("users") \
            .update({"last_login_at": "now()"}) \
            .eq("username", username) \
            .execute()

        print(f"[OK] Login: {user['username']} ({user['role']})")
        return "/dashboard", html.Span(
            "Login successful!",
            style={"color": "#4aff9e", "fontSize": "13px"}
        )

    except Exception as e:
        print(f"[ERROR] Login: {e}")
        return "/", html.Span(
            "Login failed. Please try again.",
            style={"color": "#ff6b6b", "fontSize": "13px"}
        )

# Logout callback
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("logout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def handle_logout(n_clicks):
    if supabase:
        try:
            supabase.auth.sign_out()
            print("[OK] User signed out")
        except Exception as e:
            print(f"[WARN] Sign out error: {e}")
    return "/"

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


if __name__ == "__main__":
    app.run(debug=False, port=8050)

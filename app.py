import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dashboard import create_dashboard_layout
from login_page import create_login_layout, USER_ICON, ADMIN_ICON, PERSON_ICON, LOCK_ICON, GEAR_SVG, feature_icon

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server  # Expose Flask server for deployment

# Main app layout with routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Routing callback
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == '/dashboard':
        return create_dashboard_layout()
    else:
        return create_login_layout()

# Login callback
@app.callback(
    Output("url", "pathname"),
    Input("signin-btn", "n_clicks"),
    State("username-input", "value"),
    State("password-input", "value"),
    prevent_initial_call=True,
)
def handle_login(n_clicks, username, password):
    if not username or not password:
        return '/'
    return '/dashboard'

# Logout callback
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("logout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def handle_logout(n_clicks):
    return '/'

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

# Login status callback
@app.callback(
    Output("login-status", "children"),
    Input("signin-btn", "n_clicks"),
    State("username-input", "value"),
    State("password-input", "value"),
    prevent_initial_call=True,
)
def update_login_status(n_clicks, username, password):
    if not username or not password:
        return html.Span("Please enter your credentials.",
                         style={"color": "#ff6b6b", "fontSize": "13px"})
    return html.Span(f"✓ Authenticating as {username}…",
                     style={"color": "#4aff9e", "fontSize": "13px"})


if __name__ == "__main__":
    app.run(debug=False, port=8050)

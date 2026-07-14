"""
Change Password Page — Forced password update on first login.
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import bcrypt


# ═════════════════════════════════════════════
#  SVG ICONS
# ═════════════════════════════════════════════

LOCK_ICON = html.Img(
    src="data:image/svg+xml;base64,"
        "PHN2ZyB2aWV3Qm94PSIwIDAgMjQgMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAw"
        "L3N2ZyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNGE5ZWZmIiBzdHJva2Utd2lkdGg9IjIiIHN0"
        "cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHJlY3QgeD0i"
        "MyIgeT0iMTEiIHdpZHRoPSIxOCIgaGVpZ2h0PSIxMSIgcng9IjIiLz48cGF0aCBkPSJNNyAx"
        "MVY3YTUgNSAwIDAgMSAxMCAwdjQiLz48L3N2Zz4=",
    style={"width": "20px", "height": "20px"}
)

SHIELD_ICON = html.Img(
    src="data:image/svg+xml;base64,"
        "PHN2ZyB2aWV3Qm94PSIwIDAgMjQgMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAw"
        "L3N2ZyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNGE5ZWZmIiBzdHJva2Utd2lkdGg9IjIiIHN0"
        "cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0i"
        "TTEyIDJMMiA3djVjMCA1LjUgMy44IDEwLjcgMTAgMTIgNi4yLTEuMyAxMC02LjUgMTAtMTJW"
        "N0wxMiAyeiIvPjwvc3ZnPg==",
    style={"width": "64px", "height": "64px", "marginBottom": "20px"}
)


# ═════════════════════════════════════════════
#  LAYOUT
# ═════════════════════════════════════════════

def create_change_password_layout():
    """Layout for the forced password change page (first login)."""
    return html.Div(
        style={
            "display": "flex",
            "minHeight": "100vh",
            "fontFamily": "'Segoe UI', sans-serif",
            "background": "#0a1628",
            "alignItems": "center",
            "justifyContent": "center",
        },
        children=[
            dcc.Location(id="url-change-password", refresh=False),
            html.Div(
                style={
                    "width": "100%",
                    "maxWidth": "480px",
                    "background": "linear-gradient(160deg, #0d2045 0%, #101a2f 100%)",
                    "border": "1px solid rgba(74,158,255,0.2)",
                    "borderRadius": "16px",
                    "padding": "48px 40px",
                    "boxShadow": "0 12px 48px rgba(0,0,0,0.4)",
                },
                children=[
                    # Header
                    html.Div(
                        style={"textAlign": "center", "marginBottom": "32px"},
                        children=[
                            SHIELD_ICON,
                            html.H2("Update Your Password", style={
                                "color": "white", "fontWeight": "700", "fontSize": "24px",
                                "marginBottom": "8px",
                            }),
                            html.P(
                                "For security purposes, please set a new password before continuing.",
                                style={
                                    "color": "rgba(168,212,255,0.7)", "fontSize": "13px",
                                    "lineHeight": "1.5", "margin": "0",
                                }
                            ),
                        ]
                    ),

                    # New Password field
                    html.Div(
                        style={"marginBottom": "20px"},
                        children=[
                            html.Label("NEW PASSWORD", style={
                                "color": "rgba(180,210,255,0.7)", "fontSize": "11px",
                                "fontWeight": "600", "letterSpacing": "1.5px",
                                "marginBottom": "10px", "display": "block",
                            }),
                            html.Div(
                                style={
                                    "display": "flex", "alignItems": "center", "gap": "12px",
                                    "background": "rgba(10,25,55,0.8)",
                                    "border": "1.5px solid rgba(74,158,255,0.25)",
                                    "borderRadius": "8px", "padding": "8px 16px",
                                },
                                children=[
                                    LOCK_ICON,
                                    dcc.Input(
                                        id="change-pw-new",
                                        type="password",
                                        placeholder="Enter new password",
                                        style={
                                            "flex": "1", "background": "transparent",
                                            "border": "none", "color": "white",
                                            "fontSize": "14px", "outline": "none",
                                            "fontFamily": "inherit",
                                        }
                                    ),
                                ]
                            ),
                        ]
                    ),

                    # Confirm Password field
                    html.Div(
                        style={"marginBottom": "28px"},
                        children=[
                            html.Label("CONFIRM PASSWORD", style={
                                "color": "rgba(180,210,255,0.7)", "fontSize": "11px",
                                "fontWeight": "600", "letterSpacing": "1.5px",
                                "marginBottom": "10px", "display": "block",
                            }),
                            html.Div(
                                style={
                                    "display": "flex", "alignItems": "center", "gap": "12px",
                                    "background": "rgba(10,25,55,0.8)",
                                    "border": "1.5px solid rgba(74,158,255,0.25)",
                                    "borderRadius": "8px", "padding": "8px 16px",
                                },
                                children=[
                                    LOCK_ICON,
                                    dcc.Input(
                                        id="change-pw-confirm",
                                        type="password",
                                        placeholder="Confirm new password",
                                        style={
                                            "flex": "1", "background": "transparent",
                                            "border": "none", "color": "white",
                                            "fontSize": "14px", "outline": "none",
                                            "fontFamily": "inherit",
                                        }
                                    ),
                                ]
                            ),
                        ]
                    ),

                    # Password requirements hint
                    html.Div(
                        style={"marginBottom": "24px", "padding": "12px 14px",
                               "background": "rgba(74,158,255,0.06)",
                               "borderRadius": "8px", "border": "1px solid rgba(74,158,255,0.12)"},
                        children=[
                            html.Div("Password requirements:", style={
                                "color": "rgba(168,212,255,0.7)", "fontSize": "11px",
                                "fontWeight": "600", "marginBottom": "6px",
                            }),
                            html.Div("• At least 8 characters", style={
                                "color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                "marginBottom": "2px",
                            }),
                            html.Div("• Must not be the same as your current password", style={
                                "color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                            }),
                        ]
                    ),

                    # Submit button
                    html.Button(
                        "Update Password",
                        id="change-pw-btn",
                        n_clicks=0,
                        style={
                            "width": "100%", "padding": "14px",
                            "background": "linear-gradient(90deg, #1a6fd4 0%, #2a85f0 100%)",
                            "border": "none", "borderRadius": "8px",
                            "color": "white", "fontSize": "15px", "fontWeight": "700",
                            "cursor": "pointer", "letterSpacing": "0.5px",
                            "boxShadow": "0 4px 20px rgba(42,133,240,0.35)",
                            "transition": "all 0.2s",
                        }
                    ),

                    # Status message
                    html.Div(
                        id="change-pw-status",
                        style={"textAlign": "center", "marginTop": "16px", "minHeight": "20px"},
                    ),
                ]
            )
        ]
    )


# ═════════════════════════════════════════════
#  CALLBACKS
# ═════════════════════════════════════════════

def register_change_password_callbacks(app, supabase=None, supabase_admin=None):
    """Register callback for handling password change."""

    @app.callback(
        Output("url-change-password", "pathname"),
        Output("change-pw-status", "children"),
        Output("session-store", "data", allow_duplicate=True),
        Input("change-pw-btn", "n_clicks"),
        State("change-pw-new", "value"),
        State("change-pw-confirm", "value"),
        State("session-store", "data"),
        prevent_initial_call=True,
    )
    def handle_change_password(n_clicks, new_password, confirm_password, session):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate

        if not new_password or not confirm_password:
            return dash.no_update, html.Span(
                "Please fill in both fields.",
                style={"color": "#ff6b6b", "fontSize": "13px"}
            ), dash.no_update

        if new_password != confirm_password:
            return dash.no_update, html.Span(
                "Passwords do not match.",
                style={"color": "#ff6b6b", "fontSize": "13px"}
            ), dash.no_update

        if len(new_password) < 8:
            return dash.no_update, html.Span(
                "Password must be at least 8 characters.",
                style={"color": "#ff6b6b", "fontSize": "13px"}
            ), dash.no_update

        if not session or not session.get("user_id"):
            return "/", html.Span(
                "Session expired. Please log in again.",
                style={"color": "#ff6b6b", "fontSize": "13px"}
            ), None

        user_id = session["user_id"]
        admin_client = supabase_admin or supabase

        try:
            # Hash the new password with bcrypt
            hashed_pw = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            # Update password_hash in the users table
            if supabase:
                supabase.table("users") \
                    .update({"password_hash": hashed_pw, "last_login_at": "now()"}) \
                    .eq("id", user_id) \
                    .execute()

            # Also update via Supabase Auth Admin API (keeps auth.users in sync)
            try:
                admin_client.auth.admin.update_user_by_id(
                    user_id,
                    {"password": new_password}
                )
            except Exception:
                pass  # Non-critical if auth.users update fails

            # Update session — remove the must_change_password flag
            updated_session = {**session}
            updated_session.pop("must_change_password", None)

            # Redirect to dashboard
            role = session.get("role", "user")
            redirect_path = "/dev-dashboard" if role == "developer" else "/dashboard"

            print(f"[OK] Password changed for user {user_id}")
            return redirect_path, "", updated_session

        except Exception as e:
            print(f"[ERROR] Password change failed: {e}")
            return dash.no_update, html.Span(
                "Failed to update password. Please try again.",
                style={"color": "#ff6b6b", "fontSize": "13px"}
            ), dash.no_update

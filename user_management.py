import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import base64
from datetime import datetime
from assets.components import (build_admin_sidebar, build_topbar)

PERMISSION_MATRIX = [
    {"page": "Overview", "desc": "Engine status, RUL cards, alerts", "sme": True, "admin": True},
    {"page": "Sensor Trends", "desc": "Multi-sensor chart, normalize toggle", "sme": True, "admin": True},
    {"page": "Degradation Analysis", "desc": "SHAP charts, fault mode detection", "sme": True, "admin": True},
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
                dcc.Link(
                    href=f"/edit-user/{user['id']}",
                    style={"textDecoration": "none"},
                    children=[
                        html.Button("Edit", id={"type": "edit-user-btn", "index": user["id"]}, n_clicks=0, style={
                            "background": "rgba(74,158,255,0.18)", "border": "1px solid rgba(74,158,255,0.4)",
                            "color": "#a8d4ff", "borderRadius": "6px", "padding": "5px 12px",
                            "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                        }),
                    ]
                ),
                html.Button("Remove", id={"type": "remove-user-btn", "index": user["id"]}, n_clicks=0, style={
                    "background": "rgba(255,77,77,0.15)", "border": "1px solid rgba(255,77,77,0.4)",
                    "color": "#ff6b6b", "borderRadius": "6px", "padding": "5px 12px",
                    "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                    "display": "none" if is_admin else "inline-block",
                }),
            ])
        ]
    )


def build_users_table(users, deleted_users=None):
    if deleted_users is None:
        deleted_users = []
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
                    "display": "grid", "gridTemplateColumns": "1fr 1.4fr 0.7fr 1fr 0.7fr 1fr",
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
            # Deleted users rendered inside the same table
            html.Div(id="deleted-users-body",
                     children=[deleted_user_table_row(u, i) for i, u in enumerate(deleted_users)]),
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

def deleted_user_table_row(user, idx):
    """Render a greyed-out row for a soft-deleted user with a Restore button."""
    return html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1.4fr 0.7fr 1fr 0.7fr 1fr",
            "alignItems": "center",
            "padding": "12px 24px",
            "borderBottom": "1px solid rgba(74,158,255,0.05)",
            "opacity": "0.5",
        },
        children=[
            html.Span(user["username"], style={"color": "rgba(168,212,255,0.5)", "fontSize": "13px", "fontWeight": "600"}),
            html.Span(user["full_name"], style={"color": "rgba(168,212,255,0.4)", "fontSize": "13px"}),
            role_badge(user["role"]),
            html.Span(user["last_login"], style={"color": "rgba(168,212,255,0.4)", "fontSize": "12px"}),
            html.Span("Deleted", style={"color": "rgba(255,77,77,0.6)", "fontSize": "12px"}),
            html.Div(style={"display": "flex", "gap": "8px"}, children=[
                html.Button("Restore", id={"type": "restore-user-btn", "index": user["id"]}, n_clicks=0, style={
                    "background": "rgba(0,200,117,0.15)", "border": "1px solid rgba(0,200,117,0.4)",
                    "color": "#00c875", "borderRadius": "6px", "padding": "5px 12px",
                    "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                }),
            ])
        ]
    )


def build_user_management_body(users=None, deleted_users=None):
    if users is None:
        users = _sample_users()
    if deleted_users is None:
        deleted_users = []

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
        build_users_table(users, deleted_users=deleted_users),

        dcc.Store(id="users-data", data=users),
        dcc.Store(id="deleted-users-data", data=deleted_users),
        html.Div(id="add-user-modal-container"),
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_user_management_layout(supabase=None, org_id=None):
    users = None
    deleted_users = None
    try:
        if supabase:
            # Fetch active users (is_deleted = true means active)
            query = supabase.table("users") \
                .select("id, username, first_name, last_name, role, status, last_login_at, is_deleted")
            if org_id:
                query = query.eq("organization_id", org_id)
            resp = query.execute()
            if resp.data:
                users = []
                deleted_users = []
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

                    user_data = {
                        "id": str(u.get("id")),
                        "username": u.get("username", "—"),
                        "full_name": full_name,
                        "role": (u.get("role") or "user").lower(),
                        "last_login": last_login,
                        "status": (u.get("status") or "offline").lower(),
                        "is_deleted": not u.get("is_deleted", True),  # invert: is_deleted=false in DB means deleted
                    }

                    if u.get("is_deleted", True):
                        users.append(user_data)
                    else:
                        deleted_users.append(user_data)
    except Exception as e:
        import traceback
        print(f"[ERROR] user management fetch: {traceback.format_exc()}")

    if not users:
        users = _sample_users()
    if not deleted_users:
        deleted_users = []

    return html.Div(
        style={
            "height": "100vh",
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628",
            "color": "white",
            "overflow": "hidden",
        },
        children=[
            dcc.Location(id="url-user-mgmt", refresh=False),

            build_topbar(),

            html.Div(
                style={
                    "flex": "1",
                    "display": "flex",
                    "flexDirection": "row",
                    "overflow": "hidden",
                    "minHeight": "0",
                },
                children=[
                    build_admin_sidebar(active_page="users"),
                    html.Div(
                        style={
                            "flex": "1",
                            "overflowY": "auto",
                            "padding": "24px 28px",
                            "minWidth": "0",
                        },
                        children=build_user_management_body(users=users, deleted_users=deleted_users),
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
        Output("deleted-users-body", "children"),
        Output("deleted-users-data", "data"),
        Input({"type": "remove-user-btn", "index": dash.ALL}, "n_clicks"),
        State("users-data", "data"),
        State("deleted-users-data", "data"),
        prevent_initial_call=True,
    )
    def remove_user(n_clicks_list, users_data, deleted_data):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        import json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        user_id = json.loads(trigger_id)["index"]

        # Soft delete: mark as deleted (is_deleted = false means removed)
        if supabase:
            try:
                supabase.table("users").update({"is_deleted": False}).eq("id", user_id).execute()
            except Exception as e:
                print(f"[ERROR] soft-delete user: {e}")

        # Move user from active to deleted list
        removed_user = next((u for u in users_data if u["id"] == user_id), None)
        updated_users = [u for u in users_data if u["id"] != user_id]
        if deleted_data is None:
            deleted_data = []
        if removed_user:
            removed_user["is_deleted"] = True
            deleted_data.append(removed_user)

        user_rows = [user_table_row(u, i) for i, u in enumerate(updated_users)]
        deleted_rows = [deleted_user_table_row(u, i) for i, u in enumerate(deleted_data)]

        return user_rows, updated_users, deleted_rows, deleted_data

    @app.callback(
        Output("users-table-body", "children", allow_duplicate=True),
        Output("users-data", "data", allow_duplicate=True),
        Output("deleted-users-body", "children", allow_duplicate=True),
        Output("deleted-users-data", "data", allow_duplicate=True),
        Input({"type": "restore-user-btn", "index": dash.ALL}, "n_clicks"),
        State("users-data", "data"),
        State("deleted-users-data", "data"),
        prevent_initial_call=True,
    )
    def restore_user(n_clicks_list, users_data, deleted_data):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        import json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        user_id = json.loads(trigger_id)["index"]

        # Restore: set is_deleted back to true (active)
        if supabase:
            try:
                supabase.table("users").update({"is_deleted": True}).eq("id", user_id).execute()
            except Exception as e:
                print(f"[ERROR] restore user: {e}")

        # Move user from deleted to active list
        restored_user = next((u for u in (deleted_data or []) if u["id"] == user_id), None)
        updated_deleted = [u for u in (deleted_data or []) if u["id"] != user_id]
        if restored_user:
            restored_user["is_deleted"] = False
            users_data.append(restored_user)

        user_rows = [user_table_row(u, i) for i, u in enumerate(users_data)]
        deleted_rows = [deleted_user_table_row(u, i) for i, u in enumerate(updated_deleted)]

        return user_rows, users_data, deleted_rows, updated_deleted


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
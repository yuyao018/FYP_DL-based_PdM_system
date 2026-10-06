import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import base64
from datetime import datetime
from assets.components import (build_admin_sidebar, build_topbar)

def status_badge(status):
    status_lower = status.lower()
    cfg = {
        "healthy":  {"bg": "rgba(0,200,100,0.18)", "border": "#00c875", "text": "#00c875"},
        "warning":  {"bg": "rgba(255,217,61,0.18)", "border": "#ffd93d", "text": "#ffd93d"},
        "critical": {"bg": "rgba(255,77,77,0.18)",  "border": "#ff4d4d", "text": "#ff4d4d"},
    }
    c = cfg.get(status_lower, cfg["healthy"])
    label = status_lower.upper()

    badge = html.Span(label, style={
        "background": c["bg"], "color": c["text"], "border": f"1px solid {c['border']}",
        "borderRadius": "6px", "padding": "3px 10px", "fontSize": "11px", "fontWeight": "700",
        "whiteSpace": "nowrap", "display": "inline-block",
    })
    return html.Div(style={"display": "flex", "justifyContent": "flex-start"}, children=[badge])


# ─────────────────────────────────────────────
#  ENGINES TABLE
# ─────────────────────────────────────────────

def engine_table_row(engine, idx):
    return html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "0.8fr 1.2fr 0.8fr 1fr 0.8fr 1fr",
            "alignItems": "center",
            "padding": "12px 24px",
            "borderBottom": "1px solid rgba(74,158,255,0.08)",
        },
        children=[
            html.Span(f"ENGINE-{str(engine['engine_id']).zfill(2)}", 
                     style={"color": "white", "fontSize": "13px", "fontWeight": "600"}),
            html.Span(engine.get("model_type", "—"), 
                     style={"color": "#a8d4ff", "fontSize": "13px"}),
            status_badge(engine.get("condition_status", "healthy")),
            html.Span(f"{engine.get('current_cycle', 0)} cycles", 
                     style={"color": "#a8d4ff", "fontSize": "12px"}),
            html.Span(engine.get("created_at", "—"), 
                     style={"color": "#a8d4ff", "fontSize": "12px"}),
            html.Div(style={"display": "flex", "gap": "8px"}, children=[
                dcc.Link(
                    href=f"/overview/{engine['id']}",
                    style={"textDecoration": "none"},
                    children=[
                        html.Button("View", n_clicks=0, style={
                            "background": "rgba(74,158,255,0.18)", "border": "1px solid rgba(74,158,255,0.4)",
                            "color": "#a8d4ff", "borderRadius": "6px", "padding": "5px 12px",
                            "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                        })
                    ]
                ),
                dcc.Link(
                    href=f"/edit-engine/{engine['id']}",
                    style={"textDecoration": "none"},
                    children=[
                        html.Button("Edit", id={"type": "edit-engine-btn", "index": engine["id"]}, n_clicks=0, style={
                            "background": "rgba(74,158,255,0.18)", "border": "1px solid rgba(74,158,255,0.4)",
                            "color": "#a8d4ff", "borderRadius": "6px", "padding": "5px 12px",
                            "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                        }),
                    ]
                ),
                html.Button("Remove", id={"type": "remove-engine-btn", "index": engine["id"]}, n_clicks=0, style={
                    "background": "rgba(255,77,77,0.15)", "border": "1px solid rgba(255,77,77,0.4)",
                    "color": "#ff6b6b", "borderRadius": "6px", "padding": "5px 12px",
                    "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                }),
            ])
        ]
    )


def deleted_engine_table_row(engine, idx):
    return html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "0.8fr 1.2fr 0.8fr 1fr 0.8fr 1fr",
            "alignItems": "center",
            "padding": "12px 24px",
            "borderBottom": "1px solid rgba(74,158,255,0.05)",
            "opacity": "0.5",
        },
        children=[
            html.Span(f"ENGINE-{str(engine['engine_id']).zfill(2)}", style={"color": "rgba(168,212,255,0.5)", "fontSize": "13px", "fontWeight": "600"}),
            html.Span(engine.get("model_type", "N/A"), style={"color": "rgba(168,212,255,0.4)", "fontSize": "13px"}),
            html.Span("Deleted", style={"color": "rgba(255,77,77,0.6)", "fontSize": "12px"}),
            html.Span(f"{engine.get('current_cycle', 0)} cycles", style={"color": "rgba(168,212,255,0.4)", "fontSize": "13px"}),
            html.Span((engine.get("created_at") or "")[:10], style={"color": "rgba(168,212,255,0.4)", "fontSize": "12px"}),
            html.Div(style={"display": "flex", "gap": "8px"}, children=[
                html.Button("Restore", id={"type": "restore-engine-btn", "index": engine["id"]}, n_clicks=0, style={
                    "background": "rgba(0,200,117,0.15)", "border": "1px solid rgba(0,200,117,0.4)",
                    "color": "#00c875", "borderRadius": "6px", "padding": "5px 12px",
                    "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                }),
            ])
        ]
    )


def build_engines_table(engines, deleted_engines=None):
    if deleted_engines is None:
        deleted_engines = []

    total = len(engines)
    healthy = sum(1 for e in engines if e.get("condition_status", "healthy").lower() == "healthy")
    warning = sum(1 for e in engines if e.get("condition_status", "healthy").lower() == "warning")
    critical = sum(1 for e in engines if e.get("condition_status", "healthy").lower() == "critical")

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
                    html.Span("Engines", style={"color": "white", "fontSize": "15px", "fontWeight": "700"}),
                    html.Span(f"{total} total · {healthy} healthy · {warning} warning · {critical} critical",
                              style={"color": "rgba(168,212,255,0.5)", "fontSize": "12px"}),
                ]
            ),
            html.Div(
                style={
                    "display": "grid", "gridTemplateColumns": "0.8fr 1.2fr 0.8fr 1fr 0.8fr 1fr",
                    "padding": "10px 24px",
                    "background": "rgba(74,158,255,0.06)",
                    "borderTop": "1px solid rgba(74,158,255,0.12)",
                    "borderBottom": "1px solid rgba(74,158,255,0.12)",
                },
                children=[
                    html.Span("ENGINE ID",    style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("MODEL TYPE",   style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("STATUS",       style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("CURRENT CYCLE",style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("CREATED",      style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("ACTIONS",      style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                ]
            ),
            html.Div(id="engines-table-body",
                     children=[engine_table_row(e, i) for i, e in enumerate(engines)]),
            html.Div(id="deleted-engines-body",
                     children=[deleted_engine_table_row(e, i) for i, e in enumerate(deleted_engines)]),
        ]
    )

# ─────────────────────────────────────────────
#  MAIN PAGE BODY
# ─────────────────────────────────────────────

def build_engine_management_body(engines=None, deleted_engines=None):
    if engines is None:
        engines = []
    if deleted_engines is None:
        deleted_engines = []

    return [
        # Header row: title + Add Engine button
        html.Div(
            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between",
                   "marginBottom": "8px"},
            children=[
                html.H2("ENGINE MANAGEMENT", style={"margin": "0", "color": "white",
                                                     "fontSize": "22px", "fontWeight": "800"}),
                dcc.Link(href="/add-engine", style={"textDecoration": "none"}, children=[
                    html.Button(
                        "+ Add Engine", id="add-engine-btn", n_clicks=0,
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

        build_engines_table(engines, deleted_engines=deleted_engines),

        dcc.Store(id="engines-data", data=engines),
        dcc.Store(id="deleted-engines-data", data=deleted_engines),
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_engine_management_layout(supabase=None, org_id=None):
    engines = []
    deleted_engines = []

    if not supabase:
        print("[WARN] Supabase not connected - no engine data available")
    else:
        try:
            # ── Fetch alert thresholds ──
            warn_thresh = 62
            crit_thresh = 30
            max_life    = 125
            try:
                t_resp = supabase.table("alert_thresholds") \
                    .select("warning_threshold, critical_threshold, max_rul_cap") \
                    .order("updated_at", desc=True) \
                    .limit(1).execute()
                if t_resp.data:
                    warn_thresh = int(t_resp.data[0].get("warning_threshold", warn_thresh))
                    crit_thresh = int(t_resp.data[0].get("critical_threshold", crit_thresh))
                    max_life    = int(t_resp.data[0].get("max_rul_cap", max_life))
            except Exception:
                pass

            query = supabase.table("engines") \
                .select("id, engine_id, model_type, condition_status, current_cycle, created_at, is_deleted")

            if org_id:
                query = query.eq("organization_id", org_id)

            resp = query.order("engine_id").execute()

            if resp.data:
                engine_ids = [e.get("id") for e in resp.data if e.get("id")]

                # ── Batch-fetch latest predicted_rul per engine ──
                latest_rul_map = {}
                if engine_ids:
                    try:
                        pred_resp = supabase.table("rul_predictions") \
                            .select("engine_id, predicted_rul") \
                            .in_("engine_id", engine_ids) \
                            .order("predicted_at", desc=True) \
                            .execute()
                        for row in (pred_resp.data or []):
                            eid = row.get("engine_id")
                            if eid and eid not in latest_rul_map \
                                    and row.get("predicted_rul") is not None:
                                latest_rul_map[eid] = float(row["predicted_rul"])
                    except Exception:
                        pass

                for e in resp.data:
                    created_at = e.get("created_at")
                    if created_at:
                        try:
                            created_at = datetime.fromisoformat(
                                created_at.replace("Z", "+00:00")
                            ).strftime("%Y-%m-%d")
                        except Exception:
                            created_at = str(created_at)[:10]
                    else:
                        created_at = "—"

                    db_id = str(e.get("id"))

                    # Derive status from latest prediction + thresholds
                    if db_id in latest_rul_map:
                        rul = latest_rul_map[db_id]
                        if rul <= crit_thresh:
                            condition_status = "critical"
                        elif rul <= warn_thresh:
                            condition_status = "warning"
                        else:
                            condition_status = "healthy"
                    else:
                        condition_status = (e.get("condition_status") or "healthy").lower()

                    engines.append({
                        "id":               db_id,
                        "engine_id":        e.get("engine_id", 0),
                        "model_type":       e.get("model_type", "—"),
                        "condition_status": condition_status,
                        "current_cycle":    e.get("current_cycle", 0),
                        "created_at":       created_at,
                        "is_deleted":       e.get("is_deleted", True),
                    })

                # Separate active engines from deleted ones
                all_engines = engines[:]
                engines = [eng for eng in all_engines if eng.get("is_deleted", True) is True]
                deleted_engines = [eng for eng in all_engines if eng.get("is_deleted", True) is False]

                print(f"[OK] Loaded {len(engines)} active engines and {len(deleted_engines)} deleted engines from database")
            else:
                print("[INFO] No engines found in database")

        except Exception as e:
            import traceback
            print(f"[ERROR] engine management fetch: {traceback.format_exc()}")

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
            dcc.Location(id="url-engine-mgmt", refresh=False),

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
                    build_admin_sidebar(active_page="engines"),
                    html.Div(
                        style={
                            "flex": "1",
                            "overflowY": "auto",
                            "padding": "24px 28px",
                            "minWidth": "0",
                        },
                        children=build_engine_management_body(engines=engines, deleted_engines=deleted_engines),
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def register_engine_management_callbacks(app, supabase=None):

    @app.callback(
        Output("engines-table-body", "children"),
        Output("engines-data", "data"),
        Output("deleted-engines-body", "children", allow_duplicate=True),
        Output("deleted-engines-data", "data", allow_duplicate=True),
        Input({"type": "remove-engine-btn", "index": dash.ALL}, "n_clicks"),
        State("engines-data", "data"),
        State("deleted-engines-data", "data"),
        prevent_initial_call=True,
    )
    def remove_engine(n_clicks_list, engines_data, deleted_engines_data):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        if deleted_engines_data is None:
            deleted_engines_data = []

        import json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        engine_id = json.loads(trigger_id)["index"]

        # Soft-delete: set is_deleted = False in Supabase
        if supabase:
            try:
                supabase.table("engines").update({"is_deleted": False}).eq("id", engine_id).execute()
                print(f"[OK] Soft-deleted engine {engine_id}")
            except Exception as e:
                print(f"[ERROR] soft-delete engine: {e}")

        # Stop the simulation thread if running
        try:
            from engine_simulation_manager import stop_engine_simulation, _SENSOR_BUFFER, _SENSOR_LOCK
            stop_engine_simulation(engine_id)
            # Clear sensor buffer
            with _SENSOR_LOCK:
                _SENSOR_BUFFER.pop(engine_id, None)
        except Exception:
            pass

        # Move engine from active to deleted list
        removed_engine = next((e for e in engines_data if e["id"] == engine_id), None)
        updated_engines = [e for e in engines_data if e["id"] != engine_id]
        if removed_engine:
            deleted_engines_data.append(removed_engine)

        active_rows = [engine_table_row(e, i) for i, e in enumerate(updated_engines)]
        deleted_rows = [deleted_engine_table_row(e, i) for i, e in enumerate(deleted_engines_data)]
        return active_rows, updated_engines, deleted_rows, deleted_engines_data

    @app.callback(
        Output("engines-table-body", "children", allow_duplicate=True),
        Output("engines-data", "data", allow_duplicate=True),
        Output("deleted-engines-body", "children"),
        Output("deleted-engines-data", "data"),
        Input({"type": "restore-engine-btn", "index": dash.ALL}, "n_clicks"),
        State("engines-data", "data"),
        State("deleted-engines-data", "data"),
        prevent_initial_call=True,
    )
    def restore_engine(n_clicks_list, engines_data, deleted_engines_data):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        if engines_data is None:
            engines_data = []
        if deleted_engines_data is None:
            deleted_engines_data = []

        import json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        engine_id = json.loads(trigger_id)["index"]

        # Restore: set is_deleted = True in Supabase
        if supabase:
            try:
                supabase.table("engines").update({"is_deleted": True}).eq("id", engine_id).execute()
                print(f"[OK] Restored engine {engine_id}")
            except Exception as e:
                print(f"[ERROR] restore engine: {e}")

        # Move engine from deleted to active list
        restored_engine = next((e for e in deleted_engines_data if e["id"] == engine_id), None)
        updated_deleted = [e for e in deleted_engines_data if e["id"] != engine_id]
        if restored_engine:
            engines_data.append(restored_engine)

        active_rows = [engine_table_row(e, i) for i, e in enumerate(engines_data)]
        deleted_rows = [deleted_engine_table_row(e, i) for i, e in enumerate(updated_deleted)]
        return active_rows, engines_data, deleted_rows, updated_deleted


# ─────────────────────────────────────────────
#  STANDALONE RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True)
    app.layout = html.Div([
        dcc.Store(id="sidebar-state", data=True),
        create_engine_management_layout()
    ])
    register_engine_management_callbacks(app)
    app.run(debug=True)

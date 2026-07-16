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
                html.Button("Edit", id={"type": "edit-engine-btn", "index": engine["id"]}, n_clicks=0, style={
                    "background": "rgba(74,158,255,0.18)", "border": "1px solid rgba(74,158,255,0.4)",
                    "color": "#a8d4ff", "borderRadius": "6px", "padding": "5px 12px",
                    "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                }),
                html.Button("Remove", id={"type": "remove-engine-btn", "index": engine["id"]}, n_clicks=0, style={
                    "background": "rgba(255,77,77,0.15)", "border": "1px solid rgba(255,77,77,0.4)",
                    "color": "#ff6b6b", "borderRadius": "6px", "padding": "5px 12px",
                    "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                }),
            ])
        ]
    )


def build_engines_table(engines):
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
        ]
    )

# ─────────────────────────────────────────────
#  MAIN PAGE BODY
# ─────────────────────────────────────────────

def build_engine_management_body(engines=None):
    if engines is None:
        engines = []

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

        build_engines_table(engines),

        dcc.Store(id="engines-data", data=engines),
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_engine_management_layout(supabase=None, org_id=None):
    engines = []

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
                .select("id, engine_id, model_type, condition_status, current_cycle, created_at")

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
                    })

                print(f"[OK] Loaded {len(engines)} engines from database")
            else:
                print("[INFO] No engines found in database")

        except Exception as e:
            import traceback
            print(f"[ERROR] engine management fetch: {traceback.format_exc()}")

    return html.Div(
        style={
            "minHeight": "100vh",
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628",
            "color": "white",
        },
        children=[
            dcc.Location(id="url-engine-mgmt", refresh=False),

            html.Div(
                style={
                    "position": "sticky",
                    "top": "0",
                    "zIndex": "200",
                },
                children=[build_topbar()]
            ),

            html.Div(
                style={
                    "flex": "1",
                    "display": "flex",
                    "flexDirection": "row",
                },
                children=[
                    build_admin_sidebar(active_page="engines"),
                    html.Div(
                        style={
                            "flex": "1",
                            "padding": "24px 28px",
                            "minWidth": "0",
                        },
                        children=build_engine_management_body(engines=engines),
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
        Input({"type": "remove-engine-btn", "index": dash.ALL}, "n_clicks"),
        State("engines-data", "data"),
        prevent_initial_call=True,
    )
    def remove_engine(n_clicks_list, engines_data):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        import json
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        engine_id = json.loads(trigger_id)["index"]

        # Remove from Supabase if connected
        if supabase:
            # Delete in order: dependents first, then the engine itself
            try:
                resp = supabase.table("rul_predictions").delete().eq("engine_id", engine_id).execute()
                print(f"[OK] Deleted rul_predictions for engine {engine_id}: {len(resp.data or [])} rows")
            except Exception as e:
                print(f"[ERROR] remove rul_predictions for engine {engine_id}: {e}")
            try:
                # Check what alert_logs exist for this engine
                check = supabase.table("alert_logs").select("id").eq("engine_id", engine_id).execute()
                print(f"[DEBUG] alert_logs to delete: {len(check.data or [])} rows for engine_id={engine_id}")
                if check.data:
                    resp = supabase.table("alert_logs").delete().eq("engine_id", engine_id).execute()
                    print(f"[OK] Deleted alert_logs for engine {engine_id}: {len(resp.data or [])} rows")
            except Exception as e:
                print(f"[ERROR] remove alert_logs for engine {engine_id}: {e}")
            try:
                resp = supabase.table("engines").delete().eq("id", engine_id).execute()
                print(f"[OK] Deleted engine {engine_id}")
            except Exception as e:
                print(f"[ERROR] remove engine: {e}")

        # Stop the simulation thread if running
        try:
            from engine_simulation_manager import stop_engine_simulation, _SENSOR_BUFFER, _SENSOR_LOCK
            stop_engine_simulation(engine_id)
            # Clear sensor buffer
            with _SENSOR_LOCK:
                _SENSOR_BUFFER.pop(engine_id, None)
        except Exception:
            pass

        # Remove JSON data file from disk
        try:
            from data_utils import BASE_DATA_DIR
            import os as _os
            if _os.path.isdir(BASE_DATA_DIR):
                for folder in _os.listdir(BASE_DATA_DIR):
                    folder_path = _os.path.join(BASE_DATA_DIR, folder)
                    if not _os.path.isdir(folder_path):
                        continue
                    # Look for engine_<db_id>.json (new format)
                    target = _os.path.join(folder_path, f"engine_{engine_id}.json")
                    if _os.path.exists(target):
                        _os.remove(target)
                        print(f"[OK] Removed data file: {target}")
                        break
                    # Fallback: old format engine_<num>.json
                    eng_entry = next((e for e in engines_data if e["id"] == engine_id), None)
                    if eng_entry:
                        old_target = _os.path.join(folder_path, f"engine_{str(eng_entry.get('engine_id', 0)).zfill(3)}.json")
                        if _os.path.exists(old_target):
                            _os.remove(old_target)
                            print(f"[OK] Removed data file (old format): {old_target}")
                            break
        except Exception as e:
            print(f"[WARN] Could not remove data file for engine {engine_id}: {e}")

        updated = [e for e in engines_data if e["id"] != engine_id]
        rows = [engine_table_row(e, i) for i, e in enumerate(updated)]
        return rows, updated

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
            "flexShrink": "0", "height": "100%", "background": "#0d1e3a",
            "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex", "flexDirection": "column",
            "overflow": "hidden", "transition": "width 0.3s ease",
        }
        return ({**base, "width": "210px"}, True) if is_open else ({**base, "width": "0px"}, False)


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

from assets import database_integration as db
from auth_security import require_trusted_role
from engine_maintenance_status import engine_maintenance_statuses, maintenance_badge
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import base64
import json
import logging
from datetime import datetime
from assets.components import (build_admin_sidebar, build_topbar)

ENGINE_TABLE_COLUMNS = "minmax(110px, 1fr) minmax(95px, 0.8fr) minmax(100px, 0.8fr) minmax(190px, 1.4fr) minmax(120px, 1fr) minmax(100px, 0.8fr) minmax(205px, 1.4fr)"

def status_badge(status):
    status_lower = status.lower()
    cfg = {
        "healthy":  {"bg": "rgba(0,200,100,0.18)", "border": "#00c875", "text": "#00c875"},
        "warning":  {"bg": "rgba(255,217,61,0.18)", "border": "#ffd93d", "text": "#ffd93d"},
        "critical": {"bg": "rgba(255,77,77,0.18)",  "border": "#ff4d4d", "text": "#ff4d4d"},
    }
    c = cfg.get(status_lower, cfg["healthy"])
    label = status_lower.title()

    badge = html.Span(label, style={
        "background": c["bg"], "color": c["text"], "border": f"1px solid {c['border']}",
        "borderRadius": "6px", "padding": "3px 10px", "fontSize": "11px", "fontWeight": "700",
        "whiteSpace": "nowrap", "display": "inline-block",
    })
    return html.Div(style={"display": "flex", "justifyContent": "flex-start"}, children=[badge])

def engine_table_row(engine, idx):
    return html.Div(
        id={"type": "active-engine-row", "index": engine["id"]},
        style={
            "minWidth": "1164px",
            "display": "grid",
            "gridTemplateColumns": ENGINE_TABLE_COLUMNS,
            "columnGap": "16px",
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
            html.Div(children=maintenance_badge(engine.get("maintenance_status"))
                     if engine.get("maintenance_status") else html.Span(
                         "—", style={"color": "rgba(168,212,255,0.4)"}),
                     title="Maintenance workflow; condition reflects the last sensor prediction."),
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
        id={"type": "deleted-engine-row", "index": engine["id"]},
        style={
            "minWidth": "1164px",
            "display": "grid",
            "gridTemplateColumns": ENGINE_TABLE_COLUMNS,
            "columnGap": "16px",
            "alignItems": "center",
            "padding": "12px 24px",
            "borderBottom": "1px solid rgba(74,158,255,0.05)",
            "opacity": "0.5",
        },
        children=[
            html.Span(f"ENGINE-{str(engine['engine_id']).zfill(2)}", style={"color": "rgba(168,212,255,0.5)", "fontSize": "13px", "fontWeight": "600"}),
            html.Span(engine.get("model_type", "N/A"), style={"color": "rgba(168,212,255,0.4)", "fontSize": "13px"}),
            html.Span("Deleted", style={"color": "rgba(255,77,77,0.6)", "fontSize": "12px"}),
            html.Span("—", style={"color": "rgba(168,212,255,0.4)"}),
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


def engine_count_summary(engines):
    counts = {status: sum((e.get("condition_status") or "healthy").lower() == status
                          for e in engines) for status in ("healthy", "warning", "critical")}
    pending = sum(e.get("maintenance_status") == "pending_verification" for e in engines)
    return (f"{len(engines)} total · {counts['healthy']} healthy · {counts['warning']} warning · "
            f"{counts['critical']} critical · {pending} pending verification")


def build_engines_table(engines, deleted_engines=None):
    if deleted_engines is None:
        deleted_engines = []

    return html.Div(
        style={
            "background": "#101e36", "border": "1px solid rgba(74,158,255,0.15)",
            "borderRadius": "14px", "overflowX": "auto",
        },
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "justifyContent": "space-between",
                       "padding": "16px 24px 12px"},
                children=[
                    html.Span("Engines", style={"color": "white", "fontSize": "15px", "fontWeight": "700"}),
                    html.Span(engine_count_summary(engines), id="engine-count-summary",
                              style={"color": "rgba(168,212,255,0.5)", "fontSize": "12px"}),
                ]
            ),
            html.Div(
                style={
                    "minWidth": "1164px",
                    "display": "grid", "gridTemplateColumns": ENGINE_TABLE_COLUMNS,
                    "columnGap": "16px",
                    "padding": "10px 24px",
                    "background": "rgba(74,158,255,0.06)",
                    "borderTop": "1px solid rgba(74,158,255,0.12)",
                    "borderBottom": "1px solid rgba(74,158,255,0.12)",
                },
                children=[
                    html.Span("ENGINE ID",    style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("MODEL TYPE",   style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("CONDITION",       style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("MAINTENANCE", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("CURRENT CYCLE",style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("CREATED",      style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("ACTIONS",      style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                ]
            ),
            html.Div(id="engines-table-body", children=[engine_table_row(e, i) for i, e in enumerate(engines)]),
            html.Div(id="deleted-engines-body", children=[deleted_engine_table_row(e, i) for i, e in enumerate(deleted_engines)]),
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

        dcc.Store(id="engine-action-timer"),
        dcc.Store(id="engine-action-dismiss-delay", data=None),
        dbc.Toast(
            id="engine-action-status", header="Engine management", children="",
            is_open=False, dismissable=True, duration=None, icon="success",
            className="engine-action-toast",
            style={"position": "fixed", "top": "76px", "right": "24px",
                   "width": "360px", "maxWidth": "calc(100vw - 32px)", "zIndex": 2000},
        ),
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
            filters = [('eq', "organization_id", org_id)] if org_id else []
            initial = db.fetch_records_parallel(supabase, {
                "thresholds": dict(table="alert_thresholds",
                                   columns="warning_threshold,critical_threshold,max_rul_cap",
                                   order_by=[("updated_at", True)], limit=1),
                "engines": dict(table="engines",
                                columns="id,engine_id,model_type,condition_status,current_cycle,created_at,is_deleted",
                                filters=filters, order_by=[("engine_id", False)]),
            })
            warn_thresh, crit_thresh = 50, 30
            try:
                t_resp = initial["thresholds"].result()
                if t_resp.data:
                    warn_thresh = int(t_resp.data[0].get("warning_threshold", warn_thresh))
                    crit_thresh = int(t_resp.data[0].get("critical_threshold", crit_thresh))
            except Exception:
                pass
            resp = initial["engines"].result()

            if resp.data:
                engine_ids = [e.get("id") for e in resp.data if e.get("id")]
                details = db.fetch_records_parallel(supabase, {
                    "maintenance": dict(table="maintenance_schedules", columns="engine_id,status,created_at",
                        filters=[('in_', "engine_id", engine_ids),
                                 ('in_', "status", ["in_progress", "completed", "follow_up_required"])],
                        order_by=[("created_at", True)]),
                    "predictions": dict(table="rul_predictions", columns="engine_id,predicted_rul",
                        filters=[('in_', "engine_id", engine_ids)], order_by=[("predicted_at", True)]),
                })
                try:
                    from engine_maintenance_status import maintenance_status
                    maintenance_states = {}
                    for row in details["maintenance"].result().data or []:
                        maintenance_states.setdefault(str(row.get("engine_id")), maintenance_status(row.get("status")))
                except Exception:
                    maintenance_states = {str(eid): "unavailable" for eid in engine_ids}
                latest_rul_map = {}
                try:
                    for row in details["predictions"].result().data or []:
                        eid = str(row.get("engine_id") or "")
                        if eid and eid not in latest_rul_map and row.get("predicted_rul") is not None:
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
                        "maintenance_status": maintenance_states.get(db_id),
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

    # The Toast stays open between pending and success. Its built-in timer
    # does not reliably restart on that transition, so own the timer explicitly.
    app.clientside_callback(
        """function(message, duration, isOpen) {
            const key = '__engineActionToastTimer';
            if (window[key]) {
                window.clearTimeout(window[key]);
                window[key] = null;
            }
            if (isOpen && duration > 0) {
                window[key] = window.setTimeout(function() {
                    window[key] = null;
                    window.dash_clientside.set_props('engine-action-status', {is_open: false});
                }, duration);
            }
            return window.dash_clientside.no_update;
        }""",
        Output("engine-action-timer", "data"),
        Input("engine-action-status", "children"),
        Input("engine-action-dismiss-delay", "data"),
        Input("engine-action-status", "is_open"),
        prevent_initial_call=True,
    )

    # Browser feedback runs without waiting for an HTTP/database round trip.
    # The server always returns authoritative rows, including on failure.
    for action, row_type, message in (
        ("remove", "active-engine-row", "Removing engine… Saving change."),
        ("restore", "deleted-engine-row", "Restoring engine… Saving change."),
    ):
        app.clientside_callback(
            """function(clicks, style) {
                if (!clicks) return window.dash_clientside.no_update;
                window.dash_clientside.set_props('engine-action-dismiss-delay', {data: null});
                window.dash_clientside.set_props('engine-action-status',
                    {children: %s, header: 'Saving change', icon: 'primary',
                     duration: null, is_open: true});
                return Object.assign({}, style, {display: 'none'});
            }""" % json.dumps(message),
            Output({"type": row_type, "index": dash.MATCH}, "style"),
            Input({"type": action + "-engine-btn", "index": dash.MATCH}, "n_clicks"),
            State({"type": row_type, "index": dash.MATCH}, "style"),
            prevent_initial_call=True,
        )

    @app.callback(
        Output("engines-table-body", "children"),
        Output("engines-data", "data"),
        Output("deleted-engines-body", "children"),
        Output("deleted-engines-data", "data"),
        Output("engine-action-status", "children"),
        Output("engine-count-summary", "children"),
        Output("engine-action-status", "header"),
        Output("engine-action-status", "icon"),
        Output("engine-action-dismiss-delay", "data"),
        Output("engine-action-status", "is_open"),
        Input({"type": "remove-engine-btn", "index": dash.ALL}, "n_clicks"),
        Input({"type": "restore-engine-btn", "index": dash.ALL}, "n_clicks"),
        State("engines-data", "data"),
        State("deleted-engines-data", "data"),
        running=[
            (Output({"type": "remove-engine-btn", "index": dash.ALL}, "disabled"), True, False),
            (Output({"type": "restore-engine-btn", "index": dash.ALL}, "disabled"), True, False),
        ],
        prevent_initial_call=True,
    )
    def change_engine_visibility(remove_clicks, restore_clicks, engines_data, deleted_engines_data):
        ctx = dash.callback_context
        trigger = ctx.triggered_id
        if not isinstance(trigger, dict) or not any(
            item.get("value") for item in ctx.triggered
        ):
            raise dash.exceptions.PreventUpdate

        active = [dict(e) for e in (engines_data or [])]
        deleted = [dict(e) for e in (deleted_engines_data or [])]
        engine_id = trigger["index"]
        restoring = trigger["type"] == "restore-engine-btn"
        message = ""
        saved = False
        try:
            principal = require_trusted_role("admin")
            if not supabase:
                raise RuntimeError("Database is unavailable")
            response = db.update_records(
                supabase, "engines", {"is_deleted": restoring},
                filters=[('eq', "id", engine_id),
                         ('eq', "organization_id", principal["organization_id"])],
            )
            if not response.data:
                raise RuntimeError("No engine was updated")
        except Exception as exc:
            if getattr(exc, "code", None) == "42501":
                logging.getLogger(__name__).warning("Engine visibility update blocked by database access policy")
                message = ("Could not save: the database access policy blocked this change. "
                           "The engine was returned to its previous position. "
                           "Please contact your administrator.")
            else:
                logging.getLogger(__name__).exception("Engine visibility update failed")
                message = "Could not save the change. The engine was returned to its previous position. Please try again."
        else:
            saved = True
            source, destination = (deleted, active) if restoring else (active, deleted)
            engine = next((e for e in source if e["id"] == engine_id), None)
            if engine:
                source.remove(engine)
                engine["is_deleted"] = restoring
                destination.append(engine)
            message = "Engine restored." if restoring else "Engine removed."
            if not restoring:
                # An idle engine should not load the heavy inference libraries.
                import sys
                manager = sys.modules.get("engine_simulation_manager")
                if manager is not None:
                    try:
                        manager.stop_engine_simulation(engine_id)
                        with manager._SENSOR_LOCK:
                            manager._SENSOR_BUFFER.pop(engine_id, None)
                    except Exception:
                        logging.getLogger(__name__).exception("Could not stop removed engine simulation")

        return (
            [engine_table_row(e, i) for i, e in enumerate(active)], active,
            [deleted_engine_table_row(e, i) for i, e in enumerate(deleted)], deleted,
            message, engine_count_summary(active),
            ("Engine restored" if restoring else "Engine removed") if saved else "Change wasn’t saved",
            "success" if saved else "danger", 3500 if saved else None, True,
        )


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

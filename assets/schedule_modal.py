from datetime import datetime, timezone
import dash
from dash import dcc, html, Input, Output, State

# ── shared style helpers ────────────────────────────────────────────────
def _label_style():
    return {
        "color": "rgba(168,212,255,0.8)", "fontSize": "11px", "fontWeight": "600",
        "marginBottom": "5px", "letterSpacing": "0.5px", "display": "block",
    }

def _input_style():
    return {
        "width": "100%", "background": "rgba(13,32,69,0.9)",
        "border": "1px solid rgba(74,158,255,0.25)", "borderRadius": "8px",
        "color": "white", "padding": "10px 14px", "fontSize": "13px",
        "outline": "none", "boxSizing": "border-box",
        "colorScheme": "dark", "accentColor": "#4a9eff",
        "fontFamily": "'Segoe UI', sans-serif",
    }

HIDDEN_OVERLAY_STYLE = {
    "display": "none", "position": "fixed", "top": "0", "left": "0",
    "width": "100vw", "height": "100vh", "background": "rgba(5,12,28,0.80)",
    "zIndex": "1200", "alignItems": "center", "justifyContent": "center",
}
SHOWN_OVERLAY_STYLE = {**HIDDEN_OVERLAY_STYLE, "display": "flex"}

ENGINE_ROW_HIDDEN_STYLE = {"marginBottom": "14px", "display": "none"}
ENGINE_ROW_SHOWN_STYLE  = {"marginBottom": "14px", "display": "block"}

DELETE_BTN_HIDDEN_STYLE = {
    "display": "none",
    "background": "rgba(255,77,77,0.1)", "border": "1px solid rgba(255,77,77,0.4)",
    "borderRadius": "8px", "color": "#ff6b6b", "fontSize": "13px", "fontWeight": "600",
    "padding": "9px 20px", "cursor": "pointer",
}
DELETE_BTN_SHOWN_STYLE = {**DELETE_BTN_HIDDEN_STYLE, "display": "inline-flex"}


# ─────────────────────────────────────────────
#  MODAL
# ─────────────────────────────────────────────
def build_schedule_modal(engine_options=None, *, id_map=None, namespace=None,
                         show_engine=False, show_context=True,
                         edit=False):
    """
    The single "Schedule Maintenance" popup used everywhere.

    `engine_options` seeds the engine dropdown's initial options (only
    relevant on pages that show it, e.g. schedule_maintenance.py's "New"
    flow). Pages that always know the engine (alert_log.py) can omit it —
    the dropdown row stays hidden by default and that page's "open"
    callbacks never touch it.
    """
    ls  = _label_style()
    is_ = _input_style()

    modal = html.Div(
        id="al-sched-modal-overlay",
        style=HIDDEN_OVERLAY_STYLE,
        children=[html.Div(
            style={
                "background": "linear-gradient(135deg,#0d1e3a 0%,#071530 100%)",
                "border": "1px solid rgba(74,158,255,0.25)", "borderRadius": "16px",
                "padding": "24px 28px 28px", "width": "500px", "maxWidth": "94vw",
                "boxShadow": "0 20px 60px rgba(0,0,0,0.6)",
            },
            children=[
                # Title row
                html.Div(style={"display": "flex", "justifyContent": "space-between",
                                "alignItems": "center", "marginBottom": "20px"},
                         children=[
                             html.H3(id="al-sched-modal-title", children="Edit Maintenance Event" if edit else "Schedule Maintenance",
                                     style={"margin": "0", "color": "white",
                                            "fontSize": "16px", "fontWeight": "700"}),
                             html.Span("×", id="al-sched-modal-close", n_clicks=0,
                                       style={"color": "rgba(168,212,255,0.5)", "fontSize": "22px",
                                              "cursor": "pointer", "lineHeight": "1"}),
                         ]),

                # Context info (read-only text — alert summary / engine label).
                # Calendar pages hide this row because they have no alert context.
                html.Div(id="al-sched-modal-context",
                         style={"display": "block" if show_context else "none",
                                "background": "rgba(74,158,255,0.06)",
                                "border": "1px solid rgba(74,158,255,0.15)",
                                "borderRadius": "8px", "padding": "10px 14px",
                                "marginBottom": "18px", "fontSize": "12px",
                                "color": "#a8d4ff"}),

                # Engine dropdown — only relevant when the opener doesn't already
                # know the engine (schedule_maintenance's "New" flow). Hidden by
                # default; the alert-log page never shows or touches this row.
                html.Div(
                    id="al-sched-engine-row",
                    style=ENGINE_ROW_SHOWN_STYLE if show_engine else ENGINE_ROW_HIDDEN_STYLE,
                    children=[
                        html.Label("ENGINE", style=ls),
                        dcc.Dropdown(
                            id="al-sched-engine",
                            options=engine_options or [],
                            placeholder="Select engine…",
                            clearable=False,
                            searchable=False,
                            className="dark-dropdown",
                            style={"fontSize": "13px", "background": "rgba(13,32,69,0.9)",
                                   "border": "1px solid rgba(74,158,255,0.25)", "borderRadius": "8px"},
                        ),
                    ],
                ),

                # Date
                html.Div(style={"marginBottom": "14px"}, children=[
                    html.Label("SCHEDULED DATE", style=ls),
                    dcc.Input(id="al-sched-date", type="date", className="schedule-datetime-input", style=is_),
                ]),

                # Start / End time
                html.Div(style={"display": "flex", "gap": "14px", "marginBottom": "14px"}, children=[
                    html.Div(style={"flex": "1"}, children=[
                        html.Label("START TIME", style=ls),
                        dcc.Input(id="al-sched-start", type="time", className="schedule-datetime-input", value="09:00", style=is_),
                    ]),
                    html.Div(style={"flex": "1"}, children=[
                        html.Label("END TIME", style=ls),
                        dcc.Input(id="al-sched-end", type="time", className="schedule-datetime-input", value="10:00", style=is_),
                    ]),
                ]),

                html.Div(id="al-sched-modal-msg", style={"marginBottom": "10px", "minHeight": "18px"}),

                # Delete (left, hidden unless editing an existing row) | Cancel / Confirm (right)
                html.Div(
                    style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"},
                    children=[
                        html.Button("Delete", id="al-sched-modal-delete", n_clicks=0,
                                    style=DELETE_BTN_SHOWN_STYLE if edit else DELETE_BTN_HIDDEN_STYLE),
                        html.Div(
                            style={"display": "flex", "gap": "10px"},
                            children=[
                                html.Button("Cancel", id="al-sched-modal-cancel", n_clicks=0,
                                            style={"background": "rgba(74,158,255,0.06)",
                                                   "border": "1px solid rgba(74,158,255,0.25)",
                                                   "borderRadius": "8px", "color": "rgba(168,212,255,0.7)",
                                                   "fontSize": "13px", "fontWeight": "600",
                                                   "padding": "9px 20px", "cursor": "pointer"}),
                                html.Button("Save Updated Schedule" if edit else "Confirm Schedule", id="al-sched-modal-confirm", n_clicks=0,
                                            disabled=False,
                                            style={"background": "rgba(74,158,255,0.18)",
                                                   "border": "1px solid rgba(74,158,255,0.55)",
                                                   "borderRadius": "8px", "color": "#7ab8ff",
                                                   "fontSize": "13px", "fontWeight": "700",
                                                   "padding": "9px 22px", "cursor": "pointer",
                                                   "opacity": "1", "transition": "opacity 0.2s"}),
                            ]
                        ),
                    ]
                ),

                # Stores private to the modal — created once here, so pages
                # must NOT declare their own components with these ids.
                dcc.Store(id="al-sched-trigger-store",  data=None),  # dict — see module docstring
                dcc.Store(id="al-sched-original-store", data=None),  # dirty-check baseline
                dcc.Store(id="al-sched-refresh-store",  data=0),     # bumped on every save/delete
            ]
        )]
    )

    # Give each mounted instance its own IDs while retaining one form definition.
    # Pages own their persistence/refresh callbacks; do not also register the
    # optional shared callbacks for those instances.
    def map_ids(component):
        if not isinstance(component, dash.development.base_component.Component):
            return
        component_id = getattr(component, "id", None)
        if component_id:
            component.id = (id_map or {}).get(
                component_id,
                component_id.replace("al-sched", namespace, 1) if namespace else component_id,
            )
        children = getattr(component, "children", None)
        for child in children if isinstance(children, (list, tuple)) else [children]:
            map_ids(child)

    map_ids(modal)
    return modal


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────
# Guards against duplicate-callback-output errors if more than one page's
# register_*_callbacks() calls register_schedule_modal_callbacks() on the
# same Dash `app` (this is expected — both alert_log.py and
# schedule_maintenance.py do it).
_REGISTERED_APPS = set()


def get_responsible_user(supabase, engine_id):
    """Resolve the engine owner for automatic maintenance assignment."""
    response = (supabase.table("engines").select("responsible_by")
                .eq("id", engine_id).single().execute())
    return (response.data or {}).get("responsible_by")


def register_schedule_modal_callbacks(app, supabase=None):
    if id(app) in _REGISTERED_APPS:
        return
    _REGISTERED_APPS.add(id(app))

    # ── Dirty-check / confirm-button label ──────────────────────────────
    @app.callback(
        Output("al-sched-modal-confirm", "disabled", allow_duplicate=True),
        Output("al-sched-modal-confirm", "children", allow_duplicate=True),
        Output("al-sched-modal-confirm", "style",    allow_duplicate=True),
        Input("al-sched-date",           "value"),
        Input("al-sched-start",          "value"),
        Input("al-sched-end",            "value"),
        Input("al-sched-engine",         "value"),
        Input("al-sched-trigger-store",  "data"),
        State("al-sched-original-store", "data"),
        prevent_initial_call=True,
    )
    def update_confirm_button(date_val, start_val, end_val, engine_val, trigger, original):
        btn_enabled = {
            "background": "rgba(74,158,255,0.18)", "border": "1px solid rgba(74,158,255,0.55)",
            "borderRadius": "8px", "color": "#7ab8ff", "fontSize": "13px", "fontWeight": "700",
            "padding": "9px 22px", "cursor": "pointer", "opacity": "1", "transition": "opacity 0.2s",
        }
        btn_disabled = {**btn_enabled, "opacity": "0.35", "cursor": "not-allowed"}

        mode = (trigger or {}).get("mode", "new")

        if mode == "edit":
            orig = original or {}
            is_dirty = (
                (date_val   or "") != (orig.get("date")   or "") or
                (start_val  or "") != (orig.get("start")  or "") or
                (end_val    or "") != (orig.get("end")    or "") or
                (engine_val or "") != (orig.get("engine") or "")
            )
            label = "Save Updated Schedule"
            return (False, label, btn_enabled) if is_dirty else (True, label, btn_disabled)

        label = "Schedule Follow-up" if mode == "followup" else "Confirm Schedule"
        return False, label, btn_enabled

    # ── Confirm → insert/update DB row → bump refresh store ─────────────
    @app.callback(
        Output("al-sched-modal-overlay", "style",    allow_duplicate=True),
        Output("al-sched-modal-msg",     "children", allow_duplicate=True),
        Output("al-sched-refresh-store", "data",     allow_duplicate=True),
        Input("al-sched-modal-confirm",  "n_clicks"),
        State("al-sched-date",           "value"),
        State("al-sched-start",          "value"),
        State("al-sched-end",            "value"),
        State("al-sched-engine",         "value"),
        State("al-sched-trigger-store",  "data"),
        State("session-store",           "data"),
        State("al-sched-refresh-store",  "data"),
        prevent_initial_call=True,
    )
    def confirm_schedule(n_clicks, sel_date, start_time, end_time, engine_val,
                         trigger, session, refresh_count):
        if not sel_date:
            return (dash.no_update,
                    html.Span("Please select a date.", style={"color": "#ff6b6b", "fontSize": "12px"}),
                    dash.no_update)

        trigger      = trigger or {}
        mode         = trigger.get("mode", "new")
        schedule_id  = trigger.get("schedule_db_id")
        engine_db_id = engine_val or trigger.get("engine_db_id")

        if not engine_db_id:
            return (dash.no_update,
                    html.Span("Please select an engine.", style={"color": "#ff6b6b", "fontSize": "12px"}),
                    dash.no_update)

        user_id = (session or {}).get("user_id")

        if supabase:
            try:
                if mode == "edit" and schedule_id:
                    supabase.table("maintenance_schedules").update({
                        "engine_id":      engine_db_id,
                        "scheduled_date": sel_date,
                        "start_time":     start_time or "09:00",
                        "end_time":       end_time or "10:00",
                    }).eq("id", schedule_id).execute()
                else:
                    existing_sched = None
                    try:
                        ex_resp = (
                            supabase.table("maintenance_schedules")
                            .select("id")
                            .eq("engine_id", engine_db_id)
                            .not_.in_("status", ["completed", "cancelled"])
                            .order("created_at", desc=True)
                            .limit(1)
                            .execute()
                        )
                        if ex_resp.data:
                            existing_sched = ex_resp.data[0]
                    except Exception as _e:
                        print(f"[SCHED-MODAL] check existing schedule: {_e}")

                    if existing_sched:
                        schedule_id = existing_sched["id"]
                        supabase.table("maintenance_schedules").update({
                            "scheduled_date": sel_date,
                            "start_time":     start_time or "09:00",
                            "end_time":       end_time or "10:00",
                        }).eq("id", schedule_id).execute()
                    else:
                        responsible_user_id = get_responsible_user(supabase, engine_db_id)

                        result = supabase.table("maintenance_schedules").insert({
                            "engine_id":      engine_db_id,
                            "scheduled_date": sel_date,
                            "start_time":     start_time or "09:00",
                            "end_time":       end_time or "10:00",
                            "status":         "scheduled",
                            "created_by":     user_id,
                            "assigned_to":    responsible_user_id,
                        }).execute()
                        if result.data:
                            schedule_id = result.data[0]["id"]

                    # Link every alert for this engine to the schedule.
                    if schedule_id and engine_db_id:
                        try:
                            engine_alerts_resp = supabase.table("alert_logs") \
                                .select("id").eq("engine_id", engine_db_id).execute()
                            engine_alert_ids = [r["id"] for r in (engine_alerts_resp.data or [])]
                            if engine_alert_ids:
                                linked_resp = supabase.table("maintenance_alerts") \
                                    .select("alert_id").in_("alert_id", engine_alert_ids).execute()
                                linked_ids = {r["alert_id"] for r in (linked_resp.data or [])}
                                rows_to_insert = [
                                    {"maintenance_schedule_id": schedule_id, "alert_id": aid}
                                    for aid in engine_alert_ids if aid not in linked_ids
                                ]
                                if rows_to_insert:
                                    supabase.table("maintenance_alerts").insert(rows_to_insert).execute()
                        except Exception as _e:
                            print(f"[SCHED-MODAL] maintenance_alerts mapping: {_e}")
            except Exception as _e:
                print(f"[SCHED-MODAL] confirm_schedule DB error: {_e}")
                return (dash.no_update,
                        html.Span("Save failed. Please try again.",
                                  style={"color": "#ff6b6b", "fontSize": "12px"}),
                        dash.no_update)

        return HIDDEN_OVERLAY_STYLE, "", (refresh_count or 0) + 1

    # ── Delete (only meaningful when editing an existing row) ───────────
    @app.callback(
        Output("al-sched-modal-overlay", "style", allow_duplicate=True),
        Output("al-sched-refresh-store", "data",  allow_duplicate=True),
        Input("al-sched-modal-delete",   "n_clicks"),
        State("al-sched-trigger-store",  "data"),
        State("al-sched-refresh-store",  "data"),
        prevent_initial_call=True,
    )
    def delete_schedule(n_clicks, trigger, refresh_count):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        schedule_id = (trigger or {}).get("schedule_db_id")
        if supabase and schedule_id:
            try:
                supabase.table("maintenance_schedules").delete().eq("id", schedule_id).execute()
            except Exception as _e:
                print(f"[SCHED-MODAL] delete failed: {_e}")
        return HIDDEN_OVERLAY_STYLE, (refresh_count or 0) + 1

    # ── Close (Cancel / ×) ───────────────────────────────────────────────
    @app.callback(
        Output("al-sched-modal-overlay", "style", allow_duplicate=True),
        Input("al-sched-modal-cancel",   "n_clicks"),
        Input("al-sched-modal-close",    "n_clicks"),
        prevent_initial_call=True,
    )
    def close_sched_modal(cancel, close):
        return HIDDEN_OVERLAY_STYLE
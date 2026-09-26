"""Shared floating simulation controls for engine-specific pages."""
from dash import html, dcc, Input, Output, State, ctx
from simulation_clock import SPEEDS, DEFAULT_SPEED


ENGINE_PAGES = {"overview", "sensor-trends", "degradation-analysis", "alert-log"}


def selected_simulation_engine(pathname, session):
    parts = (pathname or "").strip("/").split("/")
    if (not (session or {}).get("organization_id")
            or (session or {}).get("must_change_password")
            or len(parts) != 2 or parts[0] not in ENGINE_PAGES or not parts[1]):
        return None
    return parts[1]


def build_simulation_panel():
    return html.Div(id="simulation-widget", hidden=True, children=[
        dcc.Interval(id="simulation-control-poll", interval=2000, disabled=True),
        html.Details(id="simulation-widget-details", open=False, children=[
            html.Summary([
                html.Span("⠿", className="simulation-drag-handle", tabIndex=0,
                          role="button", title="Drag to move; arrow keys also move the panel",
                          **{"aria-label": "Move simulation panel"}),
                html.Span("Simulation", className="simulation-widget-title"),
                html.Span("⌄", className="simulation-chevron"),
            ], title="Expand or collapse simulation controls"),
            html.Div(className="simulation-widget-body", children=[
                html.Div(id="simulation-state", role="status"),
                html.Label("Choose speed", htmlFor="simulation-speed"),
                dcc.Dropdown(id="simulation-speed", options=[
                    {"label": label, "value": speed} for speed, label in SPEEDS.items()
                ], value=DEFAULT_SPEED, clearable=False, searchable=False,
                    optionHeight=42, maxHeight=200, className="simulation-speed-select"),
                html.Div(className="simulation-actions", children=[
                    html.Button("Apply speed", id="simulation-apply", n_clicks=0),
                    html.Button("Pause", id="simulation-pause", n_clicks=0),
                    html.Button("Resume", id="simulation-resume", n_clicks=0),
                ]),
                html.Button("Toggle automatic slowdown", id="simulation-auto", n_clicks=0),
                html.Div(id="simulation-feedback", role="status"),
                html.Small("1× = 8 hours/cycle · 21 cycles/week. Critical alerts do not pause. "
                           "Pause finishes the current processing cycle. Settings affect this engine "
                           "for all viewers and reset on server restart."),
            ]),
        ]),
    ])


def register_simulation_callbacks(app, supabase):
    @app.callback(
        Output("simulation-widget", "hidden"),
        Output("simulation-control-poll", "disabled"),
        Input("url", "pathname"), Input("session-store", "data"),
    )
    def show_simulation(pathname, session):
        visible = selected_simulation_engine(pathname, session) is not None
        return not visible, not visible

    @app.callback(
        Output("simulation-state", "children"),
        Output("simulation-feedback", "children"),
        Output("simulation-apply", "disabled"),
        Output("simulation-pause", "disabled"),
        Output("simulation-resume", "disabled"),
        Output("simulation-auto", "disabled"),
        Input("simulation-control-poll", "n_intervals"),
        Input("simulation-apply", "n_clicks"),
        Input("simulation-pause", "n_clicks"),
        Input("simulation-resume", "n_clicks"),
        Input("simulation-auto", "n_clicks"),
        Input("url", "pathname"),
        Input("session-store", "data"),
        State("simulation-speed", "value"),
    )
    def control_simulation(_poll, _apply, _pause, _resume, _auto, pathname, session, speed):
        engine_id = selected_simulation_engine(pathname, session)
        from dash import no_update
        from engine_simulation_manager import get_simulation_state, configure_simulation
        # Match the application's organization scope before reading or changing a runner.
        org_id = (session or {}).get("organization_id")
        if not org_id or not engine_id or supabase is None:
            return "Simulation controls unavailable.", "", True, True, True, True
        try:
            result = supabase.table("engines").select("id, engine_id").eq("id", engine_id).eq(
                "organization_id", org_id).execute()
            if not result.data:
                return "Simulation controls unavailable.", "", True, True, True, True
        except Exception:
            return "Unable to verify engine access.", "", True, True, True, True
        state = get_simulation_state(engine_id)
        if not state or not state["running"]:
            return "Simulation inactive or completed.", "", True, True, True, True
        action = ctx.triggered_id
        changes = {}
        if action == "simulation-apply":
            if speed not in SPEEDS:
                return "Invalid speed.", "Choose a listed speed.", False, False, False, False
            changes = {"speed": speed}
        elif action == "simulation-pause":
            changes = {"paused": True}
        elif action == "simulation-resume":
            changes = {"paused": False}
        elif action == "simulation-auto":
            changes = {"auto_slow": not state["auto_slow"]}
        feedback = "" if action in ("url", "session-store") else no_update
        if changes:
            updated = configure_simulation(engine_id, **changes)
            feedback = "Simulation updated." if updated else "Simulation has finished."
            state = get_simulation_state(engine_id) or state
        label = "Paused" if state["paused"] else "Running"
        auto = "on" if state["auto_slow"] else "off"
        summary = (f"Engine {result.data[0].get('engine_id', engine_id)} · {label} · Cycle {state['cycle']} · {state['condition'].title()} · "
                   f"Active speed: {SPEEDS[state['speed']]} · Automatic slowdown: {auto}. "
                   f"{state['note']}")
        return summary, feedback, False, state["paused"], not state["paused"], False

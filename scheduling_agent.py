"""Independent floating Scheduling Agent UI and callbacks."""
import dash
from dash import html, dcc, Input, Output, State, ctx


def render_message(role, content):
    is_agent = role == "assistant"
    return html.Div([
        html.Div([
            html.Span("✦" if is_agent else "●", className="sa-message-icon", **{"aria-hidden": "true"}),
            html.Span("Scheduling Agent" if is_agent else "You"),
        ], className="sa-message-author"),
        dcc.Markdown(str(content), className="sa-message-content", dangerously_allow_html=False)
        if is_agent else html.Div(str(content), className="sa-user-content"),
    ], className="sa-message sa-" + ("assistant" if is_agent else "user"))


def build_scheduling_agent(engine_options, engine_id=None):
    return html.Div(id="scheduling-agent-widget", children=[
        dcc.Store(id="sa-history", data=[]),
        html.Details(open=False, children=[
            html.Summary([
                html.Span("✦", className="sa-drag-handle", role="button", tabIndex=0,
                          title="Drag to move · Arrow keys to reposition", **{"aria-label": "Move Scheduling Agent"}),
                html.Span("Scheduling Agent", className="sa-title"),
                html.Span("⌄", className="sa-chevron"),
            ]),
            html.Div(className="sa-body", children=[
                html.Label("Engine", htmlFor="sa-engine"),
                dcc.Dropdown(id="sa-engine", options=engine_options, value=engine_id,
                             searchable=False, clearable=False, placeholder="Select an engine"),
                html.P("Find a two-hour slot with the responsible technician. All times are Malaysia time.", className="sa-hint"),
                dcc.Loading(html.Div(id="sa-messages", role="log", **{"aria-live": "polite"}, children=[
                    render_message("assistant", "How can I help you plan maintenance?\n\nTry **“Find an afternoon slot next week.”**")
                ]), type="dot", color="#76baff"),
                html.Label("Your message", htmlFor="sa-input"),
                dcc.Textarea(id="sa-input", placeholder="Find an afternoon slot next week…", maxLength=1500),
                html.Button("Send", id="sa-send", n_clicks=0),
                html.Label("Available slots", htmlFor="sa-choice"),
                dcc.Dropdown(id="sa-choice", options=[], searchable=False, clearable=False,
                             placeholder="Ask for a recommendation"),
                html.Button("Use selected slot", id="sa-use", n_clicks=0),
                html.Div(id="sa-feedback", role="status"),
                html.Small("Use selected slot saves the booking directly to your maintenance calendar."),
            ]),
        ]),
    ])


def register_scheduling_agent(app, sb):
    @app.callback(
        Output("sa-messages", "children"), Output("sa-history", "data"),
        Output("sa-choice", "options"), Output("sa-choice", "value"), Output("sa-input", "value"),
        Input("sa-send", "n_clicks"), Input("sa-engine", "value"),
        State("sa-input", "value"), State("sa-history", "data"), State("session-store", "data"),
        prevent_initial_call=True,
        running=[(Output("sa-send", "disabled"), True, False),
                 (Output("sa-engine", "disabled"), True, False),
                 (Output("sa-use", "disabled"), True, False)],
    )
    def send(_clicks, engine_id, message, history, session):
        if ctx.triggered_id == "sa-engine":
            return [render_message("assistant", "Ready to plan for this engine. Ask for a day or a preferred time.")], [], [], None, ""
        if not message or not message.strip():
            raise dash.exceptions.PreventUpdate
        from scheduling_agent_service import chat
        history = [h for h in (history or [])[-10:] if isinstance(h, dict) and h.get("role") in ("user", "assistant")]
        try:
            reply, options = chat(sb, engine_id, session, message, history)
        except ValueError as exc:
            reply, options = str(exc), []
        except Exception:
            reply, options = "The Scheduling Agent is temporarily unavailable. Please try again or use the New schedule form.", []
        history = history + [{"role": "user", "content": message[:1500]}, {"role": "assistant", "content": reply}]
        history = history[-12:]
        bubbles = [render_message(h["role"], h.get("content", ""))
                   for h in history]
        return bubbles, history, options, options[0]["value"] if options else None, ""

    @app.callback(
        Output("sm-events-store", "data", allow_duplicate=True),
        Output("sm-calendar-container", "children", allow_duplicate=True),
        Output("sm-week-offset-store", "data", allow_duplicate=True),
        Output("sm-week-nav-container", "children", allow_duplicate=True),
        Output("sa-feedback", "children"),
        Input("sa-use", "n_clicks"), State("sa-choice", "value"), State("sa-engine", "value"),
        State("session-store", "data"), State("sm-events-store", "data"),
        prevent_initial_call=True,
        running=[(Output("sa-use", "disabled"), True, False)],
    )
    def use_slot(clicks, token, engine_id, session, events):
        if not clicks:
            raise dash.exceptions.PreventUpdate
        from scheduling_agent_service import book_choice
        from itsdangerous import BadSignature
        from datetime import date
        from schedule_maintenance import _build_calendar, _build_week_nav
        try:
            if not token:
                raise ValueError("Ask for a recommendation and select a slot first.")
            event, message = book_choice(sb, token, engine_id, session)
            updated = [e for e in (events or []) if e.get("db_id") != event["db_id"]] + [event]
            booked_day = date.fromisoformat(event["date"])
            today = date.today()
            offset = ((booked_day.toordinal() - booked_day.weekday()) -
                      (today.toordinal() - today.weekday())) // 7
            return updated, [_build_calendar(updated, offset)], offset, [_build_week_nav(offset)], message
        except (ValueError, BadSignature) as exc:
            return (dash.no_update,) * 4 + (str(exc) if isinstance(exc, ValueError) else "The proposal expired. Please request a new one.",)
        except Exception:
            return (dash.no_update,) * 4 + ("Unable to confirm the booking. Refresh the calendar or retry; repeated clicks won't create duplicates.",)

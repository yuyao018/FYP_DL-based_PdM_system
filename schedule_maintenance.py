"""
schedule_maintenance.py
────────────────────────
Schedule Maintenance page.

Layout
──────
  • Sidebar + topbar (consistent with the rest of the app)
  • Header row: "Maintenance Schedule" title  |  "New +" button  (space-between)
  • Weekly calendar table: columns = time slots, rows = days (Mon–Sun)
    - Each cell can hold one or more scheduled maintenance events
  • Modal (centre-screen overlay): engine dropdown, date, start/end time, notes
    - Cancel / Schedule buttons aligned to the right
  • On submit the calendar updates to show the event in the correct day/time cell
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc
from datetime import date, datetime, timedelta
from assets.components import build_topbar
import json as _json

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

# Working hours only: 08:00 – 19:00
HOURS = [f"{h:02d}:00" for h in range(8, 20)]


def _week_dates(offset: int = 0) -> list[date]:
    """Return Mon–Sun dates for the week at `offset` weeks from today."""
    today = date.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    return [monday + timedelta(days=i) for i in range(7)]


def _week_label(offset: int = 0) -> str:
    """Return a label like '24–28 August, 2026'."""
    dates = _week_dates(offset)
    mon, fri = dates[0], dates[4]
    if mon.month == fri.month:
        return f"{mon.day}–{fri.day} {fri.strftime('%B, %Y')}"
    return f"{mon.day} {mon.strftime('%b')} – {fri.day} {fri.strftime('%b, %Y')}"

ROW_HEIGHT = 56  # px per hour slot — used for rowspan height calculation

_STATUS_COLORS = {
    "critical": "#ff4d4d",
    "warning":  "#ffd93d",
    "healthy":  "#00c875",
}

# ─────────────────────────────────────────────
#  CALENDAR BUILDER
# ─────────────────────────────────────────────

def _build_calendar(events: list[dict], offset: int = 0) -> html.Div:
    """
    Build a weekly calendar table.
    """
    week_dates = _week_dates(offset)
    today = date.today()

    # Index events by (day, hour) — only for the currently displayed week
    week_date_map = {d.isoformat(): DAYS[i] for i, d in enumerate(week_dates[:5])}
    event_map: dict[tuple, list] = {}
    for ev in (events or []):
        ev_date = ev.get("date", "")
        ev_day  = week_date_map.get(ev_date) or ev.get("day")
        if ev_day not in DAYS:
            continue
        # Only show events whose date falls in this week
        if ev_date and ev_date not in week_date_map:
            continue
        key = (ev_day, ev.get("hour"))
        event_map.setdefault(key, []).append(ev)

    # ── Header row — show "Mon\n24 Aug" style ──
    header_cells = [
        html.Th(
            "",
            style={
                "width": "52px", "minWidth": "52px",
                "padding": "10px 6px",
                "borderBottom": "1px solid rgba(74,158,255,0.15)",
                "background": "rgba(13,30,58,0.97)",
                "position": "sticky", "top": "0", "zIndex": "3",
            }
        )
    ]
    for day_name, day_date in zip(DAYS, week_dates):
        is_today = day_date == today
        header_cells.append(
            html.Th(
                children=[
                    html.Div(
                        day_name,
                        style={
                            "fontSize": "11px",
                            "fontWeight": "600",
                            "color": "#4a9eff" if is_today else "rgba(168,212,255,0.6)",
                            "letterSpacing": "0.5px",
                            "marginBottom": "2px",
                        }
                    ),
                    html.Div(
                        day_date.strftime("%d %b").lstrip("0") if hasattr(day_date, "strftime") else str(day_date),
                        style={
                            "fontSize": "15px",
                            "fontWeight": "700",
                            "color": "white" if not is_today else "#4a9eff",
                            "background": "rgba(74,158,255,0.18)" if is_today else "transparent",
                            "borderRadius": "6px",
                            "padding": "2px 6px",
                            "display": "inline-block",
                        }
                    ),
                ],
                style={
                    "padding": "8px 8px",
                    "textAlign": "center",
                    "borderBottom": "1px solid rgba(74,158,255,0.15)",
                    "borderLeft": "1px solid rgba(74,158,255,0.08)",
                    "background": "rgba(13,30,58,0.97)",
                    "position": "sticky", "top": "0", "zIndex": "3",
                    "minWidth": "110px",
                }
            )
        )

    # ── Precompute row spans ──
    # For each (day, start_hour) determine how many rows the event spans
    # based on start_time → end_time, capped at available rows.
    def _span(start_t: str, end_t: str) -> int:
        """Number of hour rows an event occupies (min 1)."""
        try:
            sh, sm_ = int(start_t[:2]), int(start_t[3:5])
            eh, em  = int(end_t[:2]),   int(end_t[3:5])
            minutes = (eh * 60 + em) - (sh * 60 + sm_)
            return max(1, -(-minutes // 60))  # ceil division
        except Exception:
            return 1

    # Track which (day, hour_index) cells are already consumed by a rowspan
    # consumed[(day, hour_idx)] = True
    consumed: dict[tuple, bool] = {}

    # ── Body rows (one per hour slot) ──
    body_rows = []
    for h_idx, hour in enumerate(HOURS):
        cells = [
            html.Td(
                hour,
                style={
                    "padding": "6px 8px",
                    "color": "rgba(168,212,255,0.55)",
                    "fontSize": "11px", "fontWeight": "600",
                    "borderBottom": "1px solid rgba(74,158,255,0.07)",
                    "whiteSpace": "nowrap",
                    "verticalAlign": "top",
                    "background": "rgba(10,22,40,0.8)",
                    "position": "sticky", "left": "0", "zIndex": "1",
                    "width": "52px", "minWidth": "52px",
                    "height": f"{ROW_HEIGHT}px",
                }
            )
        ]
        for day in DAYS:
            # Skip if this cell is consumed by a previous rowspan
            if consumed.get((day, h_idx)):
                continue

            slot_events = event_map.get((day, hour), [])
            cell_children = []
            row_span = 1

            for ev_idx, ev in enumerate(slot_events):
                color = _STATUS_COLORS.get(ev.get("status", "healthy"), "#4a9eff")
                ev_key = ev.get("_idx", f"{day}-{hour}-{ev_idx}")

                # Calculate span for the first event (events are stacked in same cell)
                span = _span(ev.get("start_time", hour), ev.get("end_time", hour))
                # Cap span so it doesn't exceed remaining rows
                span = min(span, len(HOURS) - h_idx)
                row_span = max(row_span, span)

                # Calculate exact pixel height from actual start→end minutes
                try:
                    sh, sm_ = int(ev.get("start_time","00:00")[:2]), int(ev.get("start_time","00:00")[3:5])
                    eh, em  = int(ev.get("end_time","00:00")[:2]),   int(ev.get("end_time","00:00")[3:5])
                    duration_min = (eh * 60 + em) - (sh * 60 + sm_)
                    card_height = max(int(duration_min * ROW_HEIGHT / 60) - 6, ROW_HEIGHT - 6)
                except Exception:
                    card_height = ROW_HEIGHT * span - 6

                cell_children.append(
                    html.Div(
                        id={"type": "sm-event-card", "index": ev_key},
                        n_clicks=0,
                        children=[
                            html.Div(
                                ev.get("label", "Maintenance"),
                                style={
                                    "fontWeight": "700",
                                    "fontSize": "12px",
                                    "color": "white",
                                    "marginBottom": "4px",
                                    "overflow": "hidden",
                                    "textOverflow": "ellipsis",
                                    "whiteSpace": "nowrap",
                                }
                            ),
                            html.Div(
                                f"{ev.get('start_time', '')} – {ev.get('end_time', '')}",
                                style={
                                    "fontSize": "10px",
                                    "color": "rgba(255,255,255,0.65)",
                                }
                            ),
                        ],
                        style={
                            "background": f"rgba({_hex_to_rgb(color)}, 0.20)",
                            "border": f"1px solid {color}",
                            "borderLeft": f"3px solid {color}",
                            "borderRadius": "6px",
                            "padding": "8px 10px",
                            "width": "100%",
                            "height": f"{card_height}px",
                            "boxSizing": "border-box",
                            "overflow": "hidden",
                            "cursor": "pointer",
                        }
                    )
                )

            # Mark subsequent rows as consumed
            if row_span > 1:
                for offset in range(1, row_span):
                    if h_idx + offset < len(HOURS):
                        consumed[(day, h_idx + offset)] = True

            cells.append(
                html.Td(
                    cell_children if cell_children else "",
                    rowSpan=row_span,
                    style={
                        "padding": "3px 4px",
                        "borderBottom": "1px solid rgba(74,158,255,0.07)",
                        "borderLeft": "1px solid rgba(74,158,255,0.08)",
                        "verticalAlign": "top",
                    }
                )
            )
        body_rows.append(html.Tr(cells))

    return html.Div(
        style={
            "flex": "1",
            "minHeight": "0",
            "overflowY": "auto",
            "overflowX": "hidden",
            "borderRadius": "12px",
            "border": "1px solid rgba(74,158,255,0.15)",
        },
        children=[
            html.Table(
                style={
                    "width": "100%",
                    "borderCollapse": "collapse",
                    "background": "rgba(10,22,40,0.5)",
                    "tableLayout": "fixed",
                },
                children=[
                    html.Thead(html.Tr(header_cells)),
                    html.Tbody(body_rows),
                ]
            )
        ]
    )


def _hex_to_rgb(hex_color: str) -> str:
    """Convert #rrggbb to 'r,g,b' string for rgba()."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r},{g},{b}"
    return "74,158,255"


# ─────────────────────────────────────────────
#  MODAL
# ─────────────────────────────────────────────

def _build_modal(engine_options: list[dict]) -> html.Div:
    """
    Centre-screen modal overlay for creating a new maintenance event.
    Hidden by default (display: none on the outer wrapper).
    """
    input_style = {
        "width": "100%",
        "background": "rgba(13,32,69,0.9)",
        "border": "1px solid rgba(74,158,255,0.25)",
        "borderRadius": "8px",
        "color": "white",
        "padding": "10px 14px",
        "fontSize": "13px",
        "outline": "none",
        "boxSizing": "border-box",
        "fontFamily": "'Segoe UI', sans-serif",
    }
    label_style = {
        "color": "rgba(168,212,255,0.8)",
        "fontSize": "11px",
        "fontWeight": "600",
        "marginBottom": "5px",
        "letterSpacing": "0.5px",
        "display": "block",
    }

    return html.Div(
        id="sm-modal-overlay",
        style={
            "display": "none",
            "position": "fixed",
            "top": "0", "left": "0",
            "width": "100vw", "height": "100vh",
            "background": "rgba(5,12,28,0.75)",
            "zIndex": "1000",
            "alignItems": "center",
            "justifyContent": "center",
        },
        children=[
            html.Div(
                style={
                    "background": "linear-gradient(135deg, #0d1e3a 0%, #071530 100%)",
                    "border": "1px solid rgba(74,158,255,0.25)",
                    "borderRadius": "16px",
                    "padding": "16px 32px 28px",
                    "width": "480px",
                    "maxWidth": "92vw",
                    "boxShadow": "0 20px 60px rgba(0,0,0,0.6)",
                },
                children=[
                    # Modal title
                    html.Div(
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "space-between",
                            "marginBottom": "22px",
                        },
                        children=[
                            html.H3(
                                "New Maintenance Event",
                                style={
                                    "margin": "0",
                                    "color": "white",
                                    "fontSize": "16px",
                                    "fontWeight": "700",
                                }
                            ),
                            # Close × button
                            html.Span(
                                "×",
                                id="sm-modal-close",
                                n_clicks=0,
                                style={
                                    "color": "rgba(168,212,255,0.5)",
                                    "fontSize": "22px",
                                    "cursor": "pointer",
                                    "lineHeight": "1",
                                    "padding": "0 4px",
                                }
                            ),
                        ]
                    ),

                    # Engine selection
                    html.Div(style={"marginBottom": "16px"}, children=[
                        html.Label("ENGINE", style=label_style),
                        dcc.Dropdown(
                            id="sm-modal-engine",
                            options=engine_options,
                            placeholder="Select engine…",
                            clearable=False,
                            className="dark-dropdown",
                            style={
                                "fontSize": "13px",
                                "background": "rgba(13,32,69,0.9)",
                                "border": "1px solid rgba(74,158,255,0.25)",
                                "borderRadius": "8px",
                            },
                        ),
                    ]),

                    # Date
                    html.Div(style={"marginBottom": "16px"}, children=[
                        html.Label("DATE", style=label_style),
                        dcc.Input(
                            id="sm-modal-date",
                            type="date",
                            min=date.today().isoformat(),
                            style={
                                **input_style,
                                "colorScheme": "dark",
                            },
                        ),
                    ]),

                    # Start time / End time row
                    html.Div(
                        style={"display": "flex", "gap": "14px", "marginBottom": "16px"},
                        children=[
                            html.Div(style={"flex": "1"}, children=[
                                html.Label("START TIME", style=label_style),
                                dcc.Input(
                                    id="sm-modal-start-time",
                                    type="time",
                                    value="09:00",
                                    style=input_style,
                                ),
                            ]),
                            html.Div(style={"flex": "1"}, children=[
                                html.Label("END TIME", style=label_style),
                                dcc.Input(
                                    id="sm-modal-end-time",
                                    type="time",
                                    value="10:00",
                                    style=input_style,
                                ),
                            ]),
                        ]
                    ),

                    # Notes
                    html.Div(style={"marginBottom": "24px"}, children=[
                        html.Label("NOTES", style=label_style),
                        dcc.Textarea(
                            id="sm-modal-notes",
                            placeholder="Optional notes or instructions…",
                            style={
                                **input_style,
                                "height": "80px",
                                "resize": "vertical",
                            },
                        ),
                    ]),

                    # Validation message
                    html.Div(id="sm-modal-validation", style={"marginBottom": "10px", "minHeight": "18px"}),

                    # Cancel / Schedule buttons — right-aligned
                    html.Div(
                        style={
                            "display": "flex",
                            "justifyContent": "flex-end",
                            "gap": "10px",
                        },
                        children=[
                            html.Button(
                                "Cancel",
                                id="sm-modal-cancel",
                                n_clicks=0,
                                style={
                                    "background": "rgba(74,158,255,0.06)",
                                    "border": "1px solid rgba(74,158,255,0.25)",
                                    "borderRadius": "8px",
                                    "color": "rgba(168,212,255,0.7)",
                                    "fontSize": "13px",
                                    "fontWeight": "600",
                                    "padding": "9px 20px",
                                    "cursor": "pointer",
                                }
                            ),
                            html.Button(
                                "Schedule",
                                id="sm-modal-schedule",
                                n_clicks=0,
                                style={
                                    "background": "rgba(74,158,255,0.18)",
                                    "border": "1px solid rgba(74,158,255,0.55)",
                                    "borderRadius": "8px",
                                    "color": "#7ab8ff",
                                    "fontSize": "13px",
                                    "fontWeight": "700",
                                    "padding": "9px 22px",
                                    "cursor": "pointer",
                                }
                            ),
                        ]
                    ),
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  WEEK NAVIGATION BAR
# ─────────────────────────────────────────────

def _build_week_nav(offset: int = 0) -> html.Div:
    """Today button, prev/next arrows, week range label."""
    label = _week_label(offset)
    return html.Div(
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "4px",
            "marginBottom": "14px",
        },
        children=[
            # Today button
            html.Button(
                children=[
                    html.Span("⊟", style={"fontSize": "14px", "marginRight": "6px",
                                          "color": "rgba(168,212,255,0.7)"}),
                    "Today",
                ],
                id="sm-nav-today",
                n_clicks=0,
                style={
                    "display": "flex", "alignItems": "center",
                    "background": "rgba(74,158,255,0.10)",
                    "border": "1px solid rgba(74,158,255,0.3)",
                    "borderRadius": "8px",
                    "color": "rgba(168,212,255,0.85)",
                    "fontSize": "13px", "fontWeight": "600",
                    "padding": "6px 14px",
                    "cursor": "pointer",
                    "marginRight": "4px",
                }
            ),
            # Prev arrow
            html.Button(
                "‹",
                id="sm-nav-prev",
                n_clicks=0,
                style={
                    "background": "rgba(74,158,255,0.08)",
                    "border": "1px solid rgba(74,158,255,0.25)",
                    "borderRadius": "6px",
                    "color": "rgba(168,212,255,0.8)",
                    "fontSize": "18px", "lineHeight": "1",
                    "padding": "4px 10px",
                    "cursor": "pointer",
                }
            ),
            # Next arrow
            html.Button(
                "›",
                id="sm-nav-next",
                n_clicks=0,
                style={
                    "background": "rgba(74,158,255,0.08)",
                    "border": "1px solid rgba(74,158,255,0.25)",
                    "borderRadius": "6px",
                    "color": "rgba(168,212,255,0.8)",
                    "fontSize": "18px", "lineHeight": "1",
                    "padding": "4px 10px",
                    "cursor": "pointer",
                    "marginRight": "8px",
                }
            ),
            # Week range label
            html.Span(
                label,
                id="sm-week-label",
                style={
                    "color": "white",
                    "fontSize": "15px",
                    "fontWeight": "700",
                    "letterSpacing": "0.3px",
                }
            ),
        ]
    )


# ─────────────────────────────────────────────
#  EDIT / DELETE MODAL
# ─────────────────────────────────────────────

def _build_edit_modal(engine_options: list[dict]) -> html.Div:
    """Modal for viewing, editing, or deleting an existing scheduled event."""
    input_style = {
        "width": "100%",
        "background": "rgba(13,32,69,0.9)",
        "border": "1px solid rgba(74,158,255,0.25)",
        "borderRadius": "8px",
        "color": "white",
        "padding": "10px 14px",
        "fontSize": "13px",
        "outline": "none",
        "boxSizing": "border-box",
        "fontFamily": "'Segoe UI', sans-serif",
    }
    label_style = {
        "color": "rgba(168,212,255,0.8)",
        "fontSize": "11px",
        "fontWeight": "600",
        "marginBottom": "5px",
        "letterSpacing": "0.5px",
        "display": "block",
    }

    return html.Div(
        id="sm-edit-modal-overlay",
        style={
            "display": "none",
            "position": "fixed",
            "top": "0", "left": "0",
            "width": "100vw", "height": "100vh",
            "background": "rgba(5,12,28,0.75)",
            "zIndex": "1000",
            "alignItems": "center",
            "justifyContent": "center",
        },
        children=[
            html.Div(
                style={
                    "background": "linear-gradient(135deg, #0d1e3a 0%, #071530 100%)",
                    "border": "1px solid rgba(74,158,255,0.25)",
                    "borderRadius": "16px",
                    "padding": "28px 32px",
                    "width": "480px",
                    "maxWidth": "92vw",
                    "boxShadow": "0 20px 60px rgba(0,0,0,0.6)",
                },
                children=[
                    # Title row
                    html.Div(
                        style={"display": "flex", "alignItems": "center",
                               "justifyContent": "space-between", "marginBottom": "22px"},
                        children=[
                            html.H3("Edit Maintenance Event",
                                    style={"margin": "0", "color": "white",
                                           "fontSize": "16px", "fontWeight": "700"}),
                            html.Span("×", id="sm-edit-modal-close", n_clicks=0,
                                      style={"color": "rgba(168,212,255,0.5)", "fontSize": "22px",
                                             "cursor": "pointer", "lineHeight": "1", "padding": "0 4px"}),
                        ]
                    ),

                    # Engine (read-only display)
                    html.Div(style={"marginBottom": "16px"}, children=[
                        html.Label("ENGINE", style=label_style),
                        dcc.Dropdown(
                            id="sm-edit-engine",
                            options=engine_options,
                            clearable=False,
                            className="dark-dropdown",
                            style={"fontSize": "13px", "background": "rgba(13,32,69,0.9)",
                                   "border": "1px solid rgba(74,158,255,0.25)", "borderRadius": "8px"},
                        ),
                    ]),

                    # Date
                    html.Div(style={"marginBottom": "16px"}, children=[
                        html.Label("DATE", style=label_style),
                        dcc.Input(id="sm-edit-date", type="date",
                                  min=date.today().isoformat(),
                                  style={**input_style, "colorScheme": "dark"}),
                    ]),

                    # Start / End time
                    html.Div(
                        style={"display": "flex", "gap": "14px", "marginBottom": "16px"},
                        children=[
                            html.Div(style={"flex": "1"}, children=[
                                html.Label("START TIME", style=label_style),
                                dcc.Input(id="sm-edit-start-time", type="time",
                                          style={**input_style, "colorScheme": "dark"}),
                            ]),
                            html.Div(style={"flex": "1"}, children=[
                                html.Label("END TIME", style=label_style),
                                dcc.Input(id="sm-edit-end-time", type="time",
                                          style={**input_style, "colorScheme": "dark"}),
                            ]),
                        ]
                    ),

                    # Notes
                    html.Div(style={"marginBottom": "24px"}, children=[
                        html.Label("NOTES", style=label_style),
                        dcc.Textarea(id="sm-edit-notes",
                                     style={**input_style, "height": "80px", "resize": "vertical"}),
                    ]),

                    html.Div(id="sm-edit-modal-validation",
                             style={"marginBottom": "10px", "minHeight": "18px"}),

                    # Delete | Cancel + Save row
                    html.Div(
                        style={"display": "flex", "justifyContent": "space-between",
                               "alignItems": "center"},
                        children=[
                            # Delete on the left
                            html.Button(
                                "Delete",
                                id="sm-edit-delete-btn",
                                n_clicks=0,
                                style={
                                    "background": "rgba(255,77,77,0.1)",
                                    "border": "1px solid rgba(255,77,77,0.4)",
                                    "borderRadius": "8px",
                                    "color": "#ff6b6b",
                                    "fontSize": "13px", "fontWeight": "600",
                                    "padding": "9px 20px", "cursor": "pointer",
                                }
                            ),
                            # Cancel + Save on the right
                            html.Div(
                                style={"display": "flex", "gap": "10px"},
                                children=[
                                    html.Button(
                                        "Cancel",
                                        id="sm-edit-cancel-btn",
                                        n_clicks=0,
                                        style={
                                            "background": "rgba(74,158,255,0.06)",
                                            "border": "1px solid rgba(74,158,255,0.25)",
                                            "borderRadius": "8px",
                                            "color": "rgba(168,212,255,0.7)",
                                            "fontSize": "13px", "fontWeight": "600",
                                            "padding": "9px 20px", "cursor": "pointer",
                                        }
                                    ),
                                    html.Button(
                                        "Save",
                                        id="sm-edit-save-btn",
                                        n_clicks=0,
                                        style={
                                            "background": "rgba(74,158,255,0.18)",
                                            "border": "1px solid rgba(74,158,255,0.55)",
                                            "borderRadius": "8px",
                                            "color": "#7ab8ff",
                                            "fontSize": "13px", "fontWeight": "700",
                                            "padding": "9px 22px", "cursor": "pointer",
                                        }
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  PAGE LAYOUT
# ─────────────────────────────────────────────

def create_schedule_maintenance_layout(supabase=None, engine_db_id: str = None,
                                       org_id: str = None, role: str = None):
    """Build the Schedule Maintenance page."""

    # ── Fetch engines for dropdown, scoped by role ─────────────────────────
    # admin → all engines across all orgs
    # user  → only engines in their organisation
    engine_options = []
    engine_label_map = {}
    if supabase:
        try:
            q = supabase.table("engines").select("id, engine_id, model_type") \
                .eq("is_deleted", True)
            if role != "admin" and org_id:
                q = q.eq("organization_id", org_id)
            eng_resp = q.execute()
            for row in (eng_resp.data or []):
                label = f"ENGINE-{str(row.get('engine_id', '?')).zfill(2)} ({row.get('model_type', '')})"
                eid = str(row["id"])
                engine_options.append({"label": label, "value": eid})
                engine_label_map[eid] = f"ENGINE-{str(row.get('engine_id', '?')).zfill(2)}"
        except Exception:
            pass

    # ── Load existing schedules from Supabase ──────────────────────────────
    initial_events = []
    week_dates = _week_dates()
    week_date_strs = {d.isoformat() for d in week_dates}  # only show current week

    if supabase:
        try:
            sched_resp = supabase.table("maintenance_schedules") \
                .select("id, engine_id, scheduled_date, start_time, end_time, notes, status") \
                .order("scheduled_date", desc=False) \
                .execute()

            for idx, row in enumerate(sched_resp.data or []):
                sel_date = (row.get("scheduled_date") or "")[:10]
                if sel_date not in week_date_strs:
                    continue

                try:
                    dt = datetime.strptime(sel_date, "%Y-%m-%d")
                    day_name = DAYS[dt.weekday()] if dt.weekday() < 5 else None
                    if not day_name:
                        continue
                except Exception:
                    continue

                start_time = (row.get("start_time") or "09:00")[:5]
                end_time   = (row.get("end_time")   or "10:00")[:5]

                hour_str = start_time[:2] + ":00"
                if hour_str not in HOURS:
                    hour_str = HOURS[0]

                eid = str(row.get("engine_id", ""))
                engine_label = engine_label_map.get(eid, f"ENGINE-{eid[:6]}")

                initial_events.append({
                    "_idx":       f"loaded-{idx}",
                    "day":        day_name,
                    "hour":       hour_str,
                    "date":       sel_date,
                    "start_time": start_time,
                    "end_time":   end_time,
                    "label":      engine_label,
                    "engine_id":  eid,
                    "status":     row.get("status", "scheduled"),
                    "notes":      row.get("notes", ""),
                    "db_id":      str(row.get("id", "")),
                })
        except Exception as e:
            print(f"[SM] Could not load existing schedules: {e}")

    # Pre-select the engine if navigated from a specific engine card
    default_engine = engine_db_id if engine_db_id else None

    topbar = build_topbar()

    return html.Div(
        style={
            "height": "100vh",
            "overflow": "hidden",
            "fontFamily": "'Segoe UI', sans-serif",
            "background": "#0a1628",
            "color": "white",
            "display": "flex",
            "flexDirection": "column",
        },
        children=[
            dcc.Location(id="url-schedule-maintenance", refresh=False),

            # Stores
            dcc.Store(id="sm-events-store",         data=initial_events),
            dcc.Store(id="sm-preselect-engine",     data=default_engine),
            dcc.Store(id="sm-selected-event-store", data=None),
            dcc.Store(id="sm-week-offset-store",    data=0),

            topbar,

            # ── Main content (no sidebar) ──────────────────────────────────
            html.Div(
                style={
                    "flex": "1",
                    "minHeight": "0",
                    "overflow": "hidden",
                    "padding": "16px 32px 28px",
                    "minWidth": "0",
                    "display": "flex",
                    "flexDirection": "column",
                },
                children=[
                    # ── Title row ─────────────────────────────────────────
                    html.Div(
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "space-between",
                            "marginBottom": "22px",
                            "flexShrink": "0",
                        },
                        children=[
                            html.H2(
                                "Maintenance Schedule",
                                style={
                                    "margin": "0",
                                    "fontSize": "22px",
                                    "fontWeight": "700",
                                    "color": "white",
                                    "letterSpacing": "0.4px",
                                }
                            ),
                            html.Button(
                                children=[
                                    html.Span("New", style={"marginRight": "6px"}),
                                    html.Span(
                                        "+",
                                        style={
                                            "fontSize": "16px",
                                            "fontWeight": "700",
                                            "lineHeight": "1",
                                        }
                                    ),
                                ],
                                id="sm-new-btn",
                                n_clicks=0,
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "background": "rgba(74,158,255,0.14)",
                                    "border": "1px solid rgba(74,158,255,0.45)",
                                    "borderRadius": "8px",
                                    "color": "#7ab8ff",
                                    "fontSize": "13px",
                                    "fontWeight": "600",
                                    "padding": "8px 16px",
                                    "cursor": "pointer",
                                    "gap": "4px",
                                }
                            ),
                        ]
                    ),

                    # ── Week navigation bar ───────────────────────────────
                    html.Div(id="sm-week-nav-container",
                             style={"flexShrink": "0"},
                             children=[_build_week_nav(0)]),

                    # ── Calendar ──────────────────────────────────────────
                    html.Div(
                        id="sm-calendar-container",
                        style={
                            "flex": "1",
                            "minHeight": "0",
                            "display": "flex",
                            "flexDirection": "column",
                        },
                        children=[_build_calendar(initial_events, 0)],
                    ),
                ]
            ),

            # ── Modal (fixed overlay) ─────────────────────────────────────
            _build_modal(engine_options),

            # ── Edit/Delete modal ─────────────────────────────────────────
            _build_edit_modal(engine_options),
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def register_schedule_maintenance_callbacks(app, supabase=None):

    # ── Open modal ────────────────────────────────────────────────────────
    @app.callback(
        Output("sm-modal-overlay",  "style"),
        Output("sm-modal-engine",   "value"),
        Input("sm-new-btn",         "n_clicks"),
        Input("sm-modal-cancel",    "n_clicks"),
        Input("sm-modal-close",     "n_clicks"),
        State("sm-preselect-engine","data"),
        prevent_initial_call=True,
    )
    def toggle_modal(open_clicks, cancel_clicks, close_clicks, preselect):
        triggered = callback_context.triggered[0]["prop_id"].split(".")[0]

        hidden = {
            "display": "none",
            "position": "fixed", "top": "0", "left": "0",
            "width": "100vw", "height": "100vh",
            "background": "rgba(5,12,28,0.75)",
            "zIndex": "1000",
            "alignItems": "center",
            "justifyContent": "center",
        }
        visible = {**hidden, "display": "flex"}

        if triggered == "sm-new-btn":
            return visible, preselect
        return hidden, dash.no_update

    # ── Schedule event → update calendar ─────────────────────────────────
    @app.callback(
        Output("sm-events-store",       "data"),
        Output("sm-calendar-container", "children"),
        Output("sm-modal-overlay",      "style", allow_duplicate=True),
        Output("sm-modal-validation",   "children"),
        Input("sm-modal-schedule",      "n_clicks"),
        State("sm-modal-engine",        "value"),
        State("sm-modal-date",          "value"),
        State("sm-modal-start-time",    "value"),
        State("sm-modal-end-time",      "value"),
        State("sm-modal-notes",         "value"),
        State("sm-events-store",        "data"),
        State("session-store",          "data"),
        prevent_initial_call=True,
    )
    def handle_schedule(n_clicks, engine_id, sel_date,
                        start_time, end_time, notes, existing_events, session):

        hidden_style = {
            "display": "none",
            "position": "fixed", "top": "0", "left": "0",
            "width": "100vw", "height": "100vh",
            "background": "rgba(5,12,28,0.75)",
            "zIndex": "1000",
            "alignItems": "center",
            "justifyContent": "center",
        }

        # ── Validation ──
        if not engine_id:
            return (
                dash.no_update, dash.no_update, dash.no_update,
                html.Span("Please select an engine.", style={"color": "#ff6b6b", "fontSize": "12px"}),
            )
        if not sel_date:
            return (
                dash.no_update, dash.no_update, dash.no_update,
                html.Span("Please select a date.", style={"color": "#ff6b6b", "fontSize": "12px"}),
            )
        if not start_time or not end_time:
            return (
                dash.no_update, dash.no_update, dash.no_update,
                html.Span("Please set start and end time.", style={"color": "#ff6b6b", "fontSize": "12px"}),
            )

        # ── Derive day-of-week from the selected date ──
        try:
            dt = datetime.strptime(sel_date, "%Y-%m-%d")
            day_name = DAYS[dt.weekday()]   # 0=Mon … 6=Sun
        except Exception:
            return (
                dash.no_update, dash.no_update, dash.no_update,
                html.Span("Invalid date.", style={"color": "#ff6b6b", "fontSize": "12px"}),
            )

        # ── Snap start_time to the nearest hour slot ──
        try:
            hour_str = start_time[:2] + ":00"
            if hour_str not in HOURS:
                hour_str = HOURS[0]
        except Exception:
            hour_str = HOURS[0]

        # ── Fetch engine label for display ────────────────────────────────
        engine_label = f"ENGINE-{engine_id[:6]}"
        status = "warning"
        if supabase:
            try:
                resp = supabase.table("engines") \
                    .select("engine_id, model_type") \
                    .eq("id", engine_id) \
                    .single().execute()
                if resp.data:
                    engine_label = f"ENGINE-{str(resp.data.get('engine_id', '?')).zfill(2)}"
                # Fetch latest RUL to derive status
                pred = supabase.table("rul_predictions") \
                    .select("predicted_rul") \
                    .eq("engine_id", engine_id) \
                    .order("predicted_at", desc=True) \
                    .limit(1).execute()
                if pred.data:
                    rul = float(pred.data[0].get("predicted_rul", 100))
                    status = "critical" if rul <= 30 else "warning" if rul <= 62 else "healthy"
            except Exception:
                pass

        # ── Build new event dict ──────────────────────────────────────────
        import uuid as _uuid
        new_event = {
            "_idx":       str(_uuid.uuid4()),
            "day":        day_name,
            "hour":       hour_str,
            "date":       sel_date,
            "start_time": start_time,
            "end_time":   end_time,
            "label":      engine_label,
            "engine_id":  engine_id,
            "status":     status,
            "notes":      notes or "",
            "db_id":      "",  # filled after insert below
        }

        updated_events = list(existing_events or []) + [new_event]

        # ── Persist to Supabase if available ─────────────────────────────
        if supabase:
            try:
                user_id = (session or {}).get("user_id") or None
                result = supabase.table("maintenance_schedules").insert({
                    "engine_id":      engine_id,
                    "scheduled_date": sel_date,
                    "start_time":     start_time,
                    "end_time":       end_time,
                    "notes":          notes or "",
                    "status":         "scheduled",
                    "created_by":     user_id,
                    "created_at":     datetime.utcnow().isoformat(),
                }).execute()
                if result.data:
                    new_event["db_id"] = str(result.data[0].get("id", ""))
            except Exception as e:
                print(f"[SM][WARN] Supabase insert failed: {e}")

        return (
            updated_events,
            [_build_calendar(updated_events, 0)],
            hidden_style,
            "",
        )


    # ── Week navigation: prev / next / today ─────────────────────────────
    @app.callback(
        Output("sm-week-offset-store",   "data"),
        Output("sm-week-nav-container",  "children"),
        Output("sm-calendar-container",  "children", allow_duplicate=True),
        Input("sm-nav-prev",   "n_clicks"),
        Input("sm-nav-next",   "n_clicks"),
        Input("sm-nav-today",  "n_clicks"),
        State("sm-week-offset-store", "data"),
        State("sm-events-store",      "data"),
        prevent_initial_call=True,
    )
    def navigate_week(prev, nxt, today, offset, events):
        triggered = callback_context.triggered[0]["prop_id"].split(".")[0]
        offset = offset or 0
        if triggered == "sm-nav-prev":
            offset -= 1
        elif triggered == "sm-nav-next":
            offset += 1
        else:
            offset = 0
        return offset, [_build_week_nav(offset)], [_build_calendar(events or [], offset)]

    # ── Open edit modal when a card is clicked ────────────────────────────
    @app.callback(
        Output("sm-edit-modal-overlay",   "style"),
        Output("sm-selected-event-store", "data"),
        Output("sm-edit-engine",          "value"),
        Output("sm-edit-date",            "value"),
        Output("sm-edit-start-time",      "value"),
        Output("sm-edit-end-time",        "value"),
        Output("sm-edit-notes",           "value"),
        Input({"type": "sm-event-card", "index": ALL}, "n_clicks"),
        State("sm-events-store", "data"),
        prevent_initial_call=True,
    )
    def open_edit_modal(n_clicks_list, events):
        # Find which card was clicked
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise dash.exceptions.PreventUpdate

        triggered_id = ctx.triggered[0]["prop_id"]
        import json as _json
        try:
            id_dict = _json.loads(triggered_id.split(".")[0])
            clicked_idx = id_dict.get("index")
        except Exception:
            raise dash.exceptions.PreventUpdate

        # Find the matching event
        ev = next((e for e in (events or []) if e.get("_idx") == clicked_idx), None)
        if ev is None:
            raise dash.exceptions.PreventUpdate

        visible = {
            "display": "flex",
            "position": "fixed", "top": "0", "left": "0",
            "width": "100vw", "height": "100vh",
            "background": "rgba(5,12,28,0.75)",
            "zIndex": "1000",
            "alignItems": "center",
            "justifyContent": "center",
        }

        return (
            visible,
            ev,                            # store selected event
            ev.get("engine_id"),
            ev.get("date"),
            ev.get("start_time"),
            ev.get("end_time"),
            ev.get("notes", ""),
        )

    # ── Close edit modal (Cancel or ×) ────────────────────────────────────
    @app.callback(
        Output("sm-edit-modal-overlay", "style", allow_duplicate=True),
        Input("sm-edit-cancel-btn",     "n_clicks"),
        Input("sm-edit-modal-close",    "n_clicks"),
        prevent_initial_call=True,
    )
    def close_edit_modal(cancel, close):
        return {
            "display": "none",
            "position": "fixed", "top": "0", "left": "0",
            "width": "100vw", "height": "100vh",
            "background": "rgba(5,12,28,0.75)",
            "zIndex": "1000",
            "alignItems": "center",
            "justifyContent": "center",
        }

    # ── Save (edit) or Delete ─────────────────────────────────────────────
    @app.callback(
        Output("sm-events-store",           "data",          allow_duplicate=True),
        Output("sm-calendar-container",     "children",      allow_duplicate=True),
        Output("sm-edit-modal-overlay",     "style",         allow_duplicate=True),
        Output("sm-edit-modal-validation",  "children"),
        Input("sm-edit-save-btn",           "n_clicks"),
        Input("sm-edit-delete-btn",         "n_clicks"),
        State("sm-edit-engine",             "value"),
        State("sm-edit-date",               "value"),
        State("sm-edit-start-time",         "value"),
        State("sm-edit-end-time",           "value"),
        State("sm-edit-notes",              "value"),
        State("sm-selected-event-store",    "data"),
        State("sm-events-store",            "data"),
        State("session-store",              "data"),
        prevent_initial_call=True,
    )
    def save_or_delete_event(save_clicks, delete_clicks,
                             engine_id, sel_date, start_time, end_time, notes,
                             selected_ev, existing_events, session):

        hidden_style = {
            "display": "none",
            "position": "fixed", "top": "0", "left": "0",
            "width": "100vw", "height": "100vh",
            "background": "rgba(5,12,28,0.75)",
            "zIndex": "1000",
            "alignItems": "center",
            "justifyContent": "center",
        }

        triggered = callback_context.triggered[0]["prop_id"].split(".")[0]
        events = list(existing_events or [])
        ev_idx = (selected_ev or {}).get("_idx")
        db_id  = (selected_ev or {}).get("db_id", "")

        # ── DELETE ────────────────────────────────────────────────────────
        if triggered == "sm-edit-delete-btn":
            updated = [e for e in events if e.get("_idx") != ev_idx]
            if supabase and db_id:
                try:
                    supabase.table("maintenance_schedules") \
                        .delete().eq("id", db_id).execute()
                except Exception as e:
                    print(f"[SM][WARN] Delete failed: {e}")
            return updated, [_build_calendar(updated, 0)], hidden_style, ""

        # ── SAVE (edit) ───────────────────────────────────────────────────
        if not engine_id:
            return dash.no_update, dash.no_update, dash.no_update, \
                html.Span("Please select an engine.", style={"color": "#ff6b6b", "fontSize": "12px"})
        if not sel_date:
            return dash.no_update, dash.no_update, dash.no_update, \
                html.Span("Please select a date.", style={"color": "#ff6b6b", "fontSize": "12px"})
        if not start_time or not end_time:
            return dash.no_update, dash.no_update, dash.no_update, \
                html.Span("Please set start and end time.", style={"color": "#ff6b6b", "fontSize": "12px"})

        try:
            dt = datetime.strptime(sel_date, "%Y-%m-%d")
            day_name = DAYS[dt.weekday()] if dt.weekday() < 5 else None
            if not day_name:
                return dash.no_update, dash.no_update, dash.no_update, \
                    html.Span("Please select a weekday.", style={"color": "#ff6b6b", "fontSize": "12px"})
        except Exception:
            return dash.no_update, dash.no_update, dash.no_update, \
                html.Span("Invalid date.", style={"color": "#ff6b6b", "fontSize": "12px"})

        hour_str = start_time[:2] + ":00"
        if hour_str not in HOURS:
            hour_str = HOURS[0]

        # Fetch engine label
        engine_label = (selected_ev or {}).get("label", f"ENGINE-{engine_id[:6]}")
        status = (selected_ev or {}).get("status", "warning")
        if supabase:
            try:
                resp = supabase.table("engines").select("engine_id") \
                    .eq("id", engine_id).single().execute()
                if resp.data:
                    engine_label = f"ENGINE-{str(resp.data.get('engine_id', '?')).zfill(2)}"
            except Exception:
                pass

        updated_ev = {
            "_idx":       ev_idx,
            "day":        day_name,
            "hour":       hour_str,
            "date":       sel_date,
            "start_time": start_time,
            "end_time":   end_time,
            "label":      engine_label,
            "engine_id":  engine_id,
            "status":     status,
            "notes":      notes or "",
            "db_id":      db_id,
        }

        # Replace the old event in the list
        updated = [updated_ev if e.get("_idx") == ev_idx else e for e in events]

        # Persist to Supabase
        if supabase and db_id:
            try:
                supabase.table("maintenance_schedules").update({
                    "engine_id":      engine_id,
                    "scheduled_date": sel_date,
                    "start_time":     start_time,
                    "end_time":       end_time,
                    "notes":          notes or "",
                }).eq("id", db_id).execute()
            except Exception as e:
                print(f"[SM][WARN] Update failed: {e}")

        return updated, [_build_calendar(updated, 0)], hidden_style, ""

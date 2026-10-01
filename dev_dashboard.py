from assets import database_integration as db
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import base64
from assets.components import (build_dev_sidebar, icon_sidebar, gear_icon, org_icon)

def create_dev_dashboard_layout(supabase):
    """Developer dashboard showing all organizations and their engines."""
    org_data = []
    total_orgs = 0
    total_engines = 0
    total_users = 0

    try:
        if supabase:
            # ── Fetch alert thresholds ──
            warn_thresh = 50
            crit_thresh = 30
            max_life = 125
            try:
                t_resp = db.get_alert_thresholds(
                    supabase,
                    "warning_threshold, critical_threshold, max_rul_cap",
                )
                if t_resp.data:
                    warn_thresh = int(t_resp.data[0].get("warning_threshold", warn_thresh))
                    crit_thresh = int(t_resp.data[0].get("critical_threshold", crit_thresh))
                    max_life = int(t_resp.data[0].get("max_rul_cap", max_life))
            except Exception:
                pass

            # ── Fetch all organizations ──
            orgs_resp = db.fetch_records(supabase, "organizations", "*")
            orgs = orgs_resp.data or []
            total_orgs = len(orgs)

            # ── Fetch all engines ──
            engines_resp = db.fetch_records(supabase, "engines", "*")
            all_engines = engines_resp.data or []
            total_engines = len(all_engines)

            # ── Batch-fetch latest predicted_rul per engine ──
            engine_ids = [e.get("id") for e in all_engines if e.get("id")]
            latest_rul_map = {}
            if engine_ids:
                try:
                    pred_resp = db.fetch_records(
                        supabase,
                        "rul_predictions",
                        "engine_id, predicted_rul",
                        filters=[('in_', "engine_id", engine_ids)],
                        order_by=[("predicted_at", True)],
                    )
                    for row in (pred_resp.data or []):
                        eid = row.get("engine_id")
                        if eid and eid not in latest_rul_map and row.get("predicted_rul") is not None:
                            latest_rul_map[eid] = float(row["predicted_rul"])
                except Exception:
                    pass

            # ── Group engines by organization ──
            # Fetch all users to count per org
            all_users = []
            try:
                users_resp = db.fetch_records(supabase, "users", "id, organization_id", count="exact")
                all_users = users_resp.data or []
                total_users = users_resp.count if users_resp.count is not None else len(all_users)
            except Exception:
                pass

            for org in orgs:
                org_id = org.get("id")
                org_name = org.get("name", "Unknown")
                org_engines = [e for e in all_engines if e.get("organization_id") == org_id]
                org_user_count = sum(1 for u in all_users if u.get("organization_id") == org_id)

                engine_cards_data = []
                for engine in org_engines:
                    db_id = engine.get("id")
                    if db_id in latest_rul_map:
                        rul = latest_rul_map[db_id]
                    else:
                        current_cycle = engine.get("current_cycle") or 0
                        rul = max(0.0, float(max_life - current_cycle))

                    if rul <= crit_thresh:
                        status = "critical"
                    elif rul <= warn_thresh:
                        status = "warning"
                    else:
                        status = "healthy"

                    degradation = max(0, min(100, round((1 - rul / max_life) * 100)))

                    engine_cards_data.append({
                        "db_id": db_id,
                        "id": str(engine.get("engine_id", "?")).zfill(2),
                        "status": status,
                        "rul": int(round(rul)),
                        "model_type": engine.get("model_type", "N/A"),
                        "created_at": (engine.get("created_at") or "")[:10],
                    })

                org_data.append({
                    "id": org_id,
                    "name": org_name,
                    "engine_count": len(org_engines),
                    "user_count": org_user_count,
                    "engines": engine_cards_data,
                })

    except Exception as e:
        import traceback
        print(f"[ERROR] Dev Dashboard: {traceback.format_exc()}")

    # ── Helper: status colors ──
    status_colors = {
        "healthy": {"bg": "rgba(0, 255, 100, 0.15)", "border": "#00ff64", "text": "#00ff64"},
        "warning": {"bg": "rgba(255, 217, 61, 0.15)", "border": "#ffd93d", "text": "#ffd93d"},
        "critical": {"bg": "rgba(255, 77, 77, 0.15)", "border": "#ff4d4d", "text": "#ff4d4d"},
    }

    def engine_card(engine):
        colors = status_colors[engine["status"]]
        return html.Div(
            style={"minWidth": "220px", "maxWidth": "240px", "flexShrink": "0"},
            children=[
                dcc.Link(
                    href=f"/overview/{engine['db_id']}",
                    style={"textDecoration": "none"},
                    children=[
                        html.Div(
                            style={
                                "background": "#101a2f",
                                "border": "1px solid rgba(74,158,255,0.2)",
                                "borderRadius": "12px", "padding": "14px",
                                "display": "flex", "flexDirection": "column",
                                "gap": "6px", "cursor": "pointer",
                            },
                            children=[
                                html.Div(
                                    style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "paddingBottom": "8px"},
                                    children=[
                                        html.Div(style={"display": "flex", "alignItems": "center", "gap": "6px"},
                                                 children=[gear_icon(), html.Span(f"ENGINE-{engine['id']}", style={"color": "white", "fontWeight": "700", "fontSize": "13px"})]),
                                        html.Span(engine["status"].upper(), style={
                                            "background": colors["bg"], "color": colors["text"],
                                            "border": f"1px solid {colors['border']}",
                                            "borderRadius": "8px", "padding": "3px 8px",
                                            "fontSize": "9px", "fontWeight": "700",
                                        }),
                                    ]
                                ),
                                html.Div(style={"display": "flex", "justifyContent": "space-between"},
                                         children=[
                                             html.Span("Model", style={"color": "rgba(180,210,255,0.7)", "fontSize": "11px"}),
                                             html.Span(engine.get("model_type", "N/A"), style={"color": "rgba(200,220,255,0.9)", "fontWeight": "700", "fontSize": "13px"}),
                                         ]),
                                html.Div(style={"display": "flex", "justifyContent": "space-between"},
                                         children=[
                                             html.Span("Created", style={"color": "rgba(180,210,255,0.7)", "fontSize": "11px"}),
                                             html.Span(engine.get("created_at", "N/A"), style={"color": "rgba(200,220,255,0.9)", "fontWeight": "600", "fontSize": "11px"}),
                                         ]),
                                html.Div(style={"display": "flex", "justifyContent": "space-between"},
                                         children=[
                                             html.Span("Cycles left", style={"color": "rgba(74,158,255,0.7)", "fontSize": "11px"}),
                                             html.Span(f"{engine['rul']}", style={"color": "#4a9eff", "fontWeight": "700", "fontSize": "13px"}),
                                         ]),
                            ]
                        )
                    ]
                )
            ]
        )

    def org_row(org):
        """Build a row for one organization with horizontally scrollable engine cards."""
        return html.Div(
            style={
                "background": "#0d1e3a",
                "border": "1px solid rgba(74,158,255,0.2)",
                "borderRadius": "14px",
                "padding": "20px 20px 12px 20px",
                "marginBottom": "20px",
                "minWidth": "0",        # prevent flex child from overflowing its parent
                "width": "100%",        # stay within the page column
                "boxSizing": "border-box",
                "overflow": "hidden",   # clip anything that escapes
            },
            children=[
                # ── Org header (never scrolls) ──
                html.Div(
                    style={
                        "display": "flex", "alignItems": "center",
                        "justifyContent": "space-between",
                        "marginBottom": "12px",
                    },
                    children=[
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "gap": "10px"},
                            children=[org_icon(), html.Span(org["name"], style={"color": "white", "fontWeight": "700", "fontSize": "17px"})]
                        ),
                        html.Div(style={"display": "flex", "alignItems": "center", "gap": "16px"}, children=[
                            html.Span(f"{org.get('user_count', 0)} user{'s' if org.get('user_count', 0) != 1 else ''}",
                                      style={"color": "rgba(168,212,255,0.7)", "fontSize": "13px", "fontWeight": "600"}),
                            html.Span(f"{org['engine_count']} engine{'s' if org['engine_count'] != 1 else ''}",
                                      style={"color": "rgba(168,212,255,0.7)", "fontSize": "13px", "fontWeight": "600"}),
                        ]),
                    ]
                ),
                # ── Engine card strip — scrolls horizontally inside the fixed-width container ──
                html.Div(
                    className="engine-card-row",
                    style={
                        "display": "flex",
                        "flexWrap": "nowrap",
                        "gap": "14px",
                        "overflowX": "auto",
                        "overflowY": "hidden",
                        "paddingBottom": "8px",
                        "WebkitOverflowScrolling": "touch",
                    },
                    children=[engine_card(e) for e in org["engines"]] if org["engines"] else [
                        html.Div("No engines registered.",
                                 style={"color": "rgba(255,255,255,0.5)", "fontSize": "13px", "padding": "10px 0"})
                    ]
                ),
            ]
        )

    # ── Build organization dropdown options for filter ──
    org_options = [{"label": "All Organizations", "value": "all"}] + [
        {"label": o["name"], "value": o["id"]} for o in org_data
    ]

    return html.Div(
        style={
            "height": "100vh",
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": "'Segoe UI', sans-serif",
            "background": "#0a1628",
            "color": "white",
            "overflow": "hidden",
        },
        children=[
            dcc.Location(id='url-dev-dashboard', refresh=False),

            # ── Topbar ──
            html.Div(
                style={
                    "background": "linear-gradient(90deg, #0d2045 0%, #071530 100%)",
                    "borderBottom": "1px solid rgba(74,158,255,0.18)",
                    "padding": "0 28px",
                    "height": "60px",
                    "minHeight": "60px",
                    "flexShrink": "0",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "zIndex": "200",
                    "width": "100%",
                },
                children=[
                    html.H1("DEVELOPER DASHBOARD", style={
                        "margin": "0", "fontSize": "18px", "fontWeight": "700",
                        "color": "white", "letterSpacing": "1.2px",
                    }),
                    html.Div(
                        id="sidebar-toggle", n_clicks=0,
                        style={"cursor": "pointer"},
                        children=[icon_sidebar()]
                    ),
                ]
            ),

            # ── Body: sidebar + content ──
            html.Div(
                style={
                    "flex": "1",
                    "display": "flex",
                    "flexDirection": "row",
                    "overflow": "hidden",
                    "minHeight": "0",
                },
                children=[
                    # Sidebar
                    build_dev_sidebar(active_page="dashboard"),

                    # Scrollable content
                    html.Div(
                        style={
                            "flex": "1",
                            "overflowY": "auto",
                            "padding": "24px 28px",
                            "minWidth": "0",
                        },
                        children=[
                            # ── Summary cards ──
                            html.Div(
                                style={"display": "flex", "gap": "20px", "marginBottom": "32px", "justifyContent": "center"},
                                children=[
                                    html.Div(style={
                                        "background": "linear-gradient(135deg, #2a354a 0%, #1a2335 100%)",
                                        "border": "1px solid rgba(74,158,255,0.3)",
                                        "borderRadius": "12px", "padding": "16px 24px",
                                        "display": "flex", "alignItems": "center", "gap": "20px",
                                        "minWidth": "220px", "justifyContent": "space-between",
                                    }, children=[
                                        html.Span("ORGANIZATIONS", style={"color": "#4a9eff", "fontSize": "14px", "fontWeight": "600"}),
                                        html.Span(str(total_orgs), style={"color": "#4a9eff", "fontSize": "36px", "fontWeight": "700"}),
                                    ]),
                                    html.Div(style={
                                        "background": "linear-gradient(135deg, #2a354a 0%, #1a2335 100%)",
                                        "border": "1px solid rgba(255,255,255,0.2)",
                                        "borderRadius": "12px", "padding": "16px 24px",
                                        "display": "flex", "alignItems": "center", "gap": "20px",
                                        "minWidth": "220px", "justifyContent": "space-between",
                                    }, children=[
                                        html.Span("TOTAL ENGINES", style={"color": "white", "fontSize": "14px", "fontWeight": "600"}),
                                        html.Span(str(total_engines), style={"color": "white", "fontSize": "36px", "fontWeight": "700"}),
                                    ]),
                                    html.Div(style={
                                        "background": "linear-gradient(135deg, rgba(74,158,255,0.15) 0%, rgba(42,111,212,0.08) 100%)",
                                        "border": "1px solid rgba(74,158,255,0.5)",
                                        "borderRadius": "12px", "padding": "16px 24px",
                                        "display": "flex", "alignItems": "center", "gap": "20px",
                                        "minWidth": "220px", "justifyContent": "space-between",
                                    }, children=[
                                        html.Span("TOTAL USERS", style={"color": "#4a9eff", "fontSize": "14px", "fontWeight": "600"}),
                                        html.Span(str(total_users), style={"color": "#4a9eff", "fontSize": "36px", "fontWeight": "700"}),
                                    ]),
                                ]
                            ),

                            # ── Main content: Organizations ──
                            html.Div(
                                style={"display": "flex", "gap": "24px", "minWidth": "0"},
                                children=[
                                    # Organizations list
                                    html.Div(
                                        style={"flex": "1", "width": "100%", "minWidth": "0", "overflow": "hidden"},
                                        children=[
                                            html.Div(
                                                style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "20px"},
                                                children=[
                                                    html.H2("Organizations", style={"margin": "0", "color": "white", "fontSize": "22px", "fontWeight": "700", "marginRight": "auto"}),
                                                    dcc.Input(
                                                        id="dev-org-search",
                                                        type="text",
                                                        placeholder="Search organization...",
                                                        value="",
                                                        style={
                                                            "background": "rgba(10,25,55,0.8)",
                                                            "border": "1px solid rgba(74,158,255,0.3)",
                                                            "borderRadius": "8px", "padding": "8px 14px",
                                                            "color": "rgba(200,220,255,0.8)",
                                                            "fontSize": "13px", "width": "220px",
                                                            "outline": "none", "fontFamily": "inherit",
                                                        }
                                                    ),
                                                    dcc.Dropdown(
                                                        id="dev-org-filter",
                                                        options=org_options,
                                                        value="all",
                                                        clearable=False,
                                                        searchable=False,
                                                        style={
                                                            "width": "220px",
                                                            "fontSize": "13px",
                                                            "backgroundColor": "transparent",
                                                            "border": "none",
                                                            "color": "white",
                                                        },
                                                        className="dark-dropdown",
                                                    ),
                                                ]
                                            ),
                                            html.Div(
                                                id="dev-org-list",
                                                style={"minWidth": "0", "width": "100%"},
                                                children=[org_row(o) for o in org_data] if org_data else [
                                                    html.Div("No organizations found.", style={
                                                        "color": "rgba(255,255,255,0.5)", "fontSize": "14px",
                                                        "textAlign": "center", "padding": "40px 0",
                                                    })
                                                ]
                                            ),
                                        ]
                                    ),

                                ]
                            )
                        ]
                    )
                ]
            ),
            # Store org data for client-side filtering
            dcc.Store(id="dev-org-data-store", data=org_data),
        ]
    )

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import base64


def gear_icon():
    gear_svg_base64 = base64.b64encode('''
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="48" fill="none" stroke="rgba(100,160,255,0.35)" stroke-width="1.5"/>
        <circle cx="50" cy="50" r="18" fill="none" stroke="#4a9eff" stroke-width="2"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(0 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(45 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(90 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(135 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(180 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(225 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(270 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(315 50 50)"/>
        <line x1="50" y1="32" x2="50" y2="20" stroke="#4a9eff" stroke-width="1.2"/>
        <line x1="50" y1="20" x2="65" y2="20" stroke="#4a9eff" stroke-width="1.2"/>
        <circle cx="65" cy="20" r="2.5" fill="#4a9eff"/>
        <line x1="68" y1="50" x2="80" y2="50" stroke="#4a9eff" stroke-width="1.2"/>
        <line x1="80" y1="50" x2="80" y2="35" stroke="#4a9eff" stroke-width="1.2"/>
        <circle cx="80" cy="35" r="2.5" fill="#4a9eff"/>
        <line x1="50" y1="68" x2="50" y2="80" stroke="#4a9eff" stroke-width="1.2"/>
        <line x1="50" y1="80" x2="35" y2="80" stroke="#4a9eff" stroke-width="1.2"/>
        <circle cx="35" cy="80" r="2.5" fill="#4a9eff"/>
        <line x1="32" y1="50" x2="20" y2="50" stroke="#4a9eff" stroke-width="1.2"/>
        <line x1="20" y1="50" x2="20" y2="65" stroke="#4a9eff" stroke-width="1.2"/>
        <circle cx="20" cy="65" r="2.5" fill="#4a9eff"/>
        <circle cx="50" cy="50" r="4" fill="#4a9eff"/>
    </svg>
    '''.encode('utf-8')).decode('utf-8')
    return html.Img(src=f'data:image/svg+xml;base64,{gear_svg_base64}', style={'width': '28px', 'height': '28px'})


def warning_icon():
    svg_base64 = base64.b64encode('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2 L22 20 L2 20 Z" fill="none" stroke="#ffd93d" stroke-width="2"/>
        <circle cx="12" cy="15" r="1" fill="#ffd93d"/>
        <line x1="12" y1="8" x2="12" y2="12" stroke="#ffd93d" stroke-width="2" stroke-linecap="round"/>
    </svg>
    '''.encode('utf-8')).decode('utf-8')
    return html.Img(src=f'data:image/svg+xml;base64,{svg_base64}', style={'width': '28px', 'height': '28px'})


def critical_icon():
    svg_base64 = base64.b64encode('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" fill="none" stroke="#ff4d4d" stroke-width="2"/>
        <line x1="8" y1="8" x2="16" y2="16" stroke="#ff4d4d" stroke-width="2" stroke-linecap="round"/>
        <line x1="16" y1="8" x2="8" y2="16" stroke="#ff4d4d" stroke-width="2" stroke-linecap="round"/>
    </svg>
    '''.encode('utf-8')).decode('utf-8')
    return html.Img(src=f'data:image/svg+xml;base64,{svg_base64}', style={'width': '28px', 'height': '28px'})


def bell_icon():
    svg_base64 = base64.b64encode('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#ffd93d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>
    '''.encode('utf-8')).decode('utf-8')
    return html.Img(src=f'data:image/svg+xml;base64,{svg_base64}',
                    style={'width': '22px', 'height': '22px'})


def logout_icon():
    svg_base64 = base64.b64encode('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M9 21 H5 Q4 21 4 20 V4 Q4 3 5 3 H9 M15 17 L20 12 L15 7 M10 12 H20" fill="none" stroke="#ff4d4d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    '''.encode('utf-8')).decode('utf-8')
    return html.Img(src=f'data:image/svg+xml;base64,{svg_base64}', style={'width': '28px', 'height': '28px'})


def create_dashboard_layout(supabase, org_id=None):
    engine_data = []
    maintenance_alerts = []
    total_count = 0
    healthy_count = 0
    warning_count = 0
    critical_count = 0
    alert_count = 0

    try:
        if supabase:
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

            # ── Base query builder: always filter by org_id ──
            def eng_query():
                q = supabase.table("engines").select("*", count="exact")
                if org_id:
                    q = q.eq("organization_id", org_id)
                return q

            response     = eng_query().execute()
            total_count  = response.count or 0

            # warning_count / critical_count are derived below from engine_data
            # after applying the fetched thresholds, so the cards and summary
            # always use the same threshold values.

            engine_ids = [e.get("id") for e in (response.data or []) if e.get("id")]

            # Alert count scoped to org engines
            if org_id and engine_ids:
                alert_count = (
                    supabase.table("alert_logs")
                    .select("*", count="exact")
                    .in_("engine_id", engine_ids)
                    .execute().count or 0
                )
            else:
                alert_count = supabase.table("alert_logs").select("*", count="exact").execute().count or 0

            # ── Batch-fetch latest predicted_rul per engine from rul_predictions ──
            latest_rul_map = {}   # engine_db_id → predicted_rul float
            if engine_ids:
                try:
                    # Fetch all predictions for these engines ordered newest first,
                    # then keep only the first (latest) row per engine
                    pred_resp = supabase.table("rul_predictions") \
                        .select("engine_id, predicted_rul") \
                        .in_("engine_id", engine_ids) \
                        .order("predicted_at", desc=True) \
                        .execute()
                    for row in (pred_resp.data or []):
                        eid = row.get("engine_id")
                        if eid and eid not in latest_rul_map and row.get("predicted_rul") is not None:
                            latest_rul_map[eid] = float(row["predicted_rul"])
                except Exception:
                    pass

            print(f"[DEBUG] Raw rows: {response.data}")
            for engine in (response.data or []):
                db_id = engine.get("id")

                # Use predicted_rul from rul_predictions; fall back to cycle-based estimate
                if db_id in latest_rul_map:
                    rul = latest_rul_map[db_id]
                else:
                    current_cycle = engine.get("current_cycle") or 0
                    rul = max(0.0, float(max_life - current_cycle))

                # Status derived from thresholds
                if rul <= crit_thresh:
                    raw_status = "critical"
                elif rul <= warn_thresh:
                    raw_status = "warning"
                else:
                    raw_status = "healthy"

                # Degradation: how close to 0 relative to max_life
                degradation = max(0, min(100, round((1 - rul / max_life) * 100)))

                engine_data.append({
                    "db_id":       db_id,
                    "id":          str(engine.get("engine_id", "?")).zfill(2),
                    "status":      raw_status,
                    "degradation": degradation,
                    "rul":         int(round(rul)),
                })

            # ── Derive summary counts from engine_data (uses fetched thresholds) ──
            healthy_count  = sum(1 for e in engine_data if e["status"] == "healthy")
            warning_count  = sum(1 for e in engine_data if e["status"] == "warning")
            critical_count = sum(1 for e in engine_data if e["status"] == "critical")

            print(f"[DEBUG] Parsed engine_data: {engine_data}")

            # ── Fetch maintenance alerts scoped to this org's engines ──
            alert_query = supabase.table("alert_logs") \
                .select("*") \
                .in_("severity", ["warning", "critical"]) \
                .eq("status", "open") \
                .order("triggered_at", desc=True) \
                .limit(10)

            # If org_id present, only fetch alerts for this org's engines
            if org_id and engine_ids:
                alert_query = alert_query.in_("engine_id", engine_ids)

            alerts_resp = alert_query.execute()

            for alert in (alerts_resp.data or []):
                alert_engine_id = alert.get("engine_id")   # this is engines.id (PK), per your FK
                if alert_engine_id is None:
                    continue

                # Look up the engine row for this alert
                eng_resp = supabase.table("engines") \
                    .select("id, engine_id, current_cycle") \
                    .eq("id", alert_engine_id) \
                    .single() \
                    .execute()
                eng = eng_resp.data or {}

                eng_db_id = eng.get("id")
                eng_display_id = str(eng.get("engine_id", "?")).zfill(2)

                # Use predicted_rul if available, else cycle-based fallback
                if eng_db_id in latest_rul_map:
                    rul = int(round(latest_rul_map[eng_db_id]))
                else:
                    current_cycle = eng.get("current_cycle") or 0
                    rul = max(0, int(max_life - current_cycle))

                severity = (alert.get("severity") or "warning").lower()

                maintenance_alerts.append({
                    "db_id": eng_db_id,
                    "engine_id": eng_display_id,
                    "severity": severity,
                    "rul": rul,
                    "action_text": "Immediate Maintenance" if severity == "critical" else "Schedule Maintenance",
                })

            print(f"[DEBUG] Maintenance alerts: {maintenance_alerts}")

    except Exception as e:
        import traceback
        print(f"[ERROR] {traceback.format_exc()}")

    status_colors = {
        "healthy": {"bg": "rgba(0, 255, 100, 0.15)", "border": "#00ff64", "text": "#00ff64"},
        "warning": {"bg": "rgba(255, 217, 61, 0.15)", "border": "#ffd93d", "text": "#ffd93d"},
        "critical": {"bg": "rgba(255, 77, 77, 0.15)", "border": "#ff4d4d", "text": "#ff4d4d"},
    }

    def engine_card(engine):
        # ... unchanged ...
        colors = status_colors[engine["status"]]
        return html.Div(
            dcc.Link(
                href=f"/overview/{engine['db_id']}",
                style={"textDecoration": "none"},
                children=[
                    html.Div(
                        style={
                            "background": "#101a2f",
                            "border": "1px solid rgba(74, 158, 255, 0.2)",
                            "borderRadius": "12px",
                            "padding": "16px",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "8px",
                            "cursor": "pointer",
                            "transition": "border 0.2s, background 0.2s",
                        },
                        id={"type": "engine-card", "index": engine["db_id"]},
                        children=[
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
                                children=[
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                        children=[
                                            gear_icon(),
                                            html.Span(f"# ENGINE-{engine['id']}", style={"color": "white", "fontWeight": "700", "fontSize": "14px"})
                                        ]
                                    ),
                                    html.Span(
                                        engine["status"].upper(),
                                        style={
                                            "background": colors["bg"],
                                            "color": colors["text"],
                                            "border": f"1px solid {colors['border']}",
                                            "borderRadius": "8px",
                                            "padding": "4px 10px",
                                            "fontSize": "10px",
                                            "fontWeight": "700",
                                        }
                                    )
                                ]
                            ),
                            html.Div(
                                style={"display": "flex", "justifyContent": "space-between"},
                                children=[
                                    html.Span("Degradation", style={"color": "rgba(180, 210, 255, 0.7)", "fontSize": "12px"}),
                                    html.Span(f"{engine['degradation']}%", style={"color": colors["text"], "fontWeight": "700", "fontSize": "14px"})
                                ]
                            ),
                            html.Div(
                                style={"display": "flex", "justifyContent": "space-between"},
                                children=[
                                    html.Span("Predicted cycles left", style={"color": "rgba(74, 158, 255, 0.7)", "fontSize": "11px"}),
                                    html.Span(f"{engine['rul']}", style={"color": "#4a9eff", "fontWeight": "700", "fontSize": "14px"})
                                ]
                            ),
                            html.Div(
                                style={
                                    "borderTop": "1px solid rgba(74,158,255,0.15)",
                                    "paddingTop": "8px",
                                    "display": "flex",
                                    "justifyContent": "flex-end",
                                    "alignItems": "center",
                                    "gap": "4px",
                                },
                                children=[
                                    html.Span("View details", style={"color": "rgba(74,158,255,0.6)", "fontSize": "11px"}),
                                    html.Span("→", style={"color": "rgba(74,158,255,0.6)", "fontSize": "11px"}),
                                ]
                            )
                        ]
                    )
                ]
            )
        )

    # ── Maintenance alert card builder ──
    def maintenance_alert_card(alert):
        is_critical = alert["severity"] == "critical"
        icon = critical_icon() if is_critical else warning_icon()
        color = "#ff4d4d" if is_critical else "#ffd93d"
        bg = "rgba(255,77,77,0.08)" if is_critical else "rgba(255,217,61,0.08)"

        return dcc.Link(
            href=f"/overview/{alert['db_id']}",
            style={"textDecoration": "none"},
            children=[
                html.Div(
                    style={
                        "background": bg,
                        "border": f"2px solid {color}",
                        "borderRadius": "12px",
                        "padding": "16px",
                        "cursor": "pointer",
                    },
                    children=[
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "8px"},
                            children=[
                                html.Div(
                                    style={"display": "flex", "alignItems": "center", "gap": "10px"},
                                    children=[
                                        icon,
                                        html.Span(f"ENGINE-{alert['engine_id']}", style={"color": color, "fontSize": "18px", "fontWeight": "700"})
                                    ]
                                ),
                                html.Span(alert["severity"].upper(), style={
                                    "background": f"rgba({'255,77,77' if is_critical else '255,217,61'},0.2)",
                                    "color": color, "border": f"1px solid {color}",
                                    "borderRadius": "8px", "padding": "4px 10px",
                                    "fontSize": "10px", "fontWeight": "700",
                                })
                            ]
                        ),
                        html.Div(style={"marginBottom": "4px"}, children=[
                            html.Span(f"RUL = {alert['rul']} cycles", style={"color": "white", "fontSize": "16px"})
                        ]),
                        html.Div(children=[
                            html.Span(alert["action_text"], style={"color": "rgba(255,255,255,0.7)", "fontSize": "14px"})
                        ])
                    ]
                )
            ]
        )

    return html.Div(
        style={
            "minHeight": "100vh",
            "fontFamily": "'Segoe UI', sans-serif",
            "background": "#0a1628",
            "color": "white",
            "padding": "0px",
        },
        children=[
            dcc.Location(id='url-dashboard', refresh=False),
            # ... header unchanged ...
            html.Div(
                style={
                    "background": "linear-gradient(90deg, #0d2045 0%, #071530 100%)",
                    "borderBottom": "1px solid rgba(74, 158, 255, 0.2)",
                    "padding": "16px 32px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                },
                children=[
                    html.H1(
                        "ENGINE PROGNOSTIC MONITORING SYSTEM",
                        style={"margin": "0", "fontSize": "22px", "fontWeight": "700", "color": "white", "letterSpacing": "1px"}
                    ),
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "20px"},
                        children=[
                            dcc.Link(
                                href="/user-management",
                                style={"textDecoration": "none"},
                                children=[
                                    html.Div(
                                        style={
                                            "background": "rgba(74, 158, 255, 0.15)",
                                            "border": "1px solid rgba(74, 158, 255, 0.5)",
                                            "borderRadius": "12px", "padding": "6px 16px",
                                            "display": "flex", "alignItems": "center", "gap": "8px", "cursor": "pointer",
                                        },
                                        children=[html.Span("User Control", style={"color": "#a8d4ff", "fontSize": "14px", "fontWeight": "600"})]
                                    )
                                ]
                            ),
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                children=[
                                    bell_icon(),
                                    html.Span(f"{str(alert_count)} alerts", style={"color": "#ffd93d", "fontSize": "16px", "fontWeight": "700"})
                                ]
                            ),
                            html.Div(
                                id="logout-btn", n_clicks=0,
                                style={"cursor": "pointer", "display": "flex", "alignItems": "center"},
                                children=[logout_icon()]
                            )
                        ]
                    )
                ]
            ),
            html.Div(
                style={"padding": "24px 32px"},
                children=[
                    # ... status cards unchanged ...
                    html.Div(
                        style={"display": "flex", "gap": "20px", "marginBottom": "32px", "justifyContent": "center"},
                        children=[
                            html.Div(style={"background": "linear-gradient(135deg, #2a354a 0%, #1a2335 100%)", "border": "1px solid rgba(255,255,255,0.2)", "borderRadius": "12px", "padding": "16px 24px", "display": "flex", "alignItems": "center", "gap": "20px", "minWidth": "250px", "justifyContent": "space-between"},
                                     children=[html.Span("TOTAL ENGINES", style={"color": "white", "fontSize": "16px", "fontWeight": "600"}), html.Span(str(total_count), style={"color": "white", "fontSize": "36px", "fontWeight": "700"})]),
                            html.Div(style={"background": "linear-gradient(135deg, rgba(0,255,100,0.15) 0%, rgba(0,200,80,0.08) 100%)", "border": "2px solid #00ff64", "borderRadius": "12px", "padding": "16px 24px", "display": "flex", "alignItems": "center", "gap": "20px", "minWidth": "250px", "justifyContent": "space-between"},
                                     children=[html.Span("HEALTHY", style={"color": "#00ff64", "fontSize": "16px", "fontWeight": "600"}), html.Span(str(healthy_count), style={"color": "#00ff64", "fontSize": "36px", "fontWeight": "700"})]),
                            html.Div(style={"background": "linear-gradient(135deg, rgba(255,217,61,0.15) 0%, rgba(255,174,0,0.08) 100%)", "border": "2px solid #ffd93d", "borderRadius": "12px", "padding": "16px 24px", "display": "flex", "alignItems": "center", "gap": "20px", "minWidth": "250px", "justifyContent": "space-between"},
                                     children=[html.Span("DEGRADING", style={"color": "#ffd93d", "fontSize": "16px", "fontWeight": "600"}), html.Span(str(warning_count), style={"color": "#ffd93d", "fontSize": "36px", "fontWeight": "700"})]),
                            html.Div(style={"background": "linear-gradient(135deg, rgba(255,77,77,0.15) 0%, rgba(255,0,0,0.08) 100%)", "border": "2px solid #ff4d4d", "borderRadius": "12px", "padding": "16px 24px", "display": "flex", "alignItems": "center", "gap": "20px", "minWidth": "250px", "justifyContent": "space-between"},
                                     children=[html.Span("CRITICAL", style={"color": "#ff4d4d", "fontSize": "16px", "fontWeight": "600"}), html.Span(str(critical_count), style={"color": "#ff4d4d", "fontSize": "36px", "fontWeight": "700"})]),
                        ]
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "24px"},
                        children=[
                            html.Div(
                                style={"flex": "3"},
                                children=[
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "16px"},
                                        children=[
                                            html.H2("All Engines", style={"margin": "0", "color": "white", "fontSize": "22px", "fontWeight": "700"}),
                                            html.Div(
                                                style={"display": "flex", "gap": "8px"},
                                                children=[
                                                    html.Button("All",      id="filter-all",      n_clicks=1,
                                                                style={"background": "#007bff", "border": "none", "color": "white",
                                                                    "padding": "6px 14px", "borderRadius": "20px", "fontSize": "12px",
                                                                    "fontWeight": "700", "cursor": "pointer"}),
                                                    html.Button("Healthy",  id="filter-healthy",  n_clicks=0,
                                                                style={"background": "rgba(74,158,255,0.15)", "border": "1px solid rgba(74,158,255,0.4)",
                                                                    "color": "#a8d4ff", "padding": "6px 14px", "borderRadius": "20px",
                                                                    "fontSize": "12px", "fontWeight": "700", "cursor": "pointer"}),
                                                    html.Button("Degrading",id="filter-degrading",n_clicks=0,
                                                                style={"background": "rgba(74,158,255,0.15)", "border": "1px solid rgba(74,158,255,0.4)",
                                                                    "color": "#a8d4ff", "padding": "6px 14px", "borderRadius": "20px",
                                                                    "fontSize": "12px", "fontWeight": "700", "cursor": "pointer"}),
                                                    html.Button("Critical", id="filter-critical", n_clicks=0,
                                                                style={"background": "rgba(74,158,255,0.15)", "border": "1px solid rgba(74,158,255,0.4)",
                                                                    "color": "#a8d4ff", "padding": "6px 14px", "borderRadius": "20px",
                                                                    "fontSize": "12px", "fontWeight": "700", "cursor": "pointer"}),
                                                ]
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="engines-grid",
                                        style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "16px"},
                                        children=[engine_card(engine) for engine in engine_data] if engine_data else [
                                            html.Div("No data.", style={"color": "rgba(255,255,255,0.7)", "fontSize": "16px", "textAlign": "center", "padding": "40px 0", "gridColumn": "1 / -1"})
                                        ]
                                    )
                                ]
                            ),
                            # ── Maintenance alerts (now from Supabase) ──
                            html.Div(
                                style={"flex": "1", "background": "#101a2f", "border": "1px solid rgba(74,158,255,0.3)", "borderRadius": "16px", "padding": "20px"},
                                children=[
                                    html.H2("Maintenance alerts", style={"margin": "0 0 16px 0", "color": "white", "fontSize": "22px", "fontWeight": "700"}),
                                    html.Div(
                                        style={"display": "flex", "flexDirection": "column", "gap": "16px"},
                                        children=[maintenance_alert_card(a) for a in maintenance_alerts] if maintenance_alerts else [
                                            html.Div("No active maintenance alerts.",
                                                     style={"color": "rgba(255,255,255,0.5)", "fontSize": "14px", "textAlign": "center", "padding": "20px 0"})
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            ),
            dcc.Store(id="engine-data-store", data=engine_data),
        ]
    )
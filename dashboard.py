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


def create_dashboard_layout(supabase, org_id=None, role=None, username=None, first_name=None):
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
                q = q.eq("is_deleted", True)
                return q

            response     = eng_query().execute()
            total_count  = response.count or 0

            # warning_count / critical_count are derived below from engine_data
            # after applying the fetched thresholds, so the cards and summary
            # always use the same threshold values.

            engine_ids = [e.get("id") for e in (response.data or []) if e.get("id")]

            # Alert count — one per engine (latest active warning/critical only)
            if org_id and not engine_ids:
                alert_count = 0
            else:
                try:
                    ac_query = supabase.table("alert_logs") \
                        .select("engine_id") \
                        .in_("severity", ["warning", "critical"]) \
                        .eq("status", "active")
                    if org_id and engine_ids:
                        ac_query = ac_query.in_("engine_id", engine_ids)
                    ac_resp = ac_query.execute()
                    # Count distinct engines with an active alert
                    alert_count = len({r["engine_id"] for r in (ac_resp.data or []) if r.get("engine_id")})
                except Exception:
                    alert_count = 0

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
                    "rul":         int(round(rul)),
                    "has_prediction": db_id in latest_rul_map,
                    "model_type":  engine.get("model_type", "N/A"),
                    "created_at":  (engine.get("created_at") or "")[:10],
                })

            # ── Derive summary counts from engine_data (uses fetched thresholds) ──
            healthy_count  = sum(1 for e in engine_data if e["status"] == "healthy")
            warning_count  = sum(1 for e in engine_data if e["status"] == "warning")
            critical_count = sum(1 for e in engine_data if e["status"] == "critical")

            print(f"[DEBUG] Parsed engine_data: {engine_data}")

            # ── Fetch maintenance alerts scoped to this org's engines ──
            # One alert per engine: critical beats warning, latest wins within same severity.
            if org_id and not engine_ids:
                pass
            else:
                alert_query = supabase.table("alert_logs") \
                    .select("engine_id, severity, triggered_at") \
                    .in_("severity", ["warning", "critical"]) \
                    .eq("status", "active") \
                    .order("triggered_at", desc=True)

                if org_id and engine_ids:
                    alert_query = alert_query.in_("engine_id", engine_ids)

                alerts_resp = alert_query.execute()

                # Deduplicate: keep one per engine, critical > warning, then latest
                best: dict = {}  # engine_id → alert row
                for alert in (alerts_resp.data or []):
                    eid = alert.get("engine_id")
                    if not eid:
                        continue
                    sev = (alert.get("severity") or "warning").lower()
                    if eid not in best:
                        best[eid] = alert
                    else:
                        existing_sev = best[eid].get("severity", "warning").lower()
                        # Replace if new alert is critical and existing is only warning
                        if sev == "critical" and existing_sev != "critical":
                            best[eid] = alert

                from datetime import datetime as _dt, timezone as _tz

                def _relative_time(ts_str: str) -> str:
                    """Convert ISO timestamp to relative label like '12m ago'."""
                    if not ts_str:
                        return ""
                    try:
                        ts = _dt.fromisoformat(ts_str.replace("Z", "+00:00"))
                        now = _dt.now(_tz.utc)
                        delta = int((now - ts).total_seconds())
                        if delta < 60:
                            return f"{delta}s ago"
                        elif delta < 3600:
                            return f"{delta // 60}m ago"
                        elif delta < 86400:
                            return f"{delta // 3600}h ago"
                        else:
                            return f"{delta // 86400}d ago"
                    except Exception:
                        return ""

                for eid, alert in best.items():
                    # Fetch engine display info
                    try:
                        eng_resp = supabase.table("engines") \
                            .select("id, engine_id") \
                            .eq("id", eid) \
                            .single().execute()
                        eng = eng_resp.data or {}
                    except Exception:
                        eng = {}

                    eng_db_id = eng.get("id") or eid
                    eng_display_id = str(eng.get("engine_id", "?")).zfill(2)
                    severity = (alert.get("severity") or "warning").lower()
                    rul = int(round(latest_rul_map.get(eng_db_id, 0)))
                    rel_time = _relative_time(alert.get("triggered_at", ""))

                    maintenance_alerts.append({
                        "db_id":      eng_db_id,
                        "engine_id":  eng_display_id,
                        "severity":   severity,
                        "rul":        rul,
                        "rel_time":   rel_time,
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
        colors = status_colors[engine["status"]]
        show_maintenance = engine["status"] in ("warning", "critical")
        return html.Div(
            style={"position": "relative"},
            children=[
                dcc.Link(
                    href=f"/overview/{engine['db_id']}",
                    style={"textDecoration": "none", "display": "block"},
                    children=[
                        html.Div(
                            style={
                                "background": "#101a2f",
                                "border": "1px solid rgba(74, 158, 255, 0.2)",
                                "borderRadius": "12px",
                                "padding": "16px 16px 12px",
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "8px",
                                "cursor": "pointer",
                                "transition": "border 0.2s, background 0.2s",
                            },
                            id={"type": "engine-card", "index": engine["db_id"]},
                            children=[
                                html.Div(
                                    style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "paddingBottom": "8px"},
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
                                        html.Span("Model", style={"color": "rgba(180, 210, 255, 0.7)", "fontSize": "12px"}),
                                        html.Span(engine.get("model_type", "N/A"), style={"color": "rgba(200,220,255,0.9)", "fontWeight": "700", "fontSize": "14px"})
                                    ]
                                ),
                                html.Div(
                                    style={"display": "flex", "justifyContent": "space-between"},
                                    children=[
                                        html.Span("Created", style={"color": "rgba(180, 210, 255, 0.7)", "fontSize": "12px"}),
                                        html.Span(engine.get("created_at", "N/A"), style={"color": "rgba(200,220,255,0.9)", "fontWeight": "600", "fontSize": "11px"})
                                    ]
                                ),
                                html.Div(
                                    style={"display": "flex", "justifyContent": "space-between"},
                                    children=[
                                        html.Span("Predicted cycles left", style={"color": "rgba(74, 158, 255, 0.7)", "fontSize": "11px"}),
                                        html.Span(
                                            f"{engine['rul']}" if engine.get("has_prediction") else "Warming up…",
                                            style={
                                                "color": "#4a9eff" if engine.get("has_prediction") else "rgba(168,212,255,0.5)",
                                                "fontWeight": "700", "fontSize": "14px" if engine.get("has_prediction") else "12px",
                                                "fontStyle": "normal" if engine.get("has_prediction") else "italic",
                                            }
                                        )
                                    ]
                                ),
                                # Footer row — spacer keeps height consistent for healthy cards
                                html.Div(
                                    style={
                                        "borderTop": "1px solid rgba(74,158,255,0.15)",
                                        "paddingTop": "8px",
                                        "display": "flex",
                                        "justifyContent": "space-between",
                                        "alignItems": "center",
                                    },
                                    children=[
                                        html.Span(
                                            "Schedule Maintenance",
                                            style={
                                                "visibility": "hidden",
                                                "fontSize": "11px",
                                                "fontWeight": "600",
                                                "padding": "5px 10px",
                                                "display": "inline-block",
                                            }
                                        ),
                                        html.Div(
                                            style={"display": "flex", "alignItems": "center", "gap": "4px"},
                                            children=[
                                                html.Span("View details", style={"color": "rgba(74,158,255,0.6)", "fontSize": "11px"}),
                                                html.Span("→", style={"color": "rgba(74,158,255,0.6)", "fontSize": "11px"}),
                                            ]
                                        ),
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                # Schedule Maintenance — sits at same position as the spacer span above,
                # outside dcc.Link so clicking it goes to a different page.
                html.A(
                    "Schedule Maintenance",
                    href=f"/schedule-maintenance/{engine['db_id']}",
                    style={
                        "position": "absolute",
                        "bottom": "16px",
                        "left": "16px",
                        "visibility": "visible" if show_maintenance else "hidden",
                        "background": "rgba(74,158,255,0.12)",
                        "border": "1px solid rgba(74,158,255,0.45)",
                        "borderRadius": "8px",
                        "color": "#7ab8ff",
                        "fontSize": "11px",
                        "fontWeight": "600",
                        "padding": "5px 10px",
                        "textDecoration": "none",
                        "lineHeight": "1.4",
                        "zIndex": "1",
                    },
                ),
            ]
        )

    # ── Maintenance alert card builder ──
    def maintenance_alert_card(alert):
        is_critical = alert["severity"] == "critical"
        color  = "#ff4d4d" if is_critical else "#ffd93d"
        bg     = "rgba(255,77,77,0.08)" if is_critical else "rgba(255,217,61,0.06)"
        border = "rgba(255,77,77,0.35)" if is_critical else "rgba(255,217,61,0.25)"
        label  = "Escalated to critical" if is_critical else "Warning threshold reached"
        rel    = alert.get("rel_time", "")
        sub    = f"{label} · {rel}" if rel else label

        # Triangle warning icon in matching colour
        tri_svg = (
            f'<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" '
            f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
            f'<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
            f'</svg>'
        )
        import base64 as _b64
        tri_src = "data:image/svg+xml;base64," + _b64.b64encode(tri_svg.encode()).decode()

        return dcc.Link(
            href=f"/alert-log/{alert['db_id']}",
            style={"textDecoration": "none", "display": "block"},
            children=[
                html.Div(
                    style={
                        "background": bg,
                        "border": f"1px solid {border}",
                        "borderLeft": f"3px solid {color}",
                        "borderRadius": "10px",
                        "padding": "12px 14px",
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "12px",
                        "cursor": "pointer",
                    },
                    children=[
                        # Triangle icon
                        html.Img(src=tri_src, style={"width": "20px", "height": "20px", "flexShrink": "0"}),
                        # Text block
                        html.Div(
                            style={"minWidth": "0"},
                            children=[
                                # Engine name + RUL on same line
                                html.Div(
                                    style={"display": "flex", "alignItems": "baseline", "gap": "8px", "marginBottom": "2px"},
                                    children=[
                                        html.Span(
                                            f"ENGINE-{alert['engine_id']}",
                                            style={"color": "white", "fontWeight": "700", "fontSize": "14px"}
                                        ),
                                        html.Span(
                                            f"RUL {alert['rul']}",
                                            style={"color": color, "fontWeight": "700", "fontSize": "13px"}
                                        ),
                                    ]
                                ),
                                # Subtitle
                                html.Div(
                                    sub,
                                    style={
                                        "color": "rgba(168,212,255,0.55)",
                                        "fontSize": "12px",
                                        "whiteSpace": "nowrap",
                                        "overflow": "hidden",
                                        "textOverflow": "ellipsis",
                                    }
                                ),
                            ]
                        ),
                    ]
                )
            ]
        )

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
                            # ── Bell + badge ──
                            html.Div(
                                style={"position": "relative", "display": "flex",
                                       "alignItems": "center", "cursor": "pointer"},
                                children=[
                                    html.Img(
                                        src="data:image/svg+xml;base64," + base64.b64encode(
                                            b'<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="#4a9eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>'
                                        ).decode(),
                                        style={"width": "22px", "height": "22px"},
                                    ),
                                    html.Span(
                                        str(alert_count),
                                        style={
                                            "display": "flex" if alert_count > 0 else "none",
                                            "position": "absolute",
                                            "bottom": "-5px", "right": "-7px",
                                            "background": "#ff4d4d",
                                            "color": "white",
                                            "fontSize": "9px", "fontWeight": "700",
                                            "borderRadius": "50%",
                                            "width": "16px", "height": "16px",
                                            "alignItems": "center", "justifyContent": "center",
                                            "lineHeight": "1",
                                            "border": "1.5px solid #0a1628",
                                        }
                                    ),
                                ]
                            ),

                            # ── User avatar + name/role + click dropdown ──
                            html.Div(
                                id="user-menu-trigger",
                                n_clicks=0,
                                style={
                                    "position": "relative",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "10px",
                                    "cursor": "pointer",
                                    "padding": "4px 6px",
                                    "borderRadius": "10px",
                                },
                                className="user-menu-trigger",
                                children=[
                                    # Circular avatar with first initial
                                    html.Div(
                                        (first_name or username or "U")[0].upper(),
                                        style={
                                            "width": "36px", "height": "36px",
                                            "borderRadius": "50%",
                                            "background": "linear-gradient(135deg, #1e5fa8, #4a9eff)",
                                            "display": "flex", "alignItems": "center",
                                            "justifyContent": "center",
                                            "color": "white", "fontWeight": "700",
                                            "fontSize": "15px", "flexShrink": "0",
                                            "border": "2px solid rgba(74,158,255,0.35)",
                                        }
                                    ),
                                    # Name + role stacked
                                    html.Div(
                                        style={"display": "flex", "flexDirection": "column",
                                               "alignItems": "flex-start"},
                                        children=[
                                            html.Span(
                                                first_name or username or "User",
                                                style={"color": "white", "fontSize": "13px",
                                                       "fontWeight": "600", "lineHeight": "1.3",
                                                       "whiteSpace": "nowrap"}
                                            ),
                                            html.Span(
                                                (role or "user").capitalize(),
                                                style={"color": "rgba(168,212,255,0.6)",
                                                       "fontSize": "11px", "lineHeight": "1.3"}
                                            ),
                                        ]
                                    ),

                                    # Hover dropdown menu
                                    html.Div(
                                        className="user-dropdown-menu",
                                        style={
                                            "display": "none",
                                            "position": "absolute",
                                            "top": "calc(100% + 10px)",
                                            "right": "0",
                                            "minWidth": "185px",
                                            "background": "linear-gradient(135deg, #0d1e3a, #071530)",
                                            "border": "1px solid rgba(74,158,255,0.22)",
                                            "borderRadius": "12px",
                                            "boxShadow": "0 8px 32px rgba(0,0,0,0.55)",
                                            "zIndex": "9999",
                                            "padding": "6px 0",
                                        },
                                        children=[
                                            # Dashboard
                                            dcc.Link(href="/dashboard", style={"textDecoration": "none", "display": "block"},
                                                children=[html.Div(
                                                    className="user-dropdown-item",
                                                    style={"display": "flex", "alignItems": "center",
                                                           "gap": "10px", "padding": "10px 16px",
                                                           "color": "rgba(168,212,255,0.85)", "fontSize": "13px",
                                                           "fontWeight": "500"},
                                                    children=[
                                                        html.Img(src="data:image/svg+xml;base64," + base64.b64encode(b'<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>').decode(), style={"width": "15px", "height": "15px"}),
                                                        "Dashboard",
                                                    ]
                                                )]
                                            ),
                                            # My Schedule
                                            dcc.Link(href="/schedule-maintenance/none", style={"textDecoration": "none", "display": "block"},
                                                children=[html.Div(
                                                    className="user-dropdown-item",
                                                    style={"display": "flex", "alignItems": "center",
                                                           "gap": "10px", "padding": "10px 16px",
                                                           "color": "rgba(168,212,255,0.85)", "fontSize": "13px",
                                                           "fontWeight": "500"},
                                                    children=[
                                                        html.Img(src="data:image/svg+xml;base64," + base64.b64encode(b'<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>').decode(), style={"width": "15px", "height": "15px"}),
                                                        "My Schedule",
                                                    ]
                                                )]
                                            ),
                                            # Admin Control (admin only)
                                            *([
                                                dcc.Link(href="/user-management", style={"textDecoration": "none", "display": "block"},
                                                    children=[html.Div(
                                                        className="user-dropdown-item",
                                                        style={"display": "flex", "alignItems": "center",
                                                               "gap": "10px", "padding": "10px 16px",
                                                               "color": "rgba(168,212,255,0.85)", "fontSize": "13px",
                                                               "fontWeight": "500"},
                                                        children=[
                                                            html.Img(src="data:image/svg+xml;base64," + base64.b64encode(b'<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/><circle cx="19" cy="8" r="2"/><line x1="19" y1="11" x2="19" y2="13"/></svg>').decode(), style={"width": "15px", "height": "15px"}),
                                                            "Admin Control",
                                                        ]
                                                    )]
                                                ),
                                            ] if role == "admin" else []),
                                            # Divider
                                            html.Div(style={"borderTop": "1px solid rgba(74,158,255,0.15)", "margin": "4px 0"}),
                                            # Logout
                                            html.Div(
                                                id="logout-btn", n_clicks=0,
                                                className="user-dropdown-item-danger",
                                                style={"display": "flex", "alignItems": "center",
                                                       "gap": "10px", "padding": "10px 16px",
                                                       "color": "#ff6b6b", "fontSize": "13px",
                                                       "fontWeight": "500", "cursor": "pointer"},
                                                children=[
                                                    html.Img(src="data:image/svg+xml;base64," + base64.b64encode(b'<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="#ff4d4d" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>').decode(), style={"width": "15px", "height": "15px"}),
                                                    "Logout",
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    )
                ]
            ),
            html.Div(
                style={
                    "flex": "1",
                    "minHeight": "0",
                    "display": "flex",
                    "flexDirection": "column",
                    "padding": "24px 32px",
                    "overflow": "hidden",
                },
                children=[
                    # ... status cards unchanged ...
                    html.Div(
                        style={"display": "flex", "gap": "20px", "marginBottom": "24px", "justifyContent": "center", "flexShrink": "0"},
                        children=[
                            html.Div(style={"background": "linear-gradient(135deg, #2a354a 0%, #1a2335 100%)", "border": "1px solid rgba(255,255,255,0.2)", "borderRadius": "12px", "padding": "16px 24px", "display": "flex", "alignItems": "center", "gap": "20px", "minWidth": "250px", "justifyContent": "space-between"},
                                     children=[html.Span("TOTAL ENGINES", style={"color": "white", "fontSize": "16px", "fontWeight": "600"}), html.Span(str(total_count), style={"color": "white", "fontSize": "36px", "fontWeight": "700"})]),
                            html.Div(style={"background": "linear-gradient(135deg, rgba(0,255,100,0.15) 0%, rgba(0,200,80,0.08) 100%)", "border": "1px solid rgb(0,255,100,0.5)", "borderRadius": "12px", "padding": "16px 24px", "display": "flex", "alignItems": "center", "gap": "20px", "minWidth": "250px", "justifyContent": "space-between"},
                                     children=[html.Span("HEALTHY", style={"color": "#00ff64", "fontSize": "16px", "fontWeight": "600"}), html.Span(str(healthy_count), style={"color": "#00ff64", "fontSize": "36px", "fontWeight": "700"})]),
                            html.Div(style={"background": "linear-gradient(135deg, rgba(255,217,61,0.15) 0%, rgba(255,174,0,0.08) 100%)", "border": "1px solid rgb(255,217,61,0.5)", "borderRadius": "12px", "padding": "16px 24px", "display": "flex", "alignItems": "center", "gap": "20px", "minWidth": "250px", "justifyContent": "space-between"},
                                     children=[html.Span("DEGRADING", style={"color": "#ffd93d", "fontSize": "16px", "fontWeight": "600"}), html.Span(str(warning_count), style={"color": "#ffd93d", "fontSize": "36px", "fontWeight": "700"})]),
                            html.Div(style={"background": "linear-gradient(135deg, rgba(255,77,77,0.15) 0%, rgba(255,0,0,0.08) 100%)", "border": "1px solid rgb(255,77,77,0.5)", "borderRadius": "12px", "padding": "16px 24px", "display": "flex", "alignItems": "center", "gap": "20px", "minWidth": "250px", "justifyContent": "space-between"},
                                     children=[html.Span("CRITICAL", style={"color": "#ff4d4d", "fontSize": "16px", "fontWeight": "600"}), html.Span(str(critical_count), style={"color": "#ff4d4d", "fontSize": "36px", "fontWeight": "700"})]),
                        ]
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "24px", "flex": "1", "minHeight": "0"},
                        children=[
                            html.Div(
                                style={"flex": "3", "display": "flex", "flexDirection": "column", "minHeight": "0"},
                                children=[
                                    html.Div(
                                        style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "16px", "flexShrink": "0"},
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
                                        style={
                                            "display": "grid",
                                            "gridTemplateColumns": "repeat(3, 1fr)",
                                            "gap": "16px",
                                            "overflowY": "auto",
                                            "flex": "1",
                                            "minHeight": "0",
                                            "paddingRight": "4px",
                                        },
                                        children=[engine_card(engine) for engine in engine_data] if engine_data else [
                                            html.Div("No data.", style={"color": "rgba(255,255,255,0.7)", "fontSize": "16px", "textAlign": "center", "padding": "40px 0", "gridColumn": "1 / -1"})
                                        ]
                                    )
                                ]
                            ),
                            # ── Maintenance alerts (now from Supabase) ──
                            html.Div(
                                style={
                                    "flex": "1",
                                    "minHeight": "0",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "background": "#101a2f",
                                    "border": "1px solid rgba(74,158,255,0.3)",
                                    "borderRadius": "16px",
                                    "padding": "20px",
                                },
                                children=[
                                    html.H2("Maintenance alerts", style={"margin": "0 0 16px 0", "color": "white", "fontSize": "22px", "fontWeight": "700", "flexShrink": "0"}),
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "gap": "16px",
                                            "overflowY": "auto",
                                            "flex": "1",
                                            "minHeight": "0",
                                        },
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
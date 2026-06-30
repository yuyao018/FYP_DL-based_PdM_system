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
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 15 V10 Q18 6 12 6 Q6 6 6 10 V15 M12 21 Q10 21 10 19 Q10 17 12 17 Q14 17 14 19 Q14 21 12 21" fill="none" stroke="#ffd93d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    '''.encode('utf-8')).decode('utf-8')
    return html.Img(src=f'data:image/svg+xml;base64,{svg_base64}', style={'width': '28px', 'height': '28px'})


def logout_icon():
    svg_base64 = base64.b64encode('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M9 21 H5 Q4 21 4 20 V4 Q4 3 5 3 H9 M15 17 L20 12 L15 7 M10 12 H20" fill="none" stroke="#ff4d4d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    '''.encode('utf-8')).decode('utf-8')
    return html.Img(src=f'data:image/svg+xml;base64,{svg_base64}', style={'width': '28px', 'height': '28px'})


def create_dashboard_layout(supabase):
    engine_data = []
    try:
        if supabase:
            response = supabase.table("engines").select("*").execute()
            print(f"[DEBUG] Raw rows: {response.data}")

            for engine in (response.data or []):
                raw_status = (engine.get("condition_status") or "healthy").lower().strip()
                if raw_status not in ("healthy", "warning", "critical"):
                    raw_status = "healthy"

                current_cycle = engine.get("current_cycle") or 0
                # Derive a rough RUL from current_cycle (adjust max_life to your dataset)
                max_life = 100
                rul = max(0, max_life - current_cycle)
                degradation = max(0, min(100, int((rul / max_life) * 100)))

                engine_data.append({
                    "db_id":       engine.get("id"),
                    "id":          str(engine.get("engine_id", "?")).zfill(2),
                    "status":      raw_status,
                    "degradation": degradation,
                    "rul":         rul,
                })

            print(f"[DEBUG] Parsed engine_data: {engine_data}")

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
        return html.Div(
            # Make the card a clickable link
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
                            # Subtle "view details" hint at the bottom
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
            # Header
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
                        style={
                            "margin": "0",
                            "fontSize": "22px",
                            "fontWeight": "700",
                            "color": "white",
                            "letterSpacing": "1px"
                        }
                    ),
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "20px"},
                        children=[
                            html.Div(
                                style={
                                    "background": "rgba(74, 158, 255, 0.15)",
                                    "border": "1px solid rgba(74, 158, 255, 0.5)",
                                    "borderRadius": "12px",
                                    "padding": "6px 16px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "8px",
                                },
                                children=[
                                    html.Span("User Control", style={"color": "#a8d4ff", "fontSize": "14px", "fontWeight": "600"})
                                ]
                            ),
                            html.Div(
                                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                                children=[
                                    bell_icon(),
                                    html.Span("2 alerts", style={"color": "#ffd93d", "fontSize": "16px", "fontWeight": "700"})
                                ]
                            ),
                            html.Div(
                                id="logout-btn",
                                n_clicks=0,
                                style={"cursor": "pointer", "display": "flex", "alignItems": "center"},
                                children=[logout_icon()]
                            )
                        ]
                    )
                ]
            ),
            # Main content
            html.Div(
                style={"padding": "24px 32px"},
                children=[
                    # Status cards
                    html.Div(
                        style={"display": "flex", "gap": "20px", "marginBottom": "32px", "justifyContent": "center"},
                        children=[
                            html.Div(
                                style={
                                    "background": "linear-gradient(135deg, #2a354a 0%, #1a2335 100%)",
                                    "border": "1px solid rgba(255,255,255,0.2)",
                                    "borderRadius": "12px",
                                    "padding": "16px 24px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "20px",
                                    "minWidth": "250px",
                                    "justifyContent": "space-between"
                                },
                                children=[
                                    html.Span("TOTAL ENGINES", style={"color": "white", "fontSize": "16px", "fontWeight": "600"}),
                                    html.Span("3", style={"color": "white", "fontSize": "36px", "fontWeight": "700"})
                                ]
                            ),
                            html.Div(
                                style={
                                    "background": "linear-gradient(135deg, rgba(0,255,100,0.15) 0%, rgba(0,200,80,0.08) 100%)",
                                    "border": "2px solid #00ff64",
                                    "borderRadius": "12px",
                                    "padding": "16px 24px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "20px",
                                    "minWidth": "250px",
                                    "justifyContent": "space-between"
                                },
                                children=[
                                    html.Span("HEALTHY", style={"color": "#00ff64", "fontSize": "16px", "fontWeight": "600"}),
                                    html.Span("1", style={"color": "#00ff64", "fontSize": "36px", "fontWeight": "700"})
                                ]
                            ),
                            html.Div(
                                style={
                                    "background": "linear-gradient(135deg, rgba(255,217,61,0.15) 0%, rgba(255,174,0,0.08) 100%)",
                                    "border": "2px solid #ffd93d",
                                    "borderRadius": "12px",
                                    "padding": "16px 24px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "20px",
                                    "minWidth": "250px",
                                    "justifyContent": "space-between"
                                },
                                children=[
                                    html.Span("DEGRADING", style={"color": "#ffd93d", "fontSize": "16px", "fontWeight": "600"}),
                                    html.Span("1", style={"color": "#ffd93d", "fontSize": "36px", "fontWeight": "700"})
                                ]
                            ),
                            html.Div(
                                style={
                                    "background": "linear-gradient(135deg, rgba(255,77,77,0.15) 0%, rgba(255,0,0,0.08) 100%)",
                                    "border": "2px solid #ff4d4d",
                                    "borderRadius": "12px",
                                    "padding": "16px 24px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "20px",
                                    "minWidth": "250px",
                                    "justifyContent": "space-between"
                                },
                                children=[
                                    html.Span("CRITICAL", style={"color": "#ff4d4d", "fontSize": "16px", "fontWeight": "600"}),
                                    html.Span("1", style={"color": "#ff4d4d", "fontSize": "36px", "fontWeight": "700"})
                                ]
                            )
                        ]
                    ),
                    # Engines grid + alerts
                    html.Div(
                        style={"display": "flex", "gap": "24px"},
                        children=[
                            # Engines section
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
                                                    html.Button("All", style={"background": "#007bff", "border": "none", "color": "white", "padding": "6px 14px", "borderRadius": "20px", "fontSize": "12px", "fontWeight": "700", "cursor": "pointer"}),
                                                    html.Button("Healthy", style={"background": "rgba(74,158,255,0.15)", "border": "1px solid rgba(74,158,255,0.4)", "color": "#a8d4ff", "padding": "6px 14px", "borderRadius": "20px", "fontSize": "12px", "fontWeight": "700", "cursor": "pointer"}),
                                                    html.Button("Degrading", style={"background": "rgba(74,158,255,0.15)", "border": "1px solid rgba(74,158,255,0.4)", "color": "#a8d4ff", "padding": "6px 14px", "borderRadius": "20px", "fontSize": "12px", "fontWeight": "700", "cursor": "pointer"}),
                                                    html.Button("Critical", style={"background": "rgba(74,158,255,0.15)", "border": "1px solid rgba(74,158,255,0.4)", "color": "#a8d4ff", "padding": "6px 14px", "borderRadius": "20px", "fontSize": "12px", "fontWeight": "700", "cursor": "pointer"})
                                                ]
                                            )
                                        ]
                                    ),
                                    html.Div(
                                        style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "16px"},
                                        children=[engine_card(engine) for engine in engine_data] if engine_data else [
                                            html.Div(
                                                "No data.",
                                                style={
                                                    "color": "rgba(255,255,255,0.7)",
                                                    "fontSize": "16px",
                                                    "textAlign": "center",
                                                    "padding": "40px 0",
                                                    "gridColumn": "1 / -1"
                                                }
                                            )
                                        ]
                                    )
                                ]
                            ),
                            # Maintenance alerts
                            html.Div(
                                style={"flex": "1", "background": "#101a2f", "border": "1px solid rgba(74,158,255,0.3)", "borderRadius": "16px", "padding": "20px"},
                                children=[
                                    html.H2("Maintenance alerts", style={"margin": "0 0 16px 0", "color": "white", "fontSize": "22px", "fontWeight": "700"}),
                                    html.Div(
                                        style={"display": "flex", "flexDirection": "column", "gap": "16px"},
                                        children=[
                                            html.Div(
                                                style={
                                                    "background": "rgba(255,217,61,0.08)",
                                                    "border": "2px solid #ffd93d",
                                                    "borderRadius": "12px",
                                                    "padding": "16px"
                                                },
                                                children=[
                                                    html.Div(
                                                        style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "8px"},
                                                        children=[
                                                            html.Div(
                                                                style={"display": "flex", "alignItems": "center", "gap": "10px"},
                                                                children=[
                                                                    warning_icon(),
                                                                    html.Span("ENGINE-04", style={"color": "#ffd93d", "fontSize": "18px", "fontWeight": "700"})
                                                                ]
                                                            ),
                                                            html.Span("WARNING", style={"background": "rgba(255,217,61,0.2)", "color": "#ffd93d", "border": "1px solid #ffd93d", "borderRadius": "8px", "padding": "4px 10px", "fontSize": "10px", "fontWeight": "700"})
                                                        ]
                                                    ),
                                                    html.Div(
                                                        style={"marginBottom": "4px"},
                                                        children=[html.Span("RUL = 45 cycles", style={"color": "white", "fontSize": "16px"})]
                                                    ),
                                                    html.Div(
                                                        children=[html.Span("Schedule Maintenance", style={"color": "rgba(255,255,255,0.7)", "fontSize": "14px"})]
                                                    )
                                                ]
                                            ),
                                            html.Div(
                                                style={
                                                    "background": "rgba(255,77,77,0.08)",
                                                    "border": "2px solid #ff4d4d",
                                                    "borderRadius": "12px",
                                                    "padding": "16px"
                                                },
                                                children=[
                                                    html.Div(
                                                        style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "8px"},
                                                        children=[
                                                            html.Div(
                                                                style={"display": "flex", "alignItems": "center", "gap": "10px"},
                                                                children=[
                                                                    critical_icon(),
                                                                    html.Span("ENGINE-09", style={"color": "#ff4d4d", "fontSize": "18px", "fontWeight": "700"})
                                                                ]
                                                            ),
                                                            html.Span("CRITICAL", style={"background": "rgba(255,77,77,0.2)", "color": "#ff4d4d", "border": "1px solid #ff4d4d", "borderRadius": "8px", "padding": "4px 10px", "fontSize": "10px", "fontWeight": "700"})
                                                        ]
                                                    ),
                                                    html.Div(
                                                        style={"marginBottom": "4px"},
                                                        children=[html.Span("RUL = 20 cycles", style={"color": "white", "fontSize": "16px"})]
                                                    ),
                                                    html.Div(
                                                        children=[html.Span("Immediate Maintenance", style={"color": "rgba(255,255,255,0.7)", "fontSize": "14px"})]
                                                    )
                                                ]
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )
import base64
from dash import html

def _svg_img(svg_str, size="22px"):
    b64 = base64.b64encode(svg_str.strip().encode("utf-8")).decode("utf-8")
    return html.Img(
        src=f"data:image/svg+xml;base64,{b64}",
        style={"width": size, "height": size, "flexShrink": "0"},
    )


def icon_dashboard():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1"/>
      <rect x="14" y="3" width="7" height="7" rx="1"/>
      <rect x="3" y="14" width="7" height="7" rx="1"/>
      <rect x="14" y="14" width="7" height="7" rx="1"/>
    </svg>''')


def icon_overview():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="7"/>
      <line x1="16.5" y1="16.5" x2="21" y2="21"/>
    </svg>''')


def icon_sensor():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="3 17 7 11 11 14 15 8 21 8"/>
      <line x1="3" y1="21" x2="21" y2="21"/>
    </svg>''')


def icon_shap():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 2v3M12 19v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12
               M2 12h3M19 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/>
    </svg>''')


def icon_alert():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>''')


def icon_sidebar():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <line x1="9" y1="3" x2="9" y2="21"/>
    </svg>''', size="26px")


def icon_logout():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#ff4d4d" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>''', size="22px")

def build_sidebar(active_page="overview", engine_db_id=None):
    nav_item_base = {
        "display": "flex",
        "alignItems": "center",
        "gap": "10px",
        "padding": "10px 14px",
        "borderRadius": "10px",
        "cursor": "pointer",
        "fontSize": "14px",
        "fontWeight": "500",
        "color": "#a8d4ff",
        "marginBottom": "4px",
        "transition": "background 0.2s",
    }

    def nav_link(icon_fn, label, page_key, href="/"):
        is_active = active_page == page_key
        style = {**nav_item_base}
        if is_active:
            style.update({
                "background": "rgba(74,158,255,0.18)",
                "color": "white",
                "fontWeight": "700",
                "borderLeft": "3px solid #4a9eff",
                "paddingLeft": "11px",
            })
        return html.A(
            href=href,
            style={"textDecoration": "none"},
            children=[
                html.Div(style=style, children=[icon_fn(), html.Span(label)])
            ]
        )

    # Build navigation links with engine_db_id if available
    overview_href = f"/overview/{engine_db_id}" if engine_db_id else "/dashboard"
    sensor_href = f"/sensor-trends/{engine_db_id}" if engine_db_id else "/sensor-trends"
    degradation_analysis_href = f"/degradation-analysis/{engine_db_id}" if engine_db_id else "/degradation-analysis"
    alert_href = f"/alert-log/{engine_db_id}" if engine_db_id else "/alert-log"

    return html.Div(
        id="sidebar",
        style={
            "width": "210px",
            "height": "calc(100vh - 60px)",
            "maxHeight": "calc(100vh - 60px)",
            "flexShrink": "0",
            "background": "#0d1e3a",
            "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex",
            "flexDirection": "column",
            "overflow": "hidden",
            "transition": "width 0.3s ease",
        },
        children=[
            # ── Dashboard top link ──
            html.A(
                href="/dashboard",
                style={"textDecoration": "none", "flexShrink": "0"},
                children=[
                    html.Div(
                        style={
                            "padding": "20px 20px 18px",
                            "borderBottom": "1px solid rgba(74,158,255,0.12)",
                            "display": "flex",
                            "alignItems": "center",
                            "gap": "10px",
                            "cursor": "pointer",
                        },
                        children=[
                            icon_dashboard(),
                            html.Span(
                                "Dashboard",
                                style={
                                    "color": "#a8d4ff",
                                    "fontWeight": "700",
                                    "fontSize": "15px",
                                    "whiteSpace": "nowrap",
                                }
                            ),
                        ]
                    )
                ]
            ),

            # ── Navigation links (scrollable if needed) ──
            html.Div(
                style={"padding": "18px 12px 0", "flex": "1", "minHeight": "0", "overflowY": "auto"},
                children=[
                    html.Div(
                        "NAVIGATION",
                        style={
                            "color": "rgba(168,212,255,0.5)",
                            "fontSize": "10px",
                            "fontWeight": "700",
                            "letterSpacing": "1.5px",
                            "padding": "0 6px",
                            "marginBottom": "10px",
                            "whiteSpace": "nowrap",
                        }
                    ),
                    nav_link(icon_overview, "Overview",        "overview",     overview_href),
                    nav_link(icon_sensor,   "Sensor Trends",   "sensor",       sensor_href),
                    nav_link(icon_shap,     "Degradation Analysis","degradation_analysis",degradation_analysis_href),
                    nav_link(icon_alert,    "Alert Log",       "alert",        alert_href),
                ]
            ),

            # ── Logged-in user + logout ──
            html.Div(
                style={
                    "padding": "16px 20px",
                    "borderTop": "1px solid rgba(74,158,255,0.12)",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "gap": "8px",
                    "flexShrink": "0",
                },
                children=[
                    html.Div(
                        style={"minWidth": "0"},
                        children=[
                            html.Div(
                                "LOGGED IN AS",
                                style={
                                    "color": "rgba(168,212,255,0.5)",
                                    "fontSize": "9px",
                                    "fontWeight": "700",
                                    "letterSpacing": "1.2px",
                                    "marginBottom": "2px",
                                    "whiteSpace": "nowrap",
                                }
                            ),
                            html.Div(
                                "admin_ds",
                                style={
                                    "color": "white",
                                    "fontWeight": "700",
                                    "fontSize": "13px",
                                    "whiteSpace": "nowrap",
                                    "overflow": "hidden",
                                    "textOverflow": "ellipsis",
                                }
                            ),
                            html.Div(
                                "Admin",
                                style={
                                    "color": "rgba(168,212,255,0.6)",
                                    "fontSize": "11px",
                                    "whiteSpace": "nowrap",
                                }
                            ),
                        ]
                    ),
                    html.Div(
                        id="logout-btn",
                        n_clicks=0,
                        style={"cursor": "pointer", "flexShrink": "0"},
                        children=[icon_logout()]
                    )
                ]
            )
        ]
    )

def build_topbar():
    return html.Div(
        style={
            "background": "linear-gradient(90deg, #0d2045 0%, #071530 100%)",
            "borderBottom": "1px solid rgba(74,158,255,0.18)",
            "padding": "0 28px",
            "height": "60px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "flexShrink": "0",
        },
        children=[
            html.H1(
                "ENGINE PROGNOSTIC MONITORING SYSTEM",
                style={
                    "margin": "0",
                    "fontSize": "18px",
                    "fontWeight": "700",
                    "color": "white",
                    "letterSpacing": "1.2px",
                }
            ),
            html.Div(
                id="sidebar-toggle",
                n_clicks=0,
                style={"cursor": "pointer"},
                children=[icon_sidebar()]
            ),
        ]
    )
import base64
from dash import html

def _svg_img(svg_str, size="22px"):
    b64 = base64.b64encode(svg_str.strip().encode("utf-8")).decode("utf-8")
    return html.Img(
        src=f"data:image/svg+xml;base64,{b64}",
        style={"width": size, "height": size, "flexShrink": "0"},
    )

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
        <circle cx="50" cy="50" r="4" fill="#4a9eff"/>
    </svg>
    '''.encode('utf-8')).decode('utf-8')
    return html.Img(src=f'data:image/svg+xml;base64,{gear_svg_base64}', style={'width': '28px', 'height': '28px'})

def org_icon():
    return _svg_img('''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <rect x="3" y="6" width="7" height="15" rx="1" fill="none" stroke="#4a9eff" stroke-width="1.8"/>
        <rect x="14" y="3" width="7" height="18" rx="1" fill="none" stroke="#4a9eff" stroke-width="1.8"/>
        <line x1="5" y1="9" x2="8" y2="9" stroke="#4a9eff" stroke-width="1.2"/>
        <line x1="5" y1="12" x2="8" y2="12" stroke="#4a9eff" stroke-width="1.2"/>
        <line x1="5" y1="15" x2="8" y2="15" stroke="#4a9eff" stroke-width="1.2"/>
        <line x1="16" y1="6" x2="19" y2="6" stroke="#4a9eff" stroke-width="1.2"/>
        <line x1="16" y1="9" x2="19" y2="9" stroke="#4a9eff" stroke-width="1.2"/>
        <line x1="16" y1="12" x2="19" y2="12" stroke="#4a9eff" stroke-width="1.2"/>
        <line x1="16" y1="15" x2="19" y2="15" stroke="#4a9eff" stroke-width="1.2"/>
    </svg>
    ''', size="24px")

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

def icon_users():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="9" cy="8" r="3.2"/>
      <path d="M3 20c0-3.6 2.7-6 6-6s6 2.4 6 6"/>
      <circle cx="17" cy="8" r="2.4"/>
      <path d="M21 20c0-2.8-1.6-5-4-5.7"/>
    </svg>''')

def icon_engine():
    return _svg_img('''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="48" fill="none" stroke="#4a9eff" stroke-width="1.5"/>
        <circle cx="50" cy="50" r="18" fill="none" stroke="#4a9eff" stroke-width="2"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(0 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(45 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(90 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8" transform="rotate(135 50 50)"/>
        <circle cx="50" cy="50" r="4" fill="#4a9eff"/>
    </svg>''', size="22px")

def icon_upload():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 16V4M12 4l-4 4M12 4l4 4"/>
      <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>
    </svg>''')

def icon_threshold():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <line x1="4" y1="6" x2="20" y2="6"/><circle cx="14" cy="6" r="2" fill="#0d1e3a"/>
      <line x1="4" y1="12" x2="20" y2="12"/><circle cx="8" cy="12" r="2" fill="#0d1e3a"/>
      <line x1="4" y1="18" x2="20" y2="18"/><circle cx="16" cy="18" r="2" fill="#0d1e3a"/>
    </svg>''')

def icon_model_upload():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 16V4M12 4l-4 4M12 4l4 4"/>
      <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>
    </svg>''')

def icon_new_org():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <line x1="12" y1="8" x2="12" y2="16"/>
      <line x1="8" y1="12" x2="16" y2="12"/>
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

def icon_sliders():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/>
      <line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>
      <line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>
      <circle cx="4" cy="12" r="2"/><circle cx="12" cy="10" r="2"/><circle cx="20" cy="14" r="2"/>
    </svg>''')

def activity_icon():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#4a9eff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>''', size="20px")

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

def build_admin_sidebar(active_page="engines"):
    nav_item_base = {
        "display": "flex", "alignItems": "center", "gap": "10px",
        "padding": "10px 14px", "borderRadius": "10px", "cursor": "pointer",
        "fontSize": "14px", "fontWeight": "500", "color": "#a8d4ff",
        "marginBottom": "4px", "whiteSpace": "nowrap",
    }

    def nav_link(icon_fn, label, page_key, href="/"):
        style = {**nav_item_base}
        if active_page == page_key:
            style.update({
                "background": "rgba(74,158,255,0.18)", "color": "white",
                "fontWeight": "700", "borderLeft": "3px solid #4a9eff", "paddingLeft": "11px",
            })
        return html.A(href=href, style={"textDecoration": "none"},
                      children=[html.Div(style=style, children=[icon_fn(), html.Span(label)])])

    return html.Div(
        id="sidebar",
        style={
            "width": "210px", "flexShrink": "0",
            "height": "calc(100vh - 60px)", "maxHeight": "calc(100vh - 60px)",
            "background": "#0d1e3a", "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex", "flexDirection": "column",
            "overflow": "hidden", "transition": "width 0.3s ease",
        },
        children=[
            html.A(href="/dashboard", style={"textDecoration": "none", "flexShrink": "0"}, children=[
                html.Div(style={
                    "padding": "20px 20px 18px",
                    "borderBottom": "1px solid rgba(74,158,255,0.12)",
                    "display": "flex", "alignItems": "center", "gap": "10px", "cursor": "pointer",
                }, children=[
                    icon_dashboard(),
                    html.Span("Dashboard", style={"color": "#a8d4ff", "fontWeight": "700",
                                                   "fontSize": "15px", "whiteSpace": "nowrap"}),
                ])
            ]),
            html.Div(style={"padding": "18px 12px 0"}, children=[
                html.Div("ADMIN PANEL", style={
                    "color": "rgba(168,212,255,0.5)", "fontSize": "10px", "fontWeight": "700",
                    "letterSpacing": "1.5px", "padding": "0 6px", "marginBottom": "10px",
                }),
                nav_link(icon_engine,    "Engine Management", "engines",   "/engine-management"),
                nav_link(icon_users,     "User Management",  "users",     "/user-management"),
                nav_link(icon_threshold, "Alert Thresholds", "threshold", "/alert-thresholds"),
            ]),
            html.Div(style={"flex": "1"}),
            html.Div(style={
                "padding": "16px 20px", "borderTop": "1px solid rgba(74,158,255,0.12)",
                "display": "flex", "alignItems": "center", "justifyContent": "space-between",
            }, children=[
                html.Div(children=[
                    html.Div("LOGGED IN AS", style={"color": "rgba(168,212,255,0.5)", "fontSize": "9px",
                                                     "fontWeight": "700", "letterSpacing": "1.2px",
                                                     "marginBottom": "2px"}),
                    html.Div("admin_ds", style={"color": "white", "fontWeight": "700", "fontSize": "13px"}),
                    html.Div("Admin", style={"color": "rgba(168,212,255,0.6)", "fontSize": "11px"}),
                ]),
                html.Div(id="logout-btn", n_clicks=0, style={"cursor": "pointer"},
                         children=[icon_logout()])
            ])
        ]
    )

def build_dev_sidebar(active_page="dashboard"):
    """Build sidebar for developer pages: Dashboard, Model Upload, New Organization."""
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
            children=[html.Div(style=style, children=[icon_fn(), html.Span(label)])]
        )

    return html.Div(
        id="sidebar",
        style={
            "width": "210px",
            "flexShrink": "0",
            "height": "calc(100vh - 60px)",
            "maxHeight": "calc(100vh - 60px)",
            "background": "#0d1e3a",
            "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex",
            "flexDirection": "column",
            "padding": "0",
            "overflow": "hidden",
            "transition": "width 0.3s ease",
        },
        children=[
            # ── Dashboard top link ──
            html.A(
                href="/dev-dashboard",
                style={"textDecoration": "none"},
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
                            html.Span("Dev Dashboard", style={
                                "color": "#a8d4ff", "fontWeight": "700",
                                "fontSize": "15px", "whiteSpace": "nowrap",
                            }),
                        ]
                    )
                ]
            ),

            # ── Navigation links ──
            html.Div(
                style={"padding": "18px 12px 0"},
                children=[
                    html.Div("DEVELOPER PANEL", style={
                        "color": "rgba(168,212,255,0.5)",
                        "fontSize": "10px", "fontWeight": "700",
                        "letterSpacing": "1.5px", "padding": "0 6px",
                        "marginBottom": "10px", "whiteSpace": "nowrap",
                    }),
                    nav_link(icon_model_upload, "Model Upload", "model_upload", "/model-upload"),
                    nav_link(icon_new_org, "New Organization", "new_org", "/dev-new-organization"),
                ]
            ),

            # ── Spacer ──
            html.Div(style={"flex": "1"}),

            # ── Logged-in user + logout ──
            html.Div(
                style={
                    "padding": "16px 20px",
                    "borderTop": "1px solid rgba(74,158,255,0.12)",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                },
                children=[
                    html.Div(children=[
                        html.Div("LOGGED IN AS", style={
                            "color": "rgba(168,212,255,0.5)",
                            "fontSize": "9px", "fontWeight": "700",
                            "letterSpacing": "1.2px", "marginBottom": "2px",
                        }),
                        html.Div("Developer", style={
                            "color": "white", "fontWeight": "700", "fontSize": "13px",
                        }),
                    ]),
                    html.Div(
                        id="dev-logout-btn", n_clicks=0,
                        style={"cursor": "pointer"},
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
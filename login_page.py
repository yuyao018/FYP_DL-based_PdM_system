import dash
from dash import dcc, html
import base64

# ── SVG icons as base64 encoded images ──────────────────────────────────────────────────────────────────

# Gear SVG
GEAR_SVG_BASE64 = base64.b64encode('''
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

GEAR_SVG = html.Img(src=f'data:image/svg+xml;base64,{GEAR_SVG_BASE64}', style={'width': '160px', 'height': '160px'})

# User SVG
USER_SVG_BASE64 = base64.b64encode('''
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <circle cx="32" cy="20" r="10" fill="none" stroke="white" stroke-width="2.5"/>
    <path d="M10 54 Q10 38 32 38 Q54 38 54 54" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
    <path d="M20 20 Q20 8 32 8 Q44 8 44 20" fill="white" stroke="white" stroke-width="1"/>
    <rect x="16" y="19" width="32" height="4" rx="2" fill="white"/>
</svg>
'''.encode('utf-8')).decode('utf-8')

USER_ICON = html.Img(src=f'data:image/svg+xml;base64,{USER_SVG_BASE64}', style={'width': '44px', 'height': '44px', 'marginBottom': '6px'})

# Admin SVG
ADMIN_SVG_BASE64 = base64.b64encode('''
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
    <path d="M32 6 L54 16 L54 34 Q54 50 32 58 Q10 50 10 34 L10 16 Z" fill="none" stroke="rgba(255,255,255,0.45)" stroke-width="2.5"/>
    <circle cx="32" cy="28" r="9" fill="none" stroke="rgba(255,255,255,0.45)" stroke-width="2"/>
    <path d="M20 46 Q20 36 32 36 Q44 36 44 46" fill="none" stroke="rgba(255,255,255,0.45)" stroke-width="2" stroke-linecap="round"/>
</svg>
'''.encode('utf-8')).decode('utf-8')

ADMIN_ICON = html.Img(src=f'data:image/svg+xml;base64,{ADMIN_SVG_BASE64}', style={'width': '44px', 'height': '44px', 'marginBottom': '6px'})

# Person SVG
PERSON_SVG_BASE64 = base64.b64encode('''
<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="7" r="4" fill="none" stroke="#4a9eff" stroke-width="1.8"/>
    <path d="M4 21 Q4 15 12 15 Q20 15 20 21" fill="none" stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round"/>
</svg>
'''.encode('utf-8')).decode('utf-8')

PERSON_ICON = html.Img(src=f'data:image/svg+xml;base64,{PERSON_SVG_BASE64}', style={'width': '18px', 'height': '18px', 'minWidth': '18px'})

# Lock SVG
LOCK_SVG_BASE64 = base64.b64encode('''
<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <rect x="5" y="11" width="14" height="10" rx="2" fill="none" stroke="#4a9eff" stroke-width="1.8"/>
    <path d="M8 11 V8 Q8 4 12 4 Q16 4 16 8 V11" fill="none" stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round"/>
    <circle cx="12" cy="16" r="1.5" fill="#4a9eff"/>
</svg>
'''.encode('utf-8')).decode('utf-8')

LOCK_ICON = html.Img(src=f'data:image/svg+xml;base64,{LOCK_SVG_BASE64}', style={'width': '18px', 'height': '18px', 'minWidth': '18px'})


# ── Feature icons (left panel) ─────────────────────────────────────────────────
def feature_icon(path_d, label):
    # Create SVG string, then encode to base64
    svg_str = f'''
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="{path_d}" fill="none" stroke="rgba(180,210,255,0.85)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    '''
    svg_b64 = base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')
    
    return html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px",
                           "marginBottom": "18px"},
        children=[
            html.Img(src=f'data:image/svg+xml;base64,{svg_b64}', style={'width': '22px', 'height': '22px', 'minWidth': '22px'}),
            html.Span(label, style={"color": "rgba(180,210,255,0.85)", "fontSize": "14px",
                                    "letterSpacing": "0.3px"})
        ]
    )

# ── Login page layout function ────────────────────────────────────────────────────
def create_login_layout():
    return html.Div(
        style={
            "display": "flex", "minHeight": "100vh", "fontFamily": "'Segoe UI', sans-serif",
            "background": "#0a1628",
        },
        children=[
            # ── Left panel ──
            html.Div(
                style={
                    "width": "48%", "background": "linear-gradient(160deg, #0d2045 0%, #071530 100%)",
                    "display": "flex", "flexDirection": "column", "alignItems": "center",
                    "justifyContent": "center", "padding": "60px 48px",
                    "borderRight": "1px solid rgba(74,158,255,0.15)",
                },
                children=[
                    # Gear logo
                    html.Div(
                        style={
                            "width": "190px", "height": "190px", "borderRadius": "50%",
                            "border": "1.5px solid rgba(74,158,255,0.3)",
                            "display": "flex", "alignItems": "center", "justifyContent": "center",
                            "marginBottom": "36px",
                            "background": "radial-gradient(circle, rgba(74,158,255,0.06) 0%, transparent 70%)",
                        },
                        children=[GEAR_SVG]
                    ),
                    html.H1("ENGINE PROGNOSTIC", style={
                        "color": "white", "fontWeight": "700", "fontSize": "22px",
                        "letterSpacing": "2px", "textAlign": "center", "margin": "0",
                        "lineHeight": "1.35",
                    }),
                    html.H1("MONITORING SYSTEM", style={
                        "color": "white", "fontWeight": "700", "fontSize": "22px",
                        "letterSpacing": "2px", "textAlign": "center",
                        "marginTop": "2px", "marginBottom": "48px",
                    }),
                    # Features
                    feature_icon(
                        "M12 2 C6.5 2 2 6.5 2 12 C2 17.5 6.5 22 12 22 M15 9 Q18 9 20 12 Q18 15 15 15 Q12 15 12 12 Q12 9 15 9 M12 12 L19 12",
                        "Hybrid DL Model"
                    ),
                    feature_icon(
                        "M3 17 L8 11 L13 14 L18 7 L22 10 M22 10 L22 6 M22 10 L18 10",
                        "Real-time RUL Prediction"
                    ),
                    feature_icon(
                        "M12 2 Q14 5 12 8 Q10 5 12 2 M6 6 Q9 8 8 11 Q5 9 6 6 M18 6 Q19 9 16 11 Q15 8 18 6 M12 22 Q10 19 12 16 Q14 19 12 22 M4 14 Q7 12 10 14 Q8 17 4 14 M20 14 Q16 17 14 14 Q17 12 20 14 M12 12 C12 12 12 12 12 12",
                        "SHAP Explainability"
                    ),
                ]
            ),

            # ── Right panel ──
            html.Div(
                style={
                    "width": "52%", "display": "flex", "flexDirection": "column",
                    "alignItems": "center", "justifyContent": "center",
                    "padding": "60px 64px",
                    "background": "linear-gradient(170deg, #0c1e3d 0%, #071530 100%)",
                },
                children=[
                    html.H2("Sign In to Your Account", style={
                        "color": "white", "fontWeight": "700", "fontSize": "28px",
                        "marginBottom": "8px", "textAlign": "center",
                    }),
                    html.P("Select Your Role and Enter Credentials", style={
                        "color": "#4a9eff", "fontSize": "14px", "marginBottom": "40px",
                        "textAlign": "center",
                    }),

                    # Role selector
                    html.Div(style={"width": "100%", "maxWidth": "460px", "marginBottom": "28px"},
                        children=[
                            html.Label("ROLE", style={
                                "color": "rgba(180,210,255,0.7)", "fontSize": "11px",
                                "fontWeight": "600", "letterSpacing": "1.5px", "marginBottom": "12px",
                                "display": "block",
                            }),
                            html.Div(
                                id="role-selector",
                                style={"display": "flex", "gap": "16px"},
                                children=[
                                    html.Div(
                                        id="role-user",
                                        n_clicks=0,
                                        style={
                                            "flex": "1", "padding": "22px 16px",
                                            "border": "2px solid #4a9eff",
                                            "borderRadius": "10px", "cursor": "pointer",
                                            "display": "flex", "flexDirection": "column",
                                            "alignItems": "center",
                                            "background": "rgba(74,158,255,0.12)",
                                            "transition": "all 0.2s",
                                        },
                                        children=[
                                            USER_ICON,
                                            html.Span("USER", style={
                                                "color": "white", "fontSize": "13px",
                                                "fontWeight": "600", "letterSpacing": "1.5px",
                                            })
                                        ]
                                    ),
                                    html.Div(
                                        id="role-admin",
                                        n_clicks=0,
                                        style={
                                            "flex": "1", "padding": "22px 16px",
                                            "border": "2px solid rgba(74,158,255,0.2)",
                                            "borderRadius": "10px", "cursor": "pointer",
                                            "display": "flex", "flexDirection": "column",
                                            "alignItems": "center",
                                            "background": "rgba(74,158,255,0.04)",
                                            "transition": "all 0.2s",
                                        },
                                        children=[
                                            ADMIN_ICON,
                                            html.Span("ADMIN", style={
                                                "color": "rgba(255,255,255,0.45)", "fontSize": "13px",
                                                "fontWeight": "600", "letterSpacing": "1.5px",
                                            })
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),

                    # Username field
                    html.Div(style={"width": "100%", "maxWidth": "460px", "marginBottom": "20px"},
                        children=[
                            html.Label("USERNAME", style={
                                "color": "rgba(180,210,255,0.7)", "fontSize": "11px",
                                "fontWeight": "600", "letterSpacing": "1.5px", "marginBottom": "10px",
                                "display": "block",
                            }),
                            html.Div(
                                style={
                                    "display": "flex", "alignItems": "center", "gap": "12px",
                                    "background": "rgba(10,25,55,0.8)",
                                    "border": "1.5px solid rgba(74,158,255,0.25)",
                                    "borderRadius": "8px", "padding": "8px 16px",
                                },
                                children=[
                                    PERSON_ICON,
                                    dcc.Input(
                                        id="username-input",
                                        type="text",
                                        placeholder="operator_1",
                                        value="operator_1",
                                        style={
                                            "flex": "1", "background": "transparent",
                                            "border": "none", "outline": "none",
                                            "color": "rgba(200,220,255,0.8)", "fontSize": "15px",
                                            "fontFamily": "inherit",
                                        }
                                    )
                                ]
                            ),
                        ]
                    ),

                    # Password field
                    html.Div(style={"width": "100%", "maxWidth": "460px", "marginBottom": "32px"},
                        children=[
                            html.Label("PASSWORD", style={
                                "color": "rgba(180,210,255,0.7)", "fontSize": "11px",
                                "fontWeight": "600", "letterSpacing": "1.5px", "marginBottom": "10px",
                                "display": "block",
                            }),
                            html.Div(
                                style={
                                    "display": "flex", "alignItems": "center", "gap": "12px",
                                    "background": "rgba(10,25,55,0.8)",
                                    "border": "1.5px solid rgba(74,158,255,0.35)",
                                    "borderRadius": "8px", "padding": "8px 16px",
                                    "boxShadow": "0 0 0 1px rgba(74,158,255,0.15)",
                                },
                                children=[
                                    LOCK_ICON,
                                    dcc.Input(
                                        id="password-input",
                                        type="password",
                                        placeholder="••••••••••••",
                                        value="password123",
                                        style={
                                            "flex": "1", "background": "transparent",
                                            "border": "none", "outline": "none",
                                            "color": "rgba(200,220,255,0.8)", "fontSize": "18px",
                                            "fontFamily": "inherit",
                                            "letterSpacing": "4px",
                                        }
                                    )
                                ]
                            ),
                        ]
                    ),

                    # Sign In button
                    html.Button(
                        "Sign In",
                        id="signin-btn",
                        n_clicks=0,
                        style={
                            "width": "100%", "maxWidth": "460px", "padding": "18px",
                            "background": "linear-gradient(90deg, #1a6fd4 0%, #2a85f0 100%)",
                            "border": "none", "borderRadius": "8px", "color": "white",
                            "fontSize": "16px", "fontWeight": "700", "letterSpacing": "0.5px",
                            "cursor": "pointer", "marginBottom": "28px",
                            "boxShadow": "0 4px 20px rgba(42,133,240,0.35)",
                            "fontFamily": "inherit",
                            "transition": "all 0.2s",
                        }
                    ),

                    # Status message
                    html.Div(id="login-status", style={"minHeight": "24px", "marginBottom": "12px"}),

                    # Footer
                    html.Div(
                        style={"width": "100%", "maxWidth": "460px", "textAlign": "center"},
                        children=[
                            html.Div(style={
                                "display": "flex", "alignItems": "center", "gap": "12px",
                                "marginBottom": "8px",
                            }, children=[
                                html.Div(style={"flex": "1", "height": "1px",
                                               "background": "rgba(74,158,255,0.2)"}),
                                html.Span("SECURED ACCESS", style={
                                    "color": "rgba(180,210,255,0.5)", "fontSize": "10px",
                                    "letterSpacing": "2px", "fontWeight": "600",
                                }),
                                html.Div(style={"flex": "1", "height": "1px",
                                               "background": "rgba(74,158,255,0.2)"}),
                            ]),
                            html.P("Authorized Personnel Only · All Sessions Are Logged", style={
                                "color": "rgba(180,210,255,0.4)", "fontSize": "11px", "margin": "0",
                            }),
                        ]
                    ),
                ]
            ),
        ]
    )

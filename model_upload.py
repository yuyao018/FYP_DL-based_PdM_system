import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import base64
import os
from datetime import datetime

# Shared model storage directory
SHARED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "data", "shared_models")

MODEL_TYPES = ["FD001", "FD002", "FD003", "FD004"]

# ─────────────────────────────────────────────
#  SVG ICON HELPERS
# ─────────────────────────────────────────────

def _svg_img(svg_str, size="22px"):
    b64 = base64.b64encode(svg_str.strip().encode("utf-8")).decode("utf-8")
    return html.Img(src=f"data:image/svg+xml;base64,{b64}",
                    style={"width": size, "height": size, "flexShrink": "0"})

def icon_dashboard():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
      <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
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
        <circle cx="50" cy="50" r="48" fill="none" stroke="#a8d4ff" stroke-width="1.5"/>
        <circle cx="50" cy="50" r="18" fill="none" stroke="#a8d4ff" stroke-width="2"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#a8d4ff" stroke-width="1.8" transform="rotate(0 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#a8d4ff" stroke-width="1.8" transform="rotate(90 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#a8d4ff" stroke-width="1.8" transform="rotate(180 50 50)"/>
        <rect x="47" y="4" width="6" height="12" rx="2" fill="none" stroke="#a8d4ff" stroke-width="1.8" transform="rotate(270 50 50)"/>
        <circle cx="50" cy="50" r="4" fill="#a8d4ff"/>
    </svg>''', size="22px")

def icon_upload():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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

def icon_sidebar():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#a8d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <line x1="9" y1="3" x2="9" y2="21"/>
    </svg>''', size="26px")

def icon_logout():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#ff4d4d" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>''', size="22px")

def icon_chip():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="7" y="7" width="10" height="10" rx="1"/>
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <line x1="9" y1="1" x2="9" y2="3"/><line x1="15" y1="1" x2="15" y2="3"/>
      <line x1="9" y1="21" x2="9" y2="23"/><line x1="15" y1="21" x2="15" y2="23"/>
      <line x1="1" y1="9" x2="3" y2="9"/><line x1="1" y1="15" x2="3" y2="15"/>
      <line x1="21" y1="9" x2="23" y2="9"/><line x1="21" y1="15" x2="23" y2="15"/>
    </svg>''')

def icon_upload_cloud():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="white" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 16V8M12 8l-3.5 3.5M12 8l3.5 3.5"/>
      <path d="M5 17a4 4 0 0 1 0-8 5 5 0 0 1 9.6-1.5A4.5 4.5 0 0 1 19 17"/>
    </svg>''', size="28px")

def icon_model_file():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="#4a9eff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="7" y="7" width="10" height="10" rx="1"/>
      <rect x="3" y="3" width="18" height="18" rx="2"/>
    </svg>''', size="18px")

def icon_close():
    return _svg_img('''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none"
         stroke="rgba(168,212,255,0.6)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="5" y1="5" x2="19" y2="19"/><line x1="19" y1="5" x2="5" y2="19"/>
    </svg>''', size="16px")


# ─────────────────────────────────────────────
#  SIDEBAR  (Admin Panel variant — shared pattern)
# ─────────────────────────────────────────────

def build_admin_sidebar(active_page="model"):
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
            "width": "210px", "flexShrink": "0", "height": "100%",
            "background": "#0d1e3a", "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex", "flexDirection": "column",
            "overflow": "hidden", "transition": "width 0.3s ease",
        },
        children=[
            html.A(href="/dashboard", style={"textDecoration": "none"}, children=[
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
                nav_link(icon_upload,    "Model Upload",     "model",     "/model-upload"),
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


# ─────────────────────────────────────────────
#  TOPBAR
# ─────────────────────────────────────────────

def build_topbar():
    return html.Div(
        style={
            "background": "linear-gradient(90deg, #0d2045 0%, #071530 100%)",
            "borderBottom": "1px solid rgba(74,158,255,0.18)",
            "padding": "0 28px", "height": "60px", "minHeight": "60px",
            "flexShrink": "0", "display": "flex", "alignItems": "center",
            "justifyContent": "space-between", "zIndex": "200",
        },
        children=[
            html.H1("ENGINE PROGNOSTIC MONITORING SYSTEM", style={
                "margin": "0", "fontSize": "18px", "fontWeight": "700",
                "color": "white", "letterSpacing": "1.2px",
            }),
            html.Div(id="sidebar-toggle", n_clicks=0, style={"cursor": "pointer"},
                     children=[icon_sidebar()]),
        ]
    )


# ─────────────────────────────────────────────
#  PANEL WRAPPER
# ─────────────────────────────────────────────

def panel(title, icon_fn, children):
    return html.Div(
        style={
            "background": "#101e36", "border": "1px solid rgba(74,158,255,0.18)",
            "borderRadius": "14px", "padding": "20px 22px", "marginBottom": "16px",
        },
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "16px"},
                children=[icon_fn(), html.Span(title.upper(), style={
                    "color": "white", "fontSize": "13px", "fontWeight": "700", "letterSpacing": "0.5px",
                })]
            ),
            *children,
        ]
    )


# ─────────────────────────────────────────────
#  CURRENTLY ACTIVE MODEL CARD
# ─────────────────────────────────────────────

def info_box(label, value):
    return html.Div(
        style={
            "flex": "1", "background": "rgba(10,20,45,0.5)",
            "border": "1px solid rgba(74,158,255,0.15)",
            "borderRadius": "8px", "padding": "12px 16px",
        },
        children=[
            html.Div(label.upper(), style={"color": "#4a9eff", "fontSize": "10px",
                                            "fontWeight": "700", "letterSpacing": "0.8px",
                                            "marginBottom": "6px"}),
            html.Div(value, style={"color": "white", "fontSize": "14px", "fontWeight": "700"}),
        ]
    )


def build_active_model_panel(active_model=None):
    if active_model is None:
        active_model = {"filename": "No active model", "uploaded": "—", "uploaded_by": "—"}

    return panel("Currently Active Model", icon_chip, [
        html.Div(style={"display": "flex", "gap": "14px"}, children=[
            info_box("Filename", active_model["filename"]),
            info_box("Uploaded", active_model["uploaded"]),
            info_box("Uploaded By", active_model["uploaded_by"]),
        ])
    ])


# ─────────────────────────────────────────────
#  UPLOAD DROPZONE
# ─────────────────────────────────────────────

def build_upload_panel():
    return panel("Upload New Model", icon_upload, [
        dcc.Upload(
            id="model-upload-dropzone",
            children=html.Div(
                style={"display": "flex", "flexDirection": "column", "alignItems": "center", "gap": "10px"},
                children=[
                    html.Div(
                        style={
                            "width": "52px", "height": "52px", "borderRadius": "50%",
                            "background": "rgba(74,158,255,0.18)",
                            "border": "1px solid rgba(74,158,255,0.4)",
                            "display": "flex", "alignItems": "center", "justifyContent": "center",
                        },
                        children=[icon_upload_cloud()]
                    ),
                    html.Div("Drag & drop your .h5 file here",
                             style={"color": "white", "fontSize": "14px", "fontWeight": "600"}),
                    html.Div("Only Keras .h5 model files accepted",
                             style={"color": "rgba(168,212,255,0.5)", "fontSize": "12px"}),
                    html.Button("Browse File", id="browse-file-btn", n_clicks=0, style={
                        "background": "rgba(74,158,255,0.15)", "border": "1px solid rgba(74,158,255,0.4)",
                        "color": "#a8d4ff", "borderRadius": "8px", "padding": "8px 20px",
                        "fontSize": "13px", "fontWeight": "700", "cursor": "pointer", "marginTop": "4px",
                    }),
                ]
            ),
            style={
                "width": "100%", "minHeight": "150px",
                "border": "2px dashed rgba(74,158,255,0.3)",
                "borderRadius": "10px",
                "background": "rgba(10,20,45,0.4)",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "cursor": "pointer", "marginBottom": "16px", "padding": "24px 0px",
            },
            accept=".h5",
            multiple=False,
        ),

        html.Div(id="staged-file-container", children=[]),

        html.Div(style={"marginTop": "16px"}, children=[
            html.Label("VERSION NOTES (OPTIONAL)", style={
                "color": "#4a9eff", "fontSize": "11px", "fontWeight": "700",
                "letterSpacing": "0.8px", "marginBottom": "8px", "display": "block",
            }),
            dcc.Textarea(
                id="version-notes-input",
                placeholder="e.g. Retrained on FD001+FD002, improved RMSE from 14.3 → 12.8...",
                style={
                    "width": "100%", "minHeight": "70px",
                    "background": "rgba(10,20,45,0.6)",
                    "border": "1.5px solid rgba(74,158,255,0.25)",
                    "borderRadius": "8px", "padding": "10px 12px",
                    "color": "white", "fontSize": "13px", "fontFamily": "inherit",
                    "resize": "vertical",
                }
            ),
        ]),

        html.Div(
            style={"display": "flex", "justifyContent": "flex-end", "gap": "12px", "marginTop": "16px"},
            children=[
                html.Button("Cancel", id="cancel-upload-btn", n_clicks=0, style={
                    "background": "rgba(74,158,255,0.08)", "border": "1px solid rgba(74,158,255,0.25)",
                    "color": "rgba(168,212,255,0.5)", "borderRadius": "8px",
                    "padding": "10px 24px", "fontSize": "13px", "fontWeight": "600",
                    "cursor": "not-allowed",
                }),
                html.Button("Deploy Model", id="deploy-model-btn", n_clicks=0, disabled=True, style={
                    "background": "rgba(74,158,255,0.3)", "border": "none", "borderRadius": "8px",
                    "color": "rgba(255,255,255,0.5)", "padding": "10px 24px",
                    "fontSize": "13px", "fontWeight": "700", "cursor": "not-allowed",
                }),
            ]
        ),

        dcc.Store(id="staged-file-data", data=None),
        html.Div(id="model-upload-status", style={"marginTop": "10px", "textAlign": "right"}),
    ])


# ─────────────────────────────────────────────
#  STAGED FILE PREVIEW CARD
# ─────────────────────────────────────────────

def staged_file_card(filename, size_mb):
    return html.Div(
        style={
            "display": "flex", "alignItems": "center", "justifyContent": "space-between",
            "background": "rgba(74,158,255,0.06)", "border": "1px solid rgba(74,158,255,0.2)",
            "borderRadius": "8px", "padding": "12px 16px",
        },
        children=[
            html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px"}, children=[
                icon_model_file(),
                html.Div(children=[
                    html.Div(filename, style={"color": "white", "fontSize": "13px", "fontWeight": "700"}),
                    html.Div(f"{size_mb} MB · Uploaded just now",
                             style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px"}),
                ])
            ]),
            html.Div(id="remove-staged-file-btn", n_clicks=0, style={"cursor": "pointer"},
                     children=[icon_close()])
        ]
    )


# ─────────────────────────────────────────────
#  VERSION HISTORY TABLE
# ─────────────────────────────────────────────

def status_label(status):
    cfg = {
        "active":   ("#00c875",),
        "archived": ("rgba(168,212,255,0.5)",),
    }
    color = cfg.get(status.lower(), cfg["archived"])[0]
    return html.Span(status.capitalize(), style={"color": color, "fontSize": "12px", "fontWeight": "600"})


def history_row(entry, is_last=False):
    show_restore = entry["status"].lower() != "active"
    return html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "1.4fr 1fr 1fr 0.8fr 0.8fr",
            "alignItems": "center",
            "padding": "12px 20px",
            "borderBottom": "none" if is_last else "1px solid rgba(74,158,255,0.08)",
        },
        children=[
            html.Span(entry["filename"], style={"color": "white", "fontSize": "13px", "fontWeight": "600"}),
            html.Span(entry["uploaded"], style={"color": "#a8d4ff", "fontSize": "12px"}),
            html.Span(entry["uploaded_by"], style={"color": "#a8d4ff", "fontSize": "12px"}),
            status_label(entry["status"]),
            html.Button("Restore", n_clicks=0, style={
                "background": "rgba(74,158,255,0.18)", "border": "1px solid rgba(74,158,255,0.4)",
                "color": "#a8d4ff", "borderRadius": "6px", "padding": "5px 14px",
                "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
            }) if show_restore else html.Span("—", style={"color": "rgba(168,212,255,0.3)", "fontSize": "12px"}),
        ]
    )


def build_version_history(history=None):
    if history is None or len(history) == 0:
        history = []

    return html.Div(
        style={
            "background": "#101e36", "border": "1px solid rgba(74,158,255,0.18)",
            "borderRadius": "14px", "overflow": "hidden",
        },
        children=[
            html.Div("VERSION HISTORY", style={
                "color": "white", "fontSize": "13px", "fontWeight": "700",
                "letterSpacing": "0.5px", "padding": "16px 20px 12px",
            }),
            html.Div(
                style={
                    "display": "grid", "gridTemplateColumns": "1.4fr 1fr 1fr 0.8fr 0.8fr",
                    "padding": "10px 20px",
                    "background": "rgba(74,158,255,0.06)",
                    "borderTop": "1px solid rgba(74,158,255,0.12)",
                    "borderBottom": "1px solid rgba(74,158,255,0.12)",
                },
                children=[
                    html.Span("FILENAME",    style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("UPLOADED",    style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("UPLOADED BY", style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("STATUS",      style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                    html.Span("ACTION",      style={"color": "rgba(168,212,255,0.5)", "fontSize": "11px", "fontWeight": "700"}),
                ]
            ),
            html.Div(id="version-history-body", children=[
                history_row(h, is_last=(i == len(history) - 1)) for i, h in enumerate(history)
            ] if history else [
                html.Div("No version history available", style={
                    "color": "rgba(168,212,255,0.5)", "fontSize": "13px", 
                    "padding": "20px", "textAlign": "center"
                })
            ]),
        ]
    )


# ─────────────────────────────────────────────
#  MAIN PAGE BODY
# ─────────────────────────────────────────────

def build_model_type_selector(selected="FD001"):
    """Inline dropdown model type selector pushed to the far right of the header row."""
    return html.Div(
        style={"marginLeft": "auto", "display": "flex", "alignItems": "center", "gap": "8px"},
        children=[
            html.Span("MODEL TYPE", style={
                "color": "rgba(168,212,255,0.55)", "fontSize": "10px",
                "fontWeight": "700", "letterSpacing": "1px", "whiteSpace": "nowrap",
            }),
            dcc.Dropdown(
                id="model-type-dropdown",
                options=[{"label": mt, "value": mt} for mt in MODEL_TYPES],
                value=selected,
                clearable=False,
                className="model-type-dropdown",
                style={
                    "width": "120px",
                    "fontSize": "13px",
                    "fontWeight": "700",
                    # Dash injects these inline — override them here
                    "backgroundColor": "rgba(10,20,45,0.8)",
                    "color": "white",
                    "border": "1.5px solid rgba(74,158,255,0.4)",
                    "borderRadius": "8px",
                },
            ),
        ]
    )


def build_model_upload_body(active_model=None, history=None, selected_type="FD001"):
    return [
        html.Div(style={"marginBottom": "8px"}, children=[
            html.Div(
                style={
                    "display": "flex", "alignItems": "center",
                    "justifyContent": "space-between", "flexWrap": "nowrap",
                },
                children=[
                    html.H2("MODEL UPLOAD", style={"margin": "0", "color": "white",
                                                    "fontSize": "22px", "fontWeight": "800"}),
                    build_model_type_selector(selected=selected_type),
                ]
            ),
            html.Div("Replace the active .h5 model file used for RUL inference",
                     style={"color": "rgba(168,212,255,0.6)", "fontSize": "13px", "marginTop": "4px"}),
        ]),
        dcc.Store(id="selected-model-type", data=selected_type),
        html.Div(style={"height": "1px", "background": "rgba(74,158,255,0.15)", "margin": "16px 0 20px"}),

        html.Div(id="active-model-panel-container", children=[build_active_model_panel(active_model)]),
        build_upload_panel(),
        html.Div(id="version-history-container", children=[build_version_history(history)]),
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_model_upload_layout(supabase=None):
    active_model = None
    history = None
    default_type = "FD001"

    try:
        if supabase:
            # Use the shared helper so logic is consistent
            active_model, history = _fetch_history_for_type(supabase, default_type)
    except Exception as e:
        import traceback
        print(f"[ERROR] model upload fetch: {traceback.format_exc()}")

    return html.Div(
        style={
            "minHeight": "100vh", "display": "flex", "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628", "color": "white",
        },
        children=[
            dcc.Location(id="url-model-upload", refresh=False),
            html.Div(style={"position": "sticky", "top": "0", "zIndex": "200"},
                     children=[build_topbar()]),
            html.Div(
                style={"flex": "1", "display": "flex", "flexDirection": "row"},
                children=[
                    build_admin_sidebar(active_page="model"),
                    html.Div(
                        style={"flex": "1", "padding": "24px 28px", "minWidth": "0"},
                        children=build_model_upload_body(
                            active_model=active_model,
                            history=history,
                            selected_type=default_type,
                        ),
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def _fetch_history_for_type(supabase, model_type):
    """Helper: fetch version history + active model for a given model_type.

    Strategy:
    1. Fetch model_versions filtered by model_type, ordered newest first.
    2. Collect all distinct uploaded_by UUIDs and look them up in the users table.
    3. Build the history list and derive active_model from the 'active' row.
    """
    active_model = None
    history = []
    try:
        # ── Step 1: fetch model versions ──
        resp = supabase.table("model_versions") \
            .select("id, filename, uploaded_at, uploaded_by, status, model_type") \
            .eq("model_type", model_type) \
            .order("uploaded_at", desc=True) \
            .execute()

        rows = resp.data or []
        if not rows:
            return active_model, history

        # ── Step 2: batch-fetch usernames for all unique UUIDs ──
        uuids = list({r["uploaded_by"] for r in rows if r.get("uploaded_by")})
        username_map = {}
        if uuids:
            u_resp = supabase.table("users") \
                .select("id, username") \
                .in_("id", uuids) \
                .execute()
            for u in (u_resp.data or []):
                username_map[u["id"]] = u.get("username", "—")

        # ── Step 3: build history list ──
        for m in rows:
            uploaded_at = m.get("uploaded_at")
            if uploaded_at:
                try:
                    uploaded_at = datetime.fromisoformat(
                        uploaded_at.replace("Z", "+00:00")
                    ).strftime("%Y/%m/%d %H:%M")
                except Exception:
                    uploaded_at = str(uploaded_at)[:16]

            uploaded_by_username = username_map.get(m.get("uploaded_by"), "—")

            history.append({
                "filename":    m.get("filename", "—"),
                "uploaded":    uploaded_at or "—",
                "uploaded_by": uploaded_by_username,
                "status":      m.get("status", "archived"),
                "model_type":  m.get("model_type", model_type),
            })

        active_entry = next((h for h in history if h["status"].lower() == "active"), None)
        if active_entry:
            active_model = {
                "filename":    active_entry["filename"],
                "uploaded":    active_entry["uploaded"],
                "uploaded_by": active_entry["uploaded_by"],
            }

    except Exception:
        import traceback
        print(f"[ERROR] _fetch_history_for_type: {traceback.format_exc()}")

    return active_model, history


def register_model_upload_callbacks(app, supabase=None):

    # ── Model type dropdown: refresh active model panel + version history ──
    @app.callback(
        Output("selected-model-type", "data"),
        Output("active-model-panel-container", "children"),
        Output("version-history-container", "children"),
        Input("model-type-dropdown", "value"),
        prevent_initial_call=True,
    )
    def switch_model_type(selected):
        if not selected:
            raise dash.exceptions.PreventUpdate

        if supabase:
            active_model, history = _fetch_history_for_type(supabase, selected)
        else:
            active_model, history = None, []

        return selected, [build_active_model_panel(active_model)], [build_version_history(history)]

    # ── Handle file drop / browse ──
    @app.callback(
        Output("staged-file-container", "children"),
        Output("staged-file-data", "data"),
        Output("deploy-model-btn", "disabled"),
        Output("deploy-model-btn", "style"),
        Output("cancel-upload-btn", "style"),
        Input("model-upload-dropzone", "contents"),
        State("model-upload-dropzone", "filename"),
        prevent_initial_call=True,
    )
    def stage_file(contents, filename):
        if contents is None:
            raise dash.exceptions.PreventUpdate

        if not filename.lower().endswith(".h5"):
            return (
                [html.Div("Only .h5 files are accepted.",
                         style={"color": "#ff6b6b", "fontSize": "12px"})],
                None, True,
                {"background": "rgba(74,158,255,0.3)", "border": "none", "borderRadius": "8px",
                 "color": "rgba(255,255,255,0.5)", "padding": "10px 24px",
                 "fontSize": "13px", "fontWeight": "700", "cursor": "not-allowed"},
                {"background": "rgba(74,158,255,0.08)", "border": "1px solid rgba(74,158,255,0.25)",
                 "color": "rgba(168,212,255,0.5)", "borderRadius": "8px",
                 "padding": "10px 24px", "fontSize": "13px", "fontWeight": "600", "cursor": "not-allowed"},
            )

        header, b64data = contents.split(",", 1)
        size_mb = round(len(base64.b64decode(b64data)) / (1024 * 1024), 1)

        active_style = {
            "background": "linear-gradient(90deg, #1a6fd4 0%, #2a85f0 100%)",
            "border": "none", "borderRadius": "8px", "color": "white",
            "padding": "10px 24px", "fontSize": "13px", "fontWeight": "700",
            "cursor": "pointer", "boxShadow": "0 2px 10px rgba(42,133,240,0.3)",
        }
        cancel_active_style = {
            "background": "rgba(74,158,255,0.08)", "border": "1px solid rgba(74,158,255,0.25)",
            "color": "rgba(168,212,255,0.8)", "borderRadius": "8px",
            "padding": "10px 24px", "fontSize": "13px", "fontWeight": "600", "cursor": "pointer",
        }

        return (
            [staged_file_card(filename, size_mb)],
            {"filename": filename, "size_mb": size_mb, "contents": contents},
            False,
            active_style,
            cancel_active_style,
        )

    # ── Cancel upload — clear staged file ──
    @app.callback(
        Output("staged-file-container", "children", allow_duplicate=True),
        Output("staged-file-data", "data", allow_duplicate=True),
        Output("model-upload-dropzone", "contents"),
        Output("version-notes-input", "value"),
        Input("cancel-upload-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def cancel_upload(n_clicks):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        return [], None, None, ""

    # ── Deploy model ──
    @app.callback(
        Output("model-upload-status", "children"),
        Output("version-history-body", "children"),
        Output("active-model-panel-container", "children", allow_duplicate=True),
        Input("deploy-model-btn", "n_clicks"),
        State("staged-file-data", "data"),
        State("version-notes-input", "value"),
        State("session-store", "data"),
        State("selected-model-type", "data"),
        prevent_initial_call=True,
    )
    def deploy_model(n_clicks, staged_file, notes, session_data, model_type):
        if not n_clicks or not staged_file:
            raise dash.exceptions.PreventUpdate

        if not supabase:
            return (
                html.Span("Supabase not connected.", style={"color": "#ff6b6b", "fontSize": "13px"}),
                dash.no_update,
                dash.no_update,
            )

        user_id = None
        if session_data:
            user_id = session_data.get("user_id")

        if not user_id:
            return (
                html.Span("User not authenticated.", style={"color": "#ff6b6b", "fontSize": "13px"}),
                dash.no_update,
                dash.no_update,
            )

        selected_type = model_type or "FD001"

        try:
            # ── Save .h5 file to data/shared_models/<model_type>/ ──
            type_dir = os.path.join(SHARED_MODELS_DIR, selected_type)
            os.makedirs(type_dir, exist_ok=True)
            _, b64data = staged_file["contents"].split(",", 1)
            file_bytes = base64.b64decode(b64data)

            # ── Mark previous active model for this type as archived ──
            supabase.table("model_versions") \
                .update({"status": "archived"}) \
                .eq("status", "active") \
                .eq("model_type", selected_type) \
                .execute()

            # ── Insert new model version as active ──
            insert_resp = supabase.table("model_versions").insert({
                "uploaded_by": user_id,
                "filename": staged_file["filename"],
                "version_notes": notes or None,
                "status": "active",
                "model_type": selected_type,
            }).execute()

            # Get the new version's UUID
            version_id = insert_resp.data[0]["id"] if insert_resp.data else None

            # Save file as <version_id>.h5 to avoid overwrites
            if version_id:
                save_filename = f"{version_id}.h5"
            else:
                save_filename = staged_file["filename"]
            save_path = os.path.join(type_dir, save_filename)
            with open(save_path, "wb") as f:
                f.write(file_bytes)

            # Update the DB row with the actual stored filename
            if version_id:
                supabase.table("model_versions") \
                    .update({"filename": save_filename}) \
                    .eq("id", version_id) \
                    .execute()

            # ── Re-fetch active model + history for this type ──
            active_model, history = _fetch_history_for_type(supabase, selected_type)
            rows = [
                history_row(h, is_last=(i == len(history) - 1))
                for i, h in enumerate(history)
            ] if history else [
                html.Div("No version history available", style={
                    "color": "rgba(168,212,255,0.5)", "fontSize": "13px",
                    "padding": "20px", "textAlign": "center"
                })
            ]

            # ── Auto-reload the model in running simulations ──
            try:
                from engine_simulation_manager import reload_model
                reload_model(selected_type, supabase=supabase)
                print(f"[MODEL] Auto-reloaded {selected_type} model for running simulations")
            except Exception as _reload_err:
                print(f"[MODEL][WARN] Failed to reload model: {_reload_err}")

            return (
                html.Span(
                    f"Model deployed successfully to {selected_type}!",
                    style={"color": "#4aff9e", "fontSize": "13px"}
                ),
                rows,
                [build_active_model_panel(active_model)],
            )

        except Exception as e:
            import traceback
            print(f"[ERROR] deploy model: {traceback.format_exc()}")
            return (
                html.Span(f"Failed to deploy: {str(e)}", style={"color": "#ff6b6b", "fontSize": "13px"}),
                dash.no_update,
                dash.no_update,
            )

    @app.callback(
        Output("sidebar", "style"),
        Output("sidebar-state", "data"),
        Input("sidebar-toggle", "n_clicks"),
        State("sidebar-state", "data"),
        prevent_initial_call=True,
    )
    def toggle_sidebar(n, is_open):
        is_open = not is_open
        base = {
            "flexShrink": "0", "height": "100%", "background": "#0d1e3a",
            "borderRight": "1px solid rgba(74,158,255,0.15)",
            "display": "flex", "flexDirection": "column",
            "overflow": "hidden", "transition": "width 0.3s ease",
        }
        return ({**base, "width": "210px"}, True) if is_open else ({**base, "width": "0px"}, False)


# ─────────────────────────────────────────────
#  STANDALONE RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True)
    app.layout = html.Div([
        dcc.Store(id="sidebar-state", data=True),
        create_model_upload_layout()
    ])
    register_model_upload_callbacks(app)
    app.run(debug=True)
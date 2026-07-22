import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import base64
import numpy as np
from assets.components import (build_sidebar, build_topbar)

# ─────────────────────────────────────────────
#  SENSOR DEFINITIONS
# ─────────────────────────────────────────────

SENSORS = {
    "TEMPERATURE": [
        {"id": "T2",      "label": "T2",      "unit": "°R",     "desc": "Fan inlet temperature",       "color": "#ff6b6b"},
        {"id": "T24",     "label": "T24",     "unit": "°R",     "desc": "LPC outlet temperature",      "color": "#f5a623"},
        {"id": "T30",     "label": "T30",     "unit": "°R",     "desc": "HPC outlet temperature",      "color": "#ff4d4d"},
        {"id": "T50",     "label": "T50",     "unit": "°R",     "desc": "LPT outlet temperature",      "color": "#ff8c69"},
    ],
    "PRESSURE": [
        {"id": "P2",      "label": "P2",      "unit": "psia",   "desc": "Fan inlet pressure",          "color": "#4a9eff"},
        {"id": "P15",     "label": "P15",     "unit": "psia",   "desc": "Bypass duct pressure",        "color": "#00c8ff"},
        {"id": "P30",     "label": "P30",     "unit": "psia",   "desc": "HPC outlet pressure",         "color": "#7b61ff"},
        {"id": "Ps30",    "label": "Ps30",    "unit": "psia",   "desc": "HPC static pressure",         "color": "#a0f0c0"},
    ],
    "SPEED / FLOW": [
        {"id": "Nf",      "label": "Nf",      "unit": "rpm",    "desc": "Physical fan speed",          "color": "#00c875"},
        {"id": "Nc",      "label": "Nc",      "unit": "rpm",    "desc": "Physical core speed",         "color": "#00e5a0"},
        {"id": "phi",     "label": "phi",     "unit": "pps/psi","desc": "Fuel flow / Ps30 ratio",      "color": "#ffd93d"},
        {"id": "NRf",     "label": "NRf",     "unit": "rpm",    "desc": "Corrected fan speed",         "color": "#c0d0ff"},
        {"id": "NRc",     "label": "NRc",     "unit": "rpm",    "desc": "Corrected core speed",        "color": "#90a8e0"},
        {"id": "BPR",     "label": "BPR",     "unit": "—",      "desc": "Bypass ratio",                "color": "#ff9f43"},
        {"id": "htBleed", "label": "htBleed", "unit": "—",      "desc": "Bleed enthalpy",              "color": "#e879f9"},
        {"id": "W31",     "label": "W31",     "unit": "lbm/s",  "desc": "HPT coolant bleed",           "color": "#34d399"},
        {"id": "W32",     "label": "W32",     "unit": "lbm/s",  "desc": "LPT coolant bleed",           "color": "#6ee7b7"},
    ],
}

# Default selected sensors (matching screenshot)
DEFAULT_SELECTED = ["T30", "P30", "Nf", "phi"]

# Flat lookup by sensor display ID
ALL_SENSORS = {s["id"]: s for group in SENSORS.values() for s in group}

# ─────────────────────────────────────────────
#  SENSOR → JSON KEY MAPPING
# ─────────────────────────────────────────────

# Maps each display sensor ID to its key in the JSON row's "sensors" dict
# Reference: CMAPSS S-number → symbol table
SENSOR_JSON_KEY = {
    "T2":      "s1",   # S1  → T2   — Fan inlet temperature
    "T24":     "s2",   # S2  → T24  — LPC outlet temperature
    "T30":     "s3",   # S3  → T30  — HPC outlet temperature
    "T50":     "s4",   # S4  → T50  — LPT outlet temperature
    "P2":      "s5",   # S5  → P2   — Fan inlet pressure
    "P15":     "s6",   # S6  → P15  — Bypass duct pressure
    "P30":     "s7",   # S7  → P30  — HPC outlet pressure
    "Nf":      "s8",   # S8  → Nf   — Physical fan speed
    "Nc":      "s9",   # S9  → Nc   — Physical core speed
    "Ps30":    "s11",  # S11 → Ps30 — HPC static pressure
    "phi":     "s12",  # S12 → phi  — Fuel flow / Ps30
    "NRf":     "s13",  # S13 → NRf  — Corrected fan speed
    "NRc":     "s14",  # S14 → NRc  — Corrected core speed
    "BPR":     "s15",  # S15 → BPR  — Bypass ratio
    "htBleed": "s17",  # S17 → htBleed — Bleed enthalpy
    "W31":     "s20",  # S20 → W31  — HPT coolant bleed
    "W32":     "s21",  # S21 → W32  — LPT coolant bleed
}

# ─────────────────────────────────────────────
#  SENSOR CHART
# ─────────────────────────────────────────────

def build_sensor_chart(selected_ids, sensor_history=None, normalize=True, cluster_info=None):
    """
    Build multi-line sensor chart from real sensor history rows.
    sensor_history: list of row dicts from engine_simulation_manager.get_sensor_history()
    cluster_info: (centroids, cluster_means, cluster_stds) for FD002/FD004 per-cluster normalization.
    Falls back to an empty placeholder if no data yet.
    """
    fig = go.Figure()

    if not sensor_history:
        fig.add_annotation(
            text="Sensor data will appear as simulation runs…",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(color="rgba(168,212,255,0.5)", size=13),
        )
        _apply_chart_layout(fig, normalize)
        return fig

    cycles = [r.get("cycle", i + 1) for i, r in enumerate(sensor_history)]

    # ── Per-cluster normalization for FD002/FD004 ──
    _use_cluster = (cluster_info is not None and cluster_info[0] is not None)
    os_keys = ["operational_setting_1", "operational_setting_2", "operational_setting_3"]
    sensor_keys_ordered = ["s2", "s3", "s4", "s7", "s8", "s9", "s11",
                           "s12", "s13", "s14", "s15", "s17", "s20", "s21"]
    cluster_normalized = {}  # json_key → list of normalized values

    if _use_cluster and normalize:
        centroids, cl_means, cl_stds = cluster_info
        for row in sensor_history:
            sensors_dict = row.get("sensors", {})
            # Get OS for cluster assignment
            os_vals = []
            for ok in os_keys:
                v = row.get(ok, sensors_dict.get(ok, 0.0))
                os_vals.append(float(v) if v is not None else 0.0)
            os_arr = np.array(os_vals, dtype=np.float32)
            dists = np.linalg.norm(centroids - os_arr, axis=1)
            cid = int(np.argmin(dists))
            c_mean = cl_means[cid]
            c_std = cl_stds[cid].copy()
            c_std[c_std == 0] = 1.0
            for idx, sk in enumerate(sensor_keys_ordered):
                raw_val = sensors_dict.get(sk)
                if raw_val is not None:
                    norm_val = (float(raw_val) - c_mean[idx]) / c_std[idx]
                else:
                    norm_val = None
                cluster_normalized.setdefault(sk, []).append(norm_val)

    for sid in selected_ids:
        if sid not in ALL_SENSORS:
            continue
        json_key = SENSOR_JSON_KEY.get(sid)
        if not json_key:
            continue

        s = ALL_SENSORS[sid]

        # Use cluster-normalized values if available
        if _use_cluster and normalize and json_key in cluster_normalized:
            y = cluster_normalized[json_key]
            # Apply rolling mean smoothing (window=10)
            arr = np.array([v if v is not None else np.nan for v in y], dtype=float)
            smoothed = np.convolve(arr, np.ones(10) / 10, mode='same')
            # Fix edges
            for i in range(min(5, len(smoothed))):
                smoothed[i] = np.nanmean(arr[:i + 1])
            for i in range(max(0, len(smoothed) - 5), len(smoothed)):
                smoothed[i] = np.nanmean(arr[i:])
            y = smoothed.tolist()
        else:
            values = []
            for row in sensor_history:
                sensors_dict = row.get("sensors", {})
                v = sensors_dict.get(json_key)
                if v is None:
                    v = row.get(json_key)
                values.append(float(v) if v is not None else None)

            if all(v is None for v in values):
                continue

            y = values
            if normalize:
                vals = [v for v in values if v is not None]
                if vals:
                    mn, mx = min(vals), max(vals)
                    rng = mx - mn if mx != mn else 1.0
                    y = [(v - mn) / rng if v is not None else None for v in values]

        fig.add_trace(go.Scatter(
            x=cycles, y=y,
            mode="lines",
            name=s["label"],
            line=dict(color=s["color"], width=2),
            connectgaps=True,
            hovertemplate=(
                f"<b>{s['label']}</b><br>Cycle: %{{x}}<br>"
                f"Value: %{{y:.3f}}<extra></extra>"
            ),
        ))

    _apply_chart_layout(fig, normalize, x_max=max(cycles) if cycles else 1, x_min=min(cycles) if cycles else 0)
    return fig


def _apply_chart_layout(fig, normalize, x_max=None, x_min=None):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,20,45,0.6)",
        margin=dict(l=10, r=20, t=30, b=40),
        height=420,
        legend=dict(
            orientation="h", x=0, y=-0.18,
            font=dict(color="#a8d4ff", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            title=dict(text="Operational Cycles", font=dict(color="#a8d4ff", size=11)),
            showgrid=True, gridcolor="rgba(74,158,255,0.08)",
            color="#a8d4ff", tickfont=dict(size=10), zeroline=False,
            range=[x_min if x_min is not None else 0, x_max] if x_max else None,
            showticklabels=False,
        ),
        yaxis=dict(
            title=dict(
                text="Normalised Value" if normalize else "Raw Value",
                font=dict(color="#a8d4ff", size=11),
            ),
            showgrid=True, gridcolor="rgba(74,158,255,0.08)",
            color="#a8d4ff", tickfont=dict(size=10), zeroline=False,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0d1e3a", font_color="white",
            bordercolor="rgba(74,158,255,0.4)",
        ),
    )

# ─────────────────────────────────────────────
#  SENSOR CHECKLIST
# ─────────────────────────────────────────────

def build_sensor_checklist():
    children = []
    for group_name, sensors in SENSORS.items():
        children.append(
            html.Div(group_name, style={
                "color": "rgba(168,212,255,0.45)", "fontSize": "10px",
                "fontWeight": "700", "letterSpacing": "1px",
                "padding": "8px 4px 4px", "marginTop": "4px",
            })
        )
        for s in sensors:
            children.append(
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "8px",
                           "padding": "5px 4px", "borderRadius": "6px", "marginBottom": "2px"},
                    children=[
                        dcc.Checklist(
                            id={"type": "sensor-check", "index": s["id"]},
                            options=[{"label": "", "value": s["id"]}],
                            value=[s["id"]] if s["id"] in DEFAULT_SELECTED else [],
                            style={"display": "inline"},
                            inputStyle={
                                "width": "14px", "height": "14px",
                                "accentColor": "#4a9eff", "cursor": "pointer",
                            },
                        ),
                        html.Div(style={
                            "width": "10px", "height": "10px", "borderRadius": "50%",
                            "background": s["color"], "flexShrink": "0",
                        }),
                        html.Span(s["label"], style={"color": "white", "fontSize": "13px",
                                                      "fontWeight": "500", "minWidth": "36px"}),
                        html.Span(s["unit"], style={"color": "rgba(168,212,255,0.45)", "fontSize": "11px"}),
                    ]
                )
            )
    return children


# ─────────────────────────────────────────────
#  RAW / NORMALIZE TOGGLE
# ─────────────────────────────────────────────

def normalize_toggle():
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "10px"},
        children=[
            html.Span("Raw", style={"color": "#a8d4ff", "fontSize": "13px", "fontWeight": "500"}),
            # Toggle switch
            html.Div(
                id="normalize-toggle",
                n_clicks=1,   # start as Normalize (active)
                style={
                    "width": "44px", "height": "24px", "borderRadius": "12px",
                    "background": "#4a9eff", "position": "relative",
                    "cursor": "pointer", "transition": "background 0.2s",
                    "border": "1px solid rgba(74,158,255,0.6)",
                },
                children=[
                    html.Div(style={
                        "width": "18px", "height": "18px", "borderRadius": "50%",
                        "background": "white", "position": "absolute",
                        "top": "2px", "right": "3px",
                        "transition": "left 0.2s",
                        "boxShadow": "0 1px 4px rgba(0,0,0,0.3)",
                    })
                ]
            ),
            html.Span("Normalize", style={"color": "white", "fontSize": "13px", "fontWeight": "600"}),
        ]
    )


# ─────────────────────────────────────────────
#  MAIN PAGE BODY
# ─────────────────────────────────────────────

def build_sensor_trends_body(engine_id="01", status="healthy"):

    status_cfg = {
        "healthy":  ("rgba(0,200,100,0.18)",  "#00c875", "#00c875"),
        "warning":  ("rgba(255,217,61,0.18)", "#ffd93d", "#ffd93d"),
        "critical": ("rgba(255,77,77,0.18)",  "#ff4d4d", "#ff4d4d"),
    }
    sc = status_cfg.get(status, status_cfg["healthy"])

    return [
        dcc.Store(id="normalize-state", data=True),

        # ── Engine header ──
        html.Div(
            style={"display": "flex", "alignItems": "center",
                   "justifyContent": "space-between", "marginBottom": "20px"},
            children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "14px"}, children=[
                    html.H2(f"ENGINE-{engine_id}",
                            style={"margin": "0", "color": "white",
                                   "fontSize": "22px", "fontWeight": "800"}),
                    html.Span(status.upper(), style={
                        "background": sc[0], "color": sc[1], "border": f"1px solid {sc[2]}",
                        "borderRadius": "20px", "padding": "3px 12px",
                        "fontSize": "11px", "fontWeight": "700",
                    }),
                ]),
                # Raw / Normalize toggle
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "10px"}, children=[
                    html.Span("Raw", id="raw-label",
                            style={"color": "#a8d4ff", "fontSize": "13px", "fontWeight": "500"}),
                    html.Div(
                        id="normalize-toggle",
                        n_clicks=1,
                        style={
                            "width": "44px", "height": "24px", "borderRadius": "12px",
                            "background": "#4a9eff", "position": "relative",
                            "cursor": "pointer", "flexShrink": "0",
                            "border": "1px solid rgba(74,158,255,0.6)",
                        },
                        children=[
                            html.Div(id="toggle-knob", style={
                                "width": "18px", "height": "18px", "borderRadius": "50%",
                                "background": "white", "position": "absolute",
                                "top": "2px", "right": "3px",
                                "transition": "right 0.2s",
                                "boxShadow": "0 1px 4px rgba(0,0,0,0.3)",
                            })
                        ]
                    ),
                    html.Span("Normalize", id="norm-label",
                            style={"color": "white", "fontSize": "13px", "fontWeight": "700"}),
                ]),
            ]
        ),

        # ── Two-column layout ──
        html.Div(
            style={"display": "flex", "gap": "0", "flex": "1", "minHeight": "500px"},
            children=[

                # Left: sensor panel
                html.Div(
                    style={
                        "width": "210px", "flexShrink": "0",
                        "background": "#0d1e3a",
                        "border": "1px solid rgba(74,158,255,0.15)",
                        "borderRadius": "14px 0 0 14px",
                        "padding": "14px 12px",
                        "overflowY": "auto",
                    },
                    children=[
                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between",
                                   "alignItems": "center", "marginBottom": "10px", "padding": "0 4px"},
                            children=[
                                html.Span("SENSORS", style={"color": "rgba(168,212,255,0.5)",
                                                              "fontSize": "10px", "fontWeight": "700",
                                                              "letterSpacing": "1.5px"}),
                                html.Span("Select all", id="select-all-btn", n_clicks=0,
                                          style={"color": "#4a9eff", "fontSize": "11px",
                                                 "cursor": "pointer", "fontWeight": "600"}),
                            ]
                        ),
                        *build_sensor_checklist(),
                    ]
                ),

                # Right: chart
                html.Div(
                    style={
                        "flex": "1", "minWidth": "0",
                        "background": "#101e36",
                        "border": "1px solid rgba(74,158,255,0.15)",
                        "borderLeft": "none",
                        "borderRadius": "0 14px 14px 0",
                        "padding": "16px 16px 8px",
                        "display": "flex", "flexDirection": "column",
                    },
                    children=[
                        dcc.Graph(
                            id="sensor-chart",
                            figure=build_sensor_chart(DEFAULT_SELECTED, sensor_history=None, normalize=True),
                            config={"displayModeBar": False},
                            style={"flex": "1"},
                        ),
                        html.Div(id="chart-legend",
                                 style={"display": "flex", "flexWrap": "wrap", "gap": "16px",
                                        "padding": "8px 4px 0",
                                        "borderTop": "1px solid rgba(74,158,255,0.1)"},
                                 children=[
                                     html.Div(
                                         style={"display": "flex", "alignItems": "center", "gap": "6px"},
                                         children=[
                                             html.Div(style={"width": "24px", "height": "2px",
                                                             "background": ALL_SENSORS[sid]["color"]}),
                                             html.Span(
                                                 f"{ALL_SENSORS[sid]['label']} — {ALL_SENSORS[sid]['desc']}",
                                                 style={"color": "#a8d4ff", "fontSize": "11px"}
                                             )
                                         ]
                                     )
                                     for sid in DEFAULT_SELECTED
                                 ]),
                    ]
                ),
            ]
        ),
    ]

# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_sensor_trends_layout(supabase=None, engine_db_id=None):
    engine_id = "01"
    status    = "healthy"

    try:
        if supabase and engine_db_id is not None:
            eng_resp = supabase.table("engines") \
                .select("engine_id, condition_status") \
                .eq("id", engine_db_id) \
                .single().execute()
            engine   = eng_resp.data or {}
            engine_id = str(engine.get("engine_id", "01")).zfill(2)
            status    = (engine.get("condition_status") or "healthy").lower().strip()
            if status not in ("healthy", "warning", "critical"):
                status = "healthy"
    except Exception as e:
        import traceback
        print(f"[ERROR] sensor trends fetch: {traceback.format_exc()}")

    return html.Div(
        style={
            "height": "100vh", "display": "flex", "flexDirection": "column",
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628", "color": "white", "overflow": "hidden",
        },
        children=[
            dcc.Location(id="url-sensor", refresh=False),
            dcc.Store(id="sensor-engine-id-store", data=engine_db_id),
            dcc.Interval(id="sensor-poll-interval", interval=3_000, n_intervals=0),

            build_topbar(),

            # ── Sidebar + content ──
            html.Div(
                style={"flex": "1", "display": "flex", "flexDirection": "row",
                       "overflow": "hidden", "minHeight": "0"},
                children=[
                    build_sidebar(active_page="sensor", engine_db_id=engine_db_id),
                    html.Div(
                        style={"flex": "1", "overflowY": "auto", "padding": "24px 28px",
                               "minWidth": "0", "display": "flex", "flexDirection": "column"},
                        children=build_sensor_trends_body(engine_id=engine_id, status=status),
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS  (register on the app object)
# ─────────────────────────────────────────────

def register_sensor_callbacks(app):
    all_ids = list(ALL_SENSORS.keys())

    # ── Toggle visual state (knob position + label colours) ──
    @app.callback(
        Output("normalize-toggle", "style"),
        Output("toggle-knob", "style"),
        Output("raw-label", "style"),
        Output("norm-label", "style"),
        Input("normalize-toggle", "n_clicks"),
    )
    def update_toggle_style(n_clicks):
        is_norm = (n_clicks % 2 == 1)   # odd clicks = Normalize on

        toggle_style = {
            "width": "44px", "height": "24px", "borderRadius": "12px",
            "background": "#4a9eff" if is_norm else "rgba(74,158,255,0.25)",
            "position": "relative", "cursor": "pointer", "flexShrink": "0",
            "border": "1px solid rgba(74,158,255,0.6)",
        }
        knob_style = {
            "width": "18px", "height": "18px", "borderRadius": "50%",
            "background": "white", "position": "absolute",
            "top": "2px",
            "right": "3px" if is_norm else "auto",
            "left": "auto" if is_norm else "3px",
            "transition": "left 0.2s, right 0.2s",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.3)",
        }
        raw_style = {
            "color": "white" if not is_norm else "#a8d4ff",
            "fontSize": "13px",
            "fontWeight": "700" if not is_norm else "500",
        }
        norm_style = {
            "color": "white" if is_norm else "#a8d4ff",
            "fontSize": "13px",
            "fontWeight": "700" if is_norm else "500",
        }
        return toggle_style, knob_style, raw_style, norm_style

    # ── Select all / deselect all checkboxes ──
    @app.callback(
        [Output({"type": "sensor-check", "index": sid}, "value") for sid in all_ids],
        Input("select-all-btn", "n_clicks"),
        State("select-all-btn", "children"),
        prevent_initial_call=True,
    )
    def toggle_select_all(n_clicks, label):
        # Odd clicks = select all, even = deselect all
        if n_clicks % 2 == 1:
            return [[sid] for sid in all_ids]   # all checked
        else:
            return [[] for _ in all_ids]         # all unchecked

    # ── Update "Select all" label text ──
    @app.callback(
        Output("select-all-btn", "children"),
        Input("select-all-btn", "n_clicks"),
    )
    def update_select_label(n_clicks):
        return "Deselect all" if n_clicks % 2 == 1 else "Select all"

    # ── Update chart every 3 s from simulation ring buffer ──
    @app.callback(
        Output("sensor-chart", "figure"),
        Output("chart-legend", "children"),
        Input("sensor-poll-interval", "n_intervals"),
        Input({"type": "sensor-check", "index": dash.ALL}, "value"),
        Input("normalize-toggle", "n_clicks"),
        State("sensor-engine-id-store", "data"),
    )
    def update_chart(n_intervals, check_values, n_clicks, engine_db_id):
        is_norm = (n_clicks % 2 == 1)

        selected = [
            all_ids[i]
            for i, vals in enumerate(check_values)
            if vals
        ]
        if not selected:
            selected = [all_ids[0]]

        # Pull live sensor rows from the simulation ring buffer
        sensor_history = None
        cluster_info = None
        if engine_db_id:
            try:
                from engine_simulation_manager import (
                    get_sensor_history, get_engine_model_type, _CLUSTER_CACHE
                )
                sensor_history = get_sensor_history(engine_db_id) or None
                # Get cluster info for FD002/FD004 per-cluster normalization
                _mt = get_engine_model_type(engine_db_id)
                if _mt:
                    _ci = _CLUSTER_CACHE.get(_mt, (None, None, None))
                    if _ci and _ci[0] is not None:
                        cluster_info = _ci
            except Exception:
                pass

        fig = build_sensor_chart(selected, sensor_history=sensor_history,
                                 normalize=is_norm, cluster_info=cluster_info)

        legend = [
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "6px"},
                children=[
                    html.Div(style={"width": "24px", "height": "2px",
                                    "background": ALL_SENSORS[sid]["color"]}),
                    html.Span(
                        f"{ALL_SENSORS[sid]['label']} — {ALL_SENSORS[sid]['desc']}",
                        style={"color": "#a8d4ff", "fontSize": "11px"}
                    )
                ]
            )
            for sid in selected if sid in ALL_SENSORS
        ]
        return fig, legend

    # ── Sidebar toggle ──
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
    app.layout = create_sensor_trends_layout()
    register_sensor_callbacks(app)
    app.run(debug=True)
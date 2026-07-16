import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import base64
import numpy as np
from assets.components import (build_sidebar, build_topbar, icon_sidebar)

def build_engine_3d_model(status="healthy", degradation_type=None):
    """
    Returns an html.Iframe pointing to the static engine_3d_viewer.html in assets/.
    Passes status and degradation_type as URL params for conditional blinking.
    """
    params = f"?status={status}"
    if degradation_type:
        params += f"&degradation={degradation_type.replace(' ', '+')}"
    return html.Iframe(
        src=f"/assets/engine_3d_viewer.html{params}",
        id="engine-3d-iframe",
        style={
            "width": "100%",
            "height": "270px",
            "border": "none",
            "background": "transparent",
            "display": "block",
        },
    )


# ─────────────────────────────────────────────
#  RUL LINE CHART
# ─────────────────────────────────────────────

def build_rul_chart(cycles=None, actual_ruls=None, predicted_ruls=None,
                    warn_thresh: int = 62, crit_thresh: int = 30,
                    window_size: int = 45):
    """
    Plot actual RUL and predicted RUL over cycles from real rul_predictions data.
    Falls back to a flat placeholder when no data is available yet.
    """
    fig = go.Figure()

    has_actual    = actual_ruls    and any(v is not None for v in actual_ruls)
    has_predicted = predicted_ruls and any(v is not None for v in predicted_ruls)

    x_min = window_size   # predictions never start before the window fills
    x_max = None
    y_max = warn_thresh + 10

    if not cycles or (not has_actual and not has_predicted):
        # ── Placeholder when simulation hasn't produced data yet ──
        fig.add_annotation(
            text=f"Warming up \u2014 predictions start after cycle {window_size}",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(color="rgba(168,212,255,0.5)", size=13),
        )
    else:
        x = cycles

        if has_actual:
            fig.add_trace(go.Scatter(
                x=x, y=actual_ruls,
                mode="lines",
                name="Actual RUL",
                line=dict(color="#4a9eff", width=2),
                connectgaps=True,
            ))

        if has_predicted:
            fig.add_trace(go.Scatter(
                x=x, y=predicted_ruls,
                mode="lines",
                name="Predicted RUL",
                line=dict(color="#4a9eff", width=2),
                connectgaps=True,
            ))

            # Endpoint marker on the latest prediction
            latest_pred = next((v for v in reversed(predicted_ruls) if v is not None), None)
            latest_cyc  = next((c for c, v in zip(reversed(x), reversed(predicted_ruls)) if v is not None), None)
            if latest_pred is not None:
                fig.add_trace(go.Scatter(
                    x=[latest_cyc], y=[latest_pred],
                    mode="markers",
                    showlegend=False,
                    marker=dict(color="#f5a623", size=9, symbol="circle"),
                ))

        x_max = max(x) if x else 1
        x_min = min(x) if x else 45

        # Dynamic y-axis: 10% headroom above the max value seen
        all_vals = [v for v in (predicted_ruls or []) if v is not None]
        y_max = max(max(all_vals) * 1.1, warn_thresh + 10) if all_vals else warn_thresh + 10

        # Warning threshold
        fig.add_shape(type="line", x0=x_min, x1=x_max, y0=warn_thresh, y1=warn_thresh,
                      line=dict(color="#ffd93d", width=1, dash="dot"))
        fig.add_annotation(x=x_max, y=warn_thresh, text="warn",
                           font=dict(color="#ffd93d", size=10),
                           showarrow=False, xanchor="left", xshift=4)
        # Critical threshold
        fig.add_shape(type="line", x0=x_min, x1=x_max, y0=crit_thresh, y1=crit_thresh,
                      line=dict(color="#ff4d4d", width=1, dash="dot"))
        fig.add_annotation(x=x_max, y=crit_thresh, text="crit",
                           font=dict(color="#ff4d4d", size=10),
                           showarrow=False, xanchor="left", xshift=4)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=50, t=10, b=10),
        autosize=True,
        legend=dict(
            orientation="h", x=1, y=1.15, xanchor="right",
            font=dict(color="#a8d4ff", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=False,
            color="#a8d4ff",
            zeroline=False,
            showticklabels=False,
            range=[x_min, x_max] if x_max is not None else None,
            title=dict(text="", font=dict(color="#a8d4ff", size=11)),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(74,158,255,0.1)",
            color="#a8d4ff", tickfont=dict(size=10),
            zeroline=False,
            range=[0, y_max],
            title=dict(text="RUL", font=dict(color="#a8d4ff", size=11)),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0d1e3a",
            bordercolor="rgba(74,158,255,0.4)",
            font=dict(color="white", size=12),
        ),
    )
    return fig


# ─────────────────────────────────────────────
#  TOP DRIVERS (SHAP) BAR CHART
# ─────────────────────────────────────────────

def build_shap_chart(shap_data=None):
    """
    Render the Top Drivers (feature importance) bar chart.
    shap_data: list of {"sensor": str, "score": float} sorted by |score| desc,
               or None/[] to show a placeholder.
    Shows the top 6 features by absolute contribution.
    """
    # Fall back to placeholder if no data yet
    if not shap_data:
        fig = go.Figure()
        fig.add_annotation(
            text="Feature importance will appear once predictions start",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(color="rgba(168,212,255,0.5)", size=12),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=40, t=10, b=10), height=220,
            xaxis=dict(visible=False), yaxis=dict(visible=False),
        )
        return fig

    # Take top 6 by absolute score — highest impact first.
    # With autorange="reversed" on the y-axis, the first item renders at the top.
    top6 = sorted(shap_data, key=lambda x: abs(x["score"]), reverse=True)[:6]

    sensors = [d["sensor"] for d in top6]
    values  = [d["score"]  for d in top6]

    colors = [
        "#ff6b6b" if v < -0.3 else
        "#f5a623" if v < 0 else
        "#4a9eff" if v < 0.15 else
        "#00c875"
        for v in values
    ]

    fig = go.Figure(go.Bar(
        x=values,
        y=sensors,
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.2f}" for v in values],
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(color="white", size=10),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        height=220,
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(74,158,255,0.1)",
            zeroline=True,
            zerolinecolor="rgba(74,158,255,0.3)",
            color="#a8d4ff",
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=False,
            color="#a8d4ff",
            tickfont=dict(size=12, color="white"),
            autorange="reversed",
        ),
        hoverlabel=dict(
            bgcolor="#0d1e3a",
            bordercolor="rgba(74,158,255,0.4)",
            font=dict(color="white", size=12),
        ),
    )
    return fig

# ─────────────────────────────────────────────
#  STATUS BADGE
# ─────────────────────────────────────────────

def status_badge(status: str):
    cfg = {
        "healthy":  {"bg": "rgba(0,200,100,0.18)", "border": "#00c875", "color": "#00c875"},
        "warning":  {"bg": "rgba(255,217,61,0.18)", "border": "#ffd93d", "color": "#ffd93d"},
        "critical": {"bg": "rgba(255,77,77,0.18)",  "border": "#ff4d4d", "color": "#ff4d4d"},
    }
    c = cfg.get(status.lower(), cfg["healthy"])
    return html.Span(
        status.upper(),
        style={
            "background": c["bg"],
            "color": c["color"],
            "border": f"1px solid {c['border']}",
            "borderRadius": "20px",
            "padding": "3px 12px",
            "fontSize": "11px",
            "fontWeight": "700",
            "letterSpacing": "0.8px",
        }
    )


# ─────────────────────────────────────────────
#  CARD WRAPPER
# ─────────────────────────────────────────────

def card(children, style_extra=None):
    base = {
        "background": "#101e36",
        "border": "1px solid rgba(74,158,255,0.18)",
        "borderRadius": "14px",
        "padding": "20px 22px",
    }
    if style_extra:
        base.update(style_extra)
    return html.Div(style=base, children=children)


def card_title(text):
    return html.Div(
        text,
        style={"color": "white", "fontWeight": "700", "fontSize": "16px", "marginBottom": "14px"}
    )


# ─────────────────────────────────────────────
#  MAIN CONTENT: OVERVIEW PAGE
# ─────────────────────────────────────────────

def build_overview_content(engine_id="01", status="healthy", rul=120, degradation=80):
    degrade_color = (
        "#00c875" if degradation >= 70 else
        "#ffd93d" if degradation >= 40 else
        "#ff4d4d"
    )

    if degradation >= 70:
        degrade_label = ("No Degradation Detected", "#00c875", "rgba(0,200,117,0.12)", "#00c875")
    elif degradation >= 40:
        degrade_label = ("Moderate Degradation", "#ffd93d", "rgba(255,217,61,0.12)", "#ffd93d")
    else:
        degrade_label = ("Severe Degradation", "#ff4d4d", "rgba(255,77,77,0.12)", "#ff4d4d")

    sensor_list = [
        ("T30", "HPC outlet temperature"),
        ("P30", "HPC outlet pressure"),
        ("Nf",  "Fan speed"),
        ("phi", "Fuel-air ratio"),
        ("W31", "HPT coolant bleed"),
    ]

    return html.Div(
        style={
            "flex": "1",
            "display": "flex",
            "flexDirection": "column",
            "minWidth": "0",
            "height": "100vh",       # ← full viewport height
            "overflow": "hidden",    # ← prevent outer scroll
        },
        children=[
            # ── Fixed topbar (stays at top always) ──
            html.Div(
                style={
                    "background": "linear-gradient(90deg, #0d2045 0%, #071530 100%)",
                    "borderBottom": "1px solid rgba(74,158,255,0.18)",
                    "padding": "0 28px",
                    "height": "60px",
                    "minHeight": "60px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "flexShrink": "0",   # ← never shrink
                    "zIndex": "100",
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
            ),

            # ── Scrollable content below topbar ──
            html.Div(
                style={
                    "flex": "1",
                    "overflowY": "auto",   # ← only this scrolls
                    "padding": "24px 28px",
                },
                children=[
                    # Engine title row
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "14px", "marginBottom": "22px"},
                        children=[
                            html.H2(
                                f"ENGINE-{engine_id}",
                                style={"margin": "0", "color": "white", "fontSize": "22px", "fontWeight": "800"}
                            ),
                            status_badge(status),
                        ]
                    ),

                    # Row 1: RUL Chart + RUL Panel
                    html.Div(
                        style={"display": "flex", "gap": "20px", "marginBottom": "20px"},
                        children=[
                            card(
                                style_extra={"flex": "3"},
                                children=[
                                    card_title("Predicted RUL"),
                                    dcc.Graph(
                                        figure=build_rul_chart(rul_value=rul),
                                        config={"displayModeBar": False},
                                        style={"height": "200px"},
                                    )
                                ]
                            ),
                            card(
                                style_extra={"flex": "1", "display": "flex", "flexDirection": "column",
                                             "alignItems": "center", "justifyContent": "center", "gap": "16px"},
                                children=[
                                    html.Div("Remaining Useful Life",
                                             style={"color": "#a8d4ff", "fontSize": "13px", "fontWeight": "600",
                                                    "textAlign": "center", "letterSpacing": "0.4px"}),
                                    html.Div(
                                        style={"textAlign": "center"},
                                        children=[
                                            html.Div(str(rul),
                                                     style={"color": "#00c875", "fontSize": "58px",
                                                            "fontWeight": "800", "lineHeight": "1"}),
                                            html.Div("cycles", style={"color": "#a8d4ff", "fontSize": "14px",
                                                                       "marginTop": "4px"})
                                        ]
                                    ),
                                    html.Div(
                                        style={"width": "100%", "borderTop": "1px solid rgba(74,158,255,0.18)",
                                               "paddingTop": "14px", "display": "flex",
                                               "justifyContent": "space-between", "alignItems": "center"},
                                        children=[
                                            html.Span("Degradation", style={"color": "#a8d4ff", "fontSize": "12px"}),
                                            html.Span(f"{degradation}%", style={"color": degrade_color,
                                                                                  "fontWeight": "700", "fontSize": "14px"})
                                        ]
                                    ),
                                    html.Div(
                                        degrade_label[0],
                                        style={
                                            "width": "100%", "textAlign": "center",
                                            "background": degrade_label[2],
                                            "border": f"1.5px solid {degrade_label[3]}",
                                            "borderRadius": "10px", "color": degrade_label[1],
                                            "fontSize": "12px", "fontWeight": "700", "padding": "8px 0",
                                        }
                                    )
                                ]
                            )
                        ]
                    ),

                    # Row 2: Sensor Trends + Top Drivers
                    html.Div(
                        style={"display": "flex", "gap": "20px"},
                        children=[
                            card(
                                style_extra={"flex": "1"},
                                children=[
                                    card_title("Sensor Trends"),
                                    html.Div(
                                        style={"display": "flex", "flexDirection": "column", "gap": "0"},
                                        children=[
                                            html.Div(
                                                style={
                                                    "display": "flex", "alignItems": "center",
                                                    "justifyContent": "space-between",
                                                    "padding": "10px 0",
                                                    "borderBottom": "1px solid rgba(74,158,255,0.1)",
                                                    "cursor": "pointer",
                                                },
                                                children=[
                                                    html.Span(f"{code} ({label})",
                                                              style={"color": "#a8d4ff", "fontSize": "13px"}),
                                                    html.Span("→", style={"color": "rgba(74,158,255,0.5)", "fontSize": "14px"}),
                                                ]
                                            )
                                            for code, label in sensor_list
                                        ]
                                    )
                                ]
                            ),
                            card(
                                style_extra={"flex": "1"},
                                children=[
                                    card_title("Top Drivers"),
                                    dcc.Graph(
                                        figure=build_shap_chart(),
                                        config={"displayModeBar": False},
                                        style={"height": "220px"},
                                    )
                                ]
                            ),
                        ]
                    )
                ]
            )
        ]
    )

def build_overview_body(engine_id="01", status="healthy", rul=None, degradation=None, degradation_type=None, engine_db_id=None):
    """Returns just the scrollable inner content children (a list)."""
    # Default display values when no prediction data available
    rul_display = str(int(rul)) if rul is not None else "\u2014"
    deg_display = f"{degradation}%" if degradation is not None else "\u2014"
    degradation = degradation if degradation is not None else 100

    degrade_color = (
        "#00c875" if degradation >= 70 else
        "#ffd93d" if degradation >= 40 else
        "#ff4d4d"
    )
    # Degradation type label — always blue, just shows the fault mode
    if degradation_type:
        degrade_label = (degradation_type, "#4a9eff", "rgba(74,158,255,0.12)", "#4a9eff")
    else:
        degrade_label = ("No Degradation Detected", "#4a9eff", "rgba(74,158,255,0.12)", "#4a9eff")

    return [
        # Engine title row
        html.Div(
            style={"display": "flex", "alignItems": "center", "gap": "14px", "marginBottom": "22px"},
            children=[
                html.H2(f"ENGINE-{engine_id}",
                        style={"margin": "0", "color": "white", "fontSize": "22px", "fontWeight": "800"}),
                html.Div(id="engine-status-badge", children=[status_badge(status)]),
            ]
        ),

        # Row 1: 3D Engine Model + RUL Chart + RUL Panel
        html.Div(
            style={"display": "flex", "gap": "20px", "marginBottom": "20px"},
            children=[
                # ── 3D Holographic Engine Model Card ──
                card(
                    style_extra={
                        "flex": "4",
                        "display": "flex",
                        "flexDirection": "column",
                        "background": "linear-gradient(160deg, #0e1e36 0%, #101e36 60%, #0b1a30 100%)",
                        "border": "1px solid rgba(0,200,255,0.20)",
                        "boxShadow": "0 0 24px rgba(0,200,255,0.08), inset 0 0 40px rgba(0,200,255,0.03)",
                        "position": "relative",
                        "overflow": "hidden",
                    },
                    children=[
                        # Holographic scanline overlay (CSS via inline style)
                        html.Div(style={
                            "position": "absolute", "top": "0", "left": "0",
                            "width": "100%", "height": "100%",
                            "background": "repeating-linear-gradient("
                                "0deg, rgba(0,200,255,0.025) 0px, "
                                "rgba(0,200,255,0.025) 1px, transparent 1px, transparent 4px)",
                            "pointerEvents": "none", "zIndex": "1",
                        }),
                        html.Div(
                            style={"position": "relative", "zIndex": "2"},
                            children=[
                                html.Div(
                                    style={"display": "flex", "alignItems": "center",
                                           "justifyContent": "space-between", "marginBottom": "4px"},
                                    children=[
                                        card_title("3D ENGINE MODEL"),
                                        html.Div(
                                            "CMAPSS TURBOFAN",
                                            style={
                                                "fontSize": "9px", "color": "rgba(0,200,255,0.6)",
                                                "letterSpacing": "1.5px", "fontWeight": "700",
                                                "fontFamily": "Courier New, monospace",
                                            }
                                        ),
                                    ]
                                ),
                                # Three.js WebGL holographic engine (html.Iframe)
                                build_engine_3d_model(status=status, degradation_type=degradation_type),
                            ]
                        ),
                    ]
                ),
                card(
                    style_extra={"flex": "2", "display": "flex", "flexDirection": "column"},
                    children=[
                        card_title("Predicted RUL"),
                        dcc.Graph(
                            id="rul-line-chart",
                            figure=build_rul_chart(),
                            config={"displayModeBar": False},
                            style={"flex": "1", "minHeight": "0"},
                        )
                    ]
                ),
                card(
                    style_extra={"flex": "1", "display": "flex", "flexDirection": "column",
                                 "alignItems": "center", "justifyContent": "center", "gap": "16px"},
                    children=[
                        html.Div("Remaining Useful Life",
                                 style={"color": "#a8d4ff", "fontSize": "13px", "fontWeight": "600",
                                        "textAlign": "center"}),
                        html.Div(style={"textAlign": "center"}, children=[
                        html.Div(id="rul-value-display", children=rul_display,
                                     style={"color": "rgba(168,212,255,0.4)", "fontSize": "58px",
                                            "fontWeight": "800", "lineHeight": "1"}),
                            html.Div("cycles", style={"color": "#a8d4ff", "fontSize": "14px", "marginTop": "4px"})
                        ]),
                        html.Div(
                            style={"width": "100%", "borderTop": "1px solid rgba(74,158,255,0.18)",
                                   "paddingTop": "14px", "display": "flex",
                                   "justifyContent": "space-between", "alignItems": "center"},
                            children=[
                                html.Span("Degradation", style={"color": "#a8d4ff", "fontSize": "12px"}),
                                html.Span(id="degradation-display", children=deg_display,
                                          style={"color": "rgba(168,212,255,0.4)", "fontWeight": "700", "fontSize": "14px"})
                            ]
                        ),
                        html.Div(
                            id="degrade-label-display",
                            children="Loading\u2026",
                            style={
                                "width": "100%", "textAlign": "center",
                                "background": "rgba(74,158,255,0.06)",
                                "border": "1.5px solid rgba(74,158,255,0.2)",
                                "borderRadius": "10px", "color": "rgba(168,212,255,0.4)",
                                "fontSize": "12px", "fontWeight": "700", "padding": "8px 0",
                            }
                        ),
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "justifyContent": "center",
                                   "gap": "6px", "marginTop": "6px"},
                            children=[
                                html.Span("Confidence:", style={
                                    "color": "rgba(168,212,255,0.5)", "fontSize": "11px",
                                }),
                                html.Span(id="overview-confidence-score", children="—", style={
                                    "color": "#4a9eff", "fontSize": "12px", "fontWeight": "700",
                                }),
                            ]
                        ),
                    ]
                )
            ]
        ),

        # Row 2: Sensor Trends (3 mini charts) + Top Drivers
        html.Div(
            style={"display": "flex", "gap": "20px"},
            children=[
                card(
                    style_extra={"flex": "3"},
                    children=[
                        # Header with "more information" link
                        html.Div(
                            style={"display": "flex", "alignItems": "center",
                                   "justifyContent": "space-between", "marginBottom": "10px"},
                            children=[
                                card_title("Sensor Trends"),
                                html.A(
                                    style={"display": "flex", "alignItems": "center", "gap": "4px",
                                           "color": "#4a9eff", "fontSize": "11px", "fontWeight": "600",
                                           "textDecoration": "none", "cursor": "pointer",
                                           "opacity": "0.8"},
                                    href="/sensor-trends",
                                    children=[
                                        html.Span("more information"),
                                        html.Span("\u2192", style={"fontSize": "14px"}),
                                    ]
                                ),
                            ]
                        ),
                        # 3 mini charts in a row
                        html.Div(
                            style={"display": "flex", "gap": "12px", "marginBottom": "8px"},
                            children=[
                                html.Div(style={"flex": "1", "minWidth": "0"}, children=[
                                    html.Div("Upward Trending (Rolling Mean)",
                                             style={"color": "#a8d4ff", "fontSize": "10px",
                                                    "fontWeight": "600", "marginBottom": "4px",
                                                    "letterSpacing": "0.3px"}),
                                    dcc.Graph(
                                        id="sensor-mini-up",
                                        config={"displayModeBar": False},
                                        style={"height": "160px"},
                                    ),
                                ]),
                                html.Div(style={"flex": "1", "minWidth": "0"}, children=[
                                    html.Div("Downward Trending (Rolling Mean)",
                                             style={"color": "#a8d4ff", "fontSize": "10px",
                                                    "fontWeight": "600", "marginBottom": "4px",
                                                    "letterSpacing": "0.3px"}),
                                    dcc.Graph(
                                        id="sensor-mini-down",
                                        config={"displayModeBar": False},
                                        style={"height": "160px"},
                                    ),
                                ]),
                                html.Div(style={"flex": "1", "minWidth": "0"}, children=[
                                    html.Div("All Sensors (Standardized)",
                                             style={"color": "#a8d4ff", "fontSize": "10px",
                                                    "fontWeight": "600", "marginBottom": "4px",
                                                    "letterSpacing": "0.3px"}),
                                    dcc.Graph(
                                        id="sensor-mini-all",
                                        config={"displayModeBar": False},
                                        style={"height": "160px"},
                                    ),
                                ]),
                            ]
                        ),
                        # Shared legend
                        html.Div(
                            id="sensor-mini-legend",
                            style={"display": "flex", "flexWrap": "wrap", "gap": "8px 14px",
                                   "justifyContent": "center", "paddingTop": "4px"},
                        ),
                    ]
                ),
                card(
                    style_extra={"flex": "1"},
                    children=[
                        html.Div(
                            style={"display": "flex", "alignItems": "center",
                                   "justifyContent": "space-between", "marginBottom": "10px"},
                            children=[
                                card_title("Top Drivers"),
                                html.A(
                                    style={"display": "flex", "alignItems": "center", "gap": "4px",
                                           "color": "#4a9eff", "fontSize": "11px", "fontWeight": "600",
                                           "textDecoration": "none", "cursor": "pointer",
                                           "opacity": "0.8"},
                                    href=f"/degradation-analysis/{engine_db_id}" if engine_db_id else "/degradation-analysis",
                                    children=[
                                        html.Span("more information"),
                                        html.Span("\u2192", style={"fontSize": "14px"}),
                                    ]
                                ),
                            ]
                        ),
                        dcc.Graph(
                            id="shap-chart",
                            figure=build_shap_chart(),
                            config={"displayModeBar": False},
                            style={"height": "220px"},
                        )
                    ]
                ),
            ]
        )
    ]


# ─────────────────────────────────────────────
#  PAGE LAYOUT ENTRY POINT
# ─────────────────────────────────────────────

def create_overview_layout(supabase, engine_db_id=None):
    # Defaults
    engine_id        = "01"
    status           = "healthy"
    rul              = None
    degradation      = None
    degradation_type = None

    try:
        if supabase and engine_db_id is not None:
            # Fetch engine row by PK
            eng_resp = supabase.table("engines") \
                .select("*") \
                .eq("id", engine_db_id) \
                .single() \
                .execute()
            engine = eng_resp.data or {}

            # Fetch latest RUL prediction for this engine
            pred_resp = supabase.table("rul_predictions") \
                .select("*") \
                .eq("engine_id", engine_db_id) \
                .order("predicted_at", desc=True) \
                .limit(1) \
                .execute()
            pred = pred_resp.data[0] if pred_resp.data else {}

            engine_id   = str(engine.get("engine_id", "01")).zfill(2)
            status      = (engine.get("condition_status") or "healthy").lower().strip()
            if status not in ("healthy", "warning", "critical"):
                status = "healthy"

            degradation_type = engine.get("degradation_type") or None

            if pred.get("predicted_rul") is not None:
                rul         = float(pred["predicted_rul"])
                max_life    = 130
                degradation = max(0, min(100, int((rul / max_life) * 100)))

            print(f"[DEBUG] Overview engine={engine}, pred={pred}")

    except Exception as e:
        import traceback
        print(f"[ERROR] overview fetch: {traceback.format_exc()}")

    return html.Div(
        style={
            "height": "100vh",
            "display": "flex",
            "flexDirection": "column",   # ← topbar on top, row below
            "fontFamily": "'Segoe UI', 'Inter', sans-serif",
            "background": "#0a1628",
            "color": "white",
            "overflow": "hidden",
        },
        children=[
            dcc.Location(id="url-overview", refresh=False),
            dcc.Store(id="overview-engine-id-store", data=engine_db_id),
            dcc.Interval(id="rul-poll-interval", interval=5_000, n_intervals=0),
            build_topbar(),
            html.Div(
                style={
                    "flex": "1",
                    "display": "flex",
                    "flexDirection": "row",   # ← sidebar | content
                    "overflow": "hidden",
                    "minHeight": "0",         # ← critical for flex children to scroll
                },
                children=[
                    # Sidebar
                    build_sidebar(active_page="overview", engine_db_id=engine_db_id),

                    # Scrollable content
                    html.Div(
                        style={
                            "flex": "1",
                            "overflowY": "auto",
                            "padding": "24px 28px",
                            "minWidth": "0",
                        },
                        children=build_overview_body(
                            engine_id=engine_id,
                            status=status,
                            rul=None,
                            degradation=None,
                            degradation_type=degradation_type,
                            engine_db_id=engine_db_id,
                        )
                    )
                ]
            )
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def register_overview_callbacks(app, supabase=None):
    """
    Register the live RUL chart polling callback.
    Called once from app.py at startup.
    """

    @app.callback(
        Output("rul-line-chart",       "figure"),
        Output("rul-value-display",    "children"),
        Output("rul-value-display",    "style"),
        Output("degradation-display",  "children"),
        Output("degradation-display",  "style"),
        Output("degrade-label-display","children"),
        Output("degrade-label-display","style"),
        Output("engine-status-badge",  "children"),
        Output("shap-chart",           "figure"),
        Output("overview-confidence-score", "children"),
        Input("rul-poll-interval",     "n_intervals"),
        State("overview-engine-id-store", "data"),
        prevent_initial_call=False,
    )
    def refresh_rul_chart(n_intervals, engine_db_id):
        import json as _json
        from engine_simulation_manager import WINDOW_SIZES
        from degradation_analysis import compute_confidence_score
        MAX_LIFE = 130
        WARN_THRESH = 62
        CRIT_THRESH = 30
        _window_size = 45  # default

        # ── Fetch engine model_type to determine window size ──
        if supabase and engine_db_id:
            try:
                _mt_resp = supabase.table("engines") \
                    .select("model_type") \
                    .eq("id", engine_db_id) \
                    .single() \
                    .execute()
                if _mt_resp.data:
                    _mt = _mt_resp.data.get("model_type", "FD001")
                    _window_size = WINDOW_SIZES.get(_mt, 45)
            except Exception:
                pass

        # ── Fetch thresholds from Supabase ──
        if supabase:
            try:
                t_resp = supabase.table("alert_thresholds") \
                    .select("warning_threshold, critical_threshold") \
                    .order("updated_at", desc=True) \
                    .limit(1) \
                    .execute()
                if t_resp.data:
                    WARN_THRESH = int(t_resp.data[0].get("warning_threshold", WARN_THRESH))
                    CRIT_THRESH = int(t_resp.data[0].get("critical_threshold", CRIT_THRESH))
            except Exception:
                pass  # fall back to defaults

        cycles_list:    list = []
        predicted_list: list = []
        latest_pred_rul: float | None = None
        latest_shap: list = []

        if supabase and engine_db_id:
            try:
                # Retry up to 2 times on transient network errors (Windows socket issue)
                _resp_data = None
                for _attempt in range(3):
                    try:
                        resp = supabase.table("rul_predictions") \
                            .select("cycle, predicted_rul, shap_values") \
                            .eq("engine_id", engine_db_id) \
                            .order("cycle", desc=False) \
                            .execute()
                        _resp_data = resp.data or []
                        break
                    except Exception as _net_err:
                        if _attempt < 2:
                            import time as _t
                            _t.sleep(1)
                        else:
                            raise

                for row in _resp_data:
                    cycles_list.append(row.get("cycle"))
                    predicted_list.append(
                        float(row["predicted_rul"]) if row.get("predicted_rul") is not None else None
                    )

                # Latest valid prediction + SHAP values
                for row in reversed(resp.data or []):
                    if row.get("predicted_rul") is not None:
                        latest_pred_rul = float(row["predicted_rul"])
                        raw_shap = row.get("shap_values")
                        if raw_shap:
                            try:
                                latest_shap = _json.loads(raw_shap) if isinstance(raw_shap, str) else raw_shap
                            except Exception:
                                latest_shap = []
                        break
            except Exception:
                import traceback
                print(f"[ERROR] rul poll: {traceback.format_exc()}")

        fig = build_rul_chart(
            cycles=cycles_list,
            predicted_ruls=predicted_list,
            warn_thresh=WARN_THRESH,
            crit_thresh=CRIT_THRESH,
            window_size=_window_size,
        )

        # ── No predictions yet — show neutral waiting state ──
        if latest_pred_rul is None:
            no_pred_style = {"color": "rgba(168,212,255,0.5)", "fontSize": "40px",
                             "fontWeight": "800", "lineHeight": "1"}
            neutral_label_style = {
                "width": "100%", "textAlign": "center",
                "background": "rgba(74,158,255,0.06)",
                "border": "1.5px solid rgba(74,158,255,0.2)",
                "borderRadius": "10px", "color": "rgba(168,212,255,0.5)",
                "fontSize": "12px", "fontWeight": "700", "padding": "8px 0",
            }
            return (
                fig, "—", no_pred_style,
                "—", {"color": "rgba(168,212,255,0.5)", "fontWeight": "700", "fontSize": "14px"},
                "Awaiting predictions…", neutral_label_style,
                [status_badge("healthy")],
                build_shap_chart(),
                "—",
            )

        rul_display = str(int(round(latest_pred_rul)))
        degradation = max(0, min(100, round((1 - latest_pred_rul / MAX_LIFE) * 100)))

        # Fetch degradation_type from engine for live display
        _deg_type = None
        if supabase and engine_db_id:
            try:
                _dt_resp = supabase.table("engines") \
                    .select("degradation_type") \
                    .eq("id", engine_db_id) \
                    .single() \
                    .execute()
                if _dt_resp.data:
                    _deg_type = _dt_resp.data.get("degradation_type")
            except Exception:
                pass

        label_text  = _deg_type if _deg_type else "No Degradation Detected"
        label_color = "#4a9eff"
        label_bg    = "rgba(74,158,255,0.12)"
        label_bdr   = "#4a9eff"

        # Color for RUL number and degradation % based on thresholds
        if latest_pred_rul > WARN_THRESH:
            rul_color = "#00c875"
        elif latest_pred_rul > CRIT_THRESH:
            rul_color = "#ffd93d"
        else:
            rul_color = "#ff4d4d"

        rul_number_style = {
            "color": rul_color,
            "fontSize": "58px",
            "fontWeight": "800",
            "lineHeight": "1",
        }
        degrade_pct_style = {
            "color": rul_color,
            "fontWeight": "700",
            "fontSize": "14px",
        }
        label_style = {
            "width": "100%", "textAlign": "center",
            "background": label_bg,
            "border": f"1.5px solid {label_bdr}",
            "borderRadius": "10px", "color": label_color,
            "fontSize": "12px", "fontWeight": "700", "padding": "8px 0",
        }

        # Derive status from thresholds
        if latest_pred_rul <= CRIT_THRESH:
            live_status = "critical"
        elif latest_pred_rul <= WARN_THRESH:
            live_status = "warning"
        else:
            live_status = "healthy"

        # Compute confidence score for display
        _confidence = compute_confidence_score(_deg_type, latest_shap) if latest_shap and _deg_type else None
        _confidence_display = f"{_confidence:.0%}" if _confidence is not None else "—"

        return (
            fig,
            rul_display,
            rul_number_style,
            f"{degradation}%",
            degrade_pct_style,
            label_text,
            label_style,
            [status_badge(live_status)],
            build_shap_chart(latest_shap),
            _confidence_display,
        )

    # ── Sensor mini-charts callback ──
    # All 14 informative CMAPSS sensors (the ones with actual variance)
    _ALL_SENSORS_MINI = ["T24", "T30", "T50", "Nf", "Ps30", "htBleed", "NRf",
                         "P30", "phi", "NRc", "BPR", "W31", "W32", "Nc"]

    # Sensor JSON key mapping (same as sensor_trends.py)
    _SENSOR_KEY = {
        "T2": "s1", "T24": "s2", "T30": "s3", "T50": "s4",
        "P2": "s5", "P15": "s6", "P30": "s7", "Nf": "s8",
        "Nc": "s9", "Ps30": "s11", "phi": "s12", "NRf": "s13",
        "NRc": "s14", "BPR": "s15", "htBleed": "s17", "W31": "s20", "W32": "s21",
    }
    _SENSOR_COLORS = {
        "T24": "#f5a623", "T30": "#ff4d4d", "T50": "#ff8c69",
        "Nf": "#00c875", "Ps30": "#a0f0c0", "NRf": "#c0d0ff",
        "BPR": "#ff9f43", "htBleed": "#e879f9",
        "P30": "#7b61ff", "Nc": "#00e5a0", "phi": "#ffd93d",
        "NRc": "#90a8e0", "W31": "#34d399", "W32": "#6ee7b7",
    }

    def _mini_chart_layout():
        return dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=30, r=8, t=5, b=28),
            height=160,
            showlegend=False,
            xaxis=dict(
                showgrid=False, zeroline=False,
                color="#a8d4ff", tickfont=dict(size=9),
                title=dict(text="Cycles", font=dict(size=9, color="#5a8ab5")),
            ),
            yaxis=dict(
                showgrid=True, gridcolor="rgba(74,158,255,0.08)",
                zeroline=False, color="#a8d4ff", tickfont=dict(size=9),
                title=dict(text="Std. Value", font=dict(size=8, color="#5a8ab5")),
            ),
            hovermode="closest",
            hoverlabel=dict(
                bgcolor="#0d1e3a", bordercolor="rgba(74,158,255,0.4)",
                font=dict(color="white", size=10),
                namelength=10,
            ),
        )

    def _extract_sensor_data(history, cluster_info=None):
        """
        Extract, standardize, smooth all sensors.
        For FD002/FD004: applies per-cluster normalization using KMeans centroids.
        Returns {sid: (cycles, smoothed, slope)}.
        """
        _RW = 10
        result = {}

        # If cluster normalization available, pre-normalize all rows
        # cluster_info = (centroids, cluster_means, cluster_stds) from model h5
        normalized_rows = None
        if cluster_info and cluster_info[0] is not None:
            centroids, cl_means, cl_stds = cluster_info
            # Build per-sensor normalized arrays using cluster assignment
            # OS columns are: operational_setting_1, operational_setting_2, operational_setting_3
            os_keys = ["operational_setting_1", "operational_setting_2", "operational_setting_3"]
            sensor_keys_ordered = ["s2", "s3", "s4", "s7", "s8", "s9", "s11",
                                   "s12", "s13", "s14", "s15", "s17", "s20", "s21"]
            # Map sensor_key index in cluster_means (first 14 are sensors, last 3 are OS)
            normalized_rows = []
            for row in history:
                sensors = row.get("sensors", row)
                # Get OS values for cluster assignment
                os_vals = []
                for ok in os_keys:
                    v = row.get(ok, sensors.get(ok, 0.0))
                    os_vals.append(float(v) if v is not None else 0.0)
                os_arr = np.array(os_vals, dtype=np.float32)
                # Assign to nearest centroid
                dists = np.linalg.norm(centroids - os_arr, axis=1)
                cid = int(np.argmin(dists))
                # Normalize this row's sensors using cluster scaler
                c_mean = cl_means[cid]  # (17,) — first 14 are sensors, last 3 OS
                c_std = cl_stds[cid].copy()
                c_std[c_std == 0] = 1.0
                norm_row = {}
                for idx, sk in enumerate(sensor_keys_ordered):
                    raw_val = sensors.get(sk)
                    if raw_val is not None:
                        norm_row[sk] = (float(raw_val) - c_mean[idx]) / c_std[idx]
                    else:
                        norm_row[sk] = None
                normalized_rows.append(norm_row)

        for sid in _ALL_SENSORS_MINI:
            json_key = _SENSOR_KEY.get(sid)
            if not json_key:
                continue
            vals = []
            if normalized_rows:
                # Use cluster-normalized values
                for norm_row in normalized_rows:
                    v = norm_row.get(json_key)
                    vals.append(v)
            else:
                # Fallback: raw values with global z-score
                for row in history:
                    sensors = row.get("sensors", row)
                    v = sensors.get(json_key)
                    vals.append(float(v) if v is not None else None)

            if not any(v is not None for v in vals):
                continue
            arr = np.array([v if v is not None else np.nan for v in vals], dtype=float)

            # If not using cluster normalization, apply global z-score
            if not normalized_rows:
                mean = np.nanmean(arr)
                std = np.nanstd(arr)
                if std > 0:
                    arr = (arr - mean) / std
                else:
                    arr = arr - mean

            smoothed = np.convolve(
                np.nan_to_num(arr, nan=0.0),
                np.ones(_RW) / _RW,
                mode="valid"
            )
            cycles = list(range(_RW, _RW + len(smoothed)))
            x = np.arange(len(smoothed), dtype=float)
            slope = np.polyfit(x, smoothed, 1)[0] if len(x) > 1 else 0.0
            result[sid] = (cycles, smoothed.tolist(), slope)
        return result

    def _build_mini_fig(sensor_data, sensor_ids):
        """Build a mini chart from pre-computed sensor data for given IDs."""
        fig = go.Figure()
        if not sensor_data or not sensor_ids:
            fig.add_annotation(
                text="Awaiting data\u2026", x=0.5, y=0.5,
                xref="paper", yref="paper", showarrow=False,
                font=dict(color="rgba(168,212,255,0.5)", size=11),
            )
            fig.update_layout(**_mini_chart_layout())
            return fig
        for sid in sensor_ids:
            if sid not in sensor_data:
                continue
            cycles, smoothed, _ = sensor_data[sid]
            fig.add_trace(go.Scatter(
                x=cycles, y=smoothed,
                mode="lines", name=sid,
                line=dict(color=_SENSOR_COLORS.get(sid, "#4a9eff"), width=1.2),
                connectgaps=True,
            ))
        fig.update_layout(**_mini_chart_layout())
        return fig

    @app.callback(
        Output("sensor-mini-up", "figure"),
        Output("sensor-mini-down", "figure"),
        Output("sensor-mini-all", "figure"),
        Output("sensor-mini-legend", "children"),
        Input("rul-poll-interval", "n_intervals"),
        State("overview-engine-id-store", "data"),
        prevent_initial_call=False,
    )
    def update_sensor_mini_charts(n_intervals, engine_db_id):
        history = []
        cluster_info = None
        if engine_db_id:
            try:
                from engine_simulation_manager import get_sensor_history, _CLUSTER_CACHE
                history = get_sensor_history(engine_db_id) or []
                # Get model_type for this engine to check if cluster normalization applies
                if supabase:
                    _eng_resp = supabase.table("engines") \
                        .select("model_type") \
                        .eq("id", engine_db_id) \
                        .single() \
                        .execute()
                    if _eng_resp.data:
                        _mt = _eng_resp.data.get("model_type", "FD001")
                        cluster_info = _CLUSTER_CACHE.get(_mt, (None, None, None))
                        # Only use if all 3 parts are present
                        if cluster_info and cluster_info[0] is None:
                            cluster_info = None
            except Exception:
                pass

        if not history:
            empty = go.Figure()
            empty.add_annotation(
                text="Awaiting data\u2026", x=0.5, y=0.5,
                xref="paper", yref="paper", showarrow=False,
                font=dict(color="rgba(168,212,255,0.5)", size=11),
            )
            empty.update_layout(**_mini_chart_layout())
            return empty, empty, empty, []

        # Extract and dynamically classify by slope direction
        sensor_data = _extract_sensor_data(history, cluster_info=cluster_info)
        up_ids   = [sid for sid, (_, _, slope) in sensor_data.items() if slope > 0]
        down_ids = [sid for sid, (_, _, slope) in sensor_data.items() if slope <= 0]
        all_ids  = list(sensor_data.keys())

        fig_up   = _build_mini_fig(sensor_data, up_ids)
        fig_down = _build_mini_fig(sensor_data, down_ids)
        fig_all  = _build_mini_fig(sensor_data, all_ids)

        # Shared legend
        legend_items = []
        for sid in all_ids:
            legend_items.append(
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "4px"},
                    children=[
                        html.Div(style={"width": "14px", "height": "2px",
                                        "background": _SENSOR_COLORS.get(sid, "#4a9eff"),
                                        "borderRadius": "1px"}),
                        html.Span(sid, style={"color": "#a8d4ff", "fontSize": "9px"}),
                    ]
                )
            )
        return fig_up, fig_down, fig_all, legend_items


# ─────────────────────────────────────────────
#  STANDALONE RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
    )
    app.layout = create_overview_layout()
    app.run(debug=True)
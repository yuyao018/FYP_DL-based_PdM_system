"""
Degradation Analysis page — SHAP beeswarm, LLM explanation, SHAP trend over cycles.

Replaces the former "Explainability AI" page.  Provides:
  • Header: engine selector, detected degradation type, confidence score
  • Row 1 col 1: SHAP beeswarm-style horizontal bar chart (feature impact on RUL)
  • Row 1 col 2: LLM-generated natural language explanation (Gemini Flash)
  • Row 2: SHAP value trend line chart for top sensors over cycles
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, MATCH, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import json as _json
import os
import base64
import traceback
from datetime import datetime
from assets.components import (build_sidebar, build_topbar, icon_shap)

# ─────────────────────────────────────────────
#  CONFIDENCE SCORE COMPUTATION
# ─────────────────────────────────────────────
# NOTE — Open Item:
# The fault-mode detector is rule-based (rolling slope + reversal detection
# across s7, s9, s12, s14, BPR), not a classifier with native probability
# output.  The confidence_score below is a *derived heuristic*:
#
#   confidence = proportion of fault-defining sensors whose slope direction
#                and SHAP sign match the expected signature for that fault mode,
#                weighted by how far each SHAP score deviates from zero.
#
# This is a V1 approximation.  Future work should consider:
#   - Rolling-slope magnitude vs. threshold ratio (continuous signal)
#   - Reversal timing consistency across correlated sensors
#   - Ensemble voting across multiple cycle windows
#
# The function below operates on the SHAP data already computed per cycle
# (available in rul_predictions.shap_values).  A more robust implementation
# would also consume the raw sensor time-series slopes, which requires
# fetching additional history and computing rolling regressions.  That is
# flagged as a follow-on design task.

# Expected SHAP sign patterns per fault mode (negative = drives RUL down)
_HPC_EXPECTED_SIGNS = {
    "T30": -1, "P30": -1, "phi": -1, "Ps30": -1, "htBleed": -1, "T24": -1,
}
_FAN_EXPECTED_SIGNS = {
    "Nf": -1, "NRf": -1, "BPR": -1, "Nc": -1, "NRc": -1,
}

_HPC_SENSORS = set(_HPC_EXPECTED_SIGNS.keys())
_FAN_SENSORS = set(_FAN_EXPECTED_SIGNS.keys())


def compute_confidence_score(degradation_type: str | None, shap_data: list[dict]) -> float | None:
    """
    Derive a confidence score (0–1) for the detected fault mode from SHAP data.

    Method: For each sensor in the expected fault signature, check whether its
    SHAP sign matches expectation.  Weight each match by |shap_score| so that
    stronger attributions contribute more.  Normalise by the maximum possible
    weighted sum (if all sensors matched perfectly at their actual magnitudes).

    Returns None if no degradation is detected or SHAP data is unavailable.
    """
    if not degradation_type or not shap_data:
        return None

    # Determine which expected-sign map(s) to use
    if "HPC" in degradation_type and "Fan" in degradation_type:
        expected = {**_HPC_EXPECTED_SIGNS, **_FAN_EXPECTED_SIGNS}
    elif "HPC" in degradation_type:
        expected = _HPC_EXPECTED_SIGNS
    elif "Fan" in degradation_type:
        expected = _FAN_EXPECTED_SIGNS
    else:
        return None

    shap_map = {s["sensor"]: s["score"] for s in shap_data}

    weighted_matches = 0.0
    total_weight = 0.0

    for sensor, expected_sign in expected.items():
        score = shap_map.get(sensor, 0.0)
        magnitude = abs(score)
        total_weight += magnitude

        # Sign match check
        if magnitude > 0.01:  # ignore negligible scores
            actual_sign = -1 if score < 0 else 1
            if actual_sign == expected_sign:
                weighted_matches += magnitude

    if total_weight == 0:
        return 0.0

    confidence = weighted_matches / total_weight
    # Clamp to [0, 1]
    return round(min(1.0, max(0.0, confidence)), 3)


# ─────────────────────────────────────────────
#  TOP DRIVERS BAR CHART
# ─────────────────────────────────────────────

def build_top_drivers_chart(shap_data: list[dict] = None, top_n: int | str = "all") -> go.Figure:
    """
    Horizontal bar chart showing feature importance (top drivers).
    top_n: "all", 5, or 10 — how many sensors to show.
    """
    if not shap_data:
        fig = go.Figure()
        fig.add_annotation(
            text="Feature importance will appear once predictions start",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(color="rgba(168,212,255,0.5)", size=12),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=40, t=10, b=10), height=340,
            xaxis=dict(visible=False), yaxis=dict(visible=False),
        )
        return fig

    # Sort by absolute score
    sorted_data = sorted(shap_data, key=lambda x: abs(x["score"]), reverse=True)

    # Apply filter
    if top_n != "all" and str(top_n).isdigit():
        sorted_data = sorted_data[:int(top_n)]

    sensors = [d["sensor"] for d in sorted_data]
    values = [d["score"] for d in sorted_data]

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
        height=340,
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
            tickfont=dict(size=11, color="white"),
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
#  SHAP BEESWARM CHART
# ─────────────────────────────────────────────

def build_shap_beeswarm(shap_data: list[dict], shap_history: list[list[dict]] = None) -> go.Figure:
    """
    Build a SHAP beeswarm plot.

    If shap_history is provided (list of SHAP snapshots across cycles), renders
    a true beeswarm: one dot per cycle per sensor, jittered vertically, colored
    by feature value (blue=low, purple=mid, red/magenta=high).

    If only shap_data (single latest snapshot) is available, falls back to a
    strip plot using just that one point per sensor.
    """
    if not shap_data and not shap_history:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            annotations=[dict(text="No SHAP data available", xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False,
                              font=dict(color="rgba(168,212,255,0.5)", size=14))]
        )
        return fig

    # Determine sensor order by mean |score| (top impact at top of chart)
    sensor_scores_agg = {}
    source = shap_history if shap_history else [shap_data]
    for snapshot in source:
        if not snapshot:
            continue
        for entry in snapshot:
            sensor_scores_agg.setdefault(entry["sensor"], []).append(entry["score"])

    # Sort sensors so highest mean |impact| is at the top (y-axis reversed)
    sensor_order = sorted(
        sensor_scores_agg.keys(),
        key=lambda s: np.mean(np.abs(sensor_scores_agg[s])),
        reverse=True,
    )
    sensor_to_y = {s: i for i, s in enumerate(sensor_order)}

    # Collect all points
    x_vals = []
    y_vals = []
    feature_values = []  # normalized feature values for coloring

    # Compute per-sensor min/max for feature value normalization
    sensor_all_scores = {}
    for snapshot in source:
        if not snapshot:
            continue
        for entry in snapshot:
            sensor_all_scores.setdefault(entry["sensor"], []).append(entry["score"])

    sensor_min = {s: min(vals) for s, vals in sensor_all_scores.items()}
    sensor_max = {s: max(vals) for s, vals in sensor_all_scores.items()}

    for snapshot in source:
        if not snapshot:
            continue
        for entry in snapshot:
            sensor = entry["sensor"]
            score = entry["score"]
            if sensor not in sensor_to_y:
                continue
            x_vals.append(score)
            # Add jitter to y position to spread dots (beeswarm effect)
            jitter = np.random.uniform(-0.25, 0.25)
            y_vals.append(sensor_to_y[sensor] + jitter)
            # Normalize feature value to [0, 1] for color mapping
            s_min = sensor_min.get(sensor, 0)
            s_max = sensor_max.get(sensor, 1)
            if s_max - s_min > 1e-8:
                norm_val = (score - s_min) / (s_max - s_min)
            else:
                norm_val = 0.5
            feature_values.append(norm_val)

    # Color scale: blue (low) → purple (mid) → red/magenta (high)
    beeswarm_colorscale = [
        [0.0, "#0066ff"],
        [0.25, "#6633cc"],
        [0.5, "#9933cc"],
        [0.75, "#cc3399"],
        [1.0, "#ff0066"],
    ]

    fig = go.Figure(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers",
        marker=dict(
            size=6,
            color=feature_values,
            colorscale=beeswarm_colorscale,
            cmin=0,
            cmax=1,
            opacity=0.8,
            line=dict(width=0),
            colorbar=dict(
                title=dict(text="Feature value", font=dict(color="rgba(168,212,255,0.7)", size=10)),
                tickvals=[0, 1],
                ticktext=["Low", "High"],
                tickfont=dict(color="rgba(168,212,255,0.6)", size=9),
                thickness=12, len=0.6,
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
            ),
        ),
        hovertemplate="<b>%{customdata}</b><br>SHAP value: %{x:.4f}<extra></extra>",
        customdata=[sensor_order[int(round(y))] if 0 <= int(round(y)) < len(sensor_order) else ""
                    for y in y_vals],
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=80, r=60, t=35, b=40),
        height=380,
        xaxis=dict(
            title="SHAP value (impact on model output)",
            title_font=dict(color="rgba(168,212,255,0.7)", size=11),
            tickfont=dict(color="rgba(168,212,255,0.6)", size=10),
            gridcolor="rgba(74,158,255,0.08)",
            zeroline=True, zerolinecolor="rgba(74,158,255,0.3)", zerolinewidth=1,
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(len(sensor_order))),
            ticktext=sensor_order,
            tickfont=dict(color="rgba(168,212,255,0.8)", size=11),
            gridcolor="rgba(74,158,255,0.05)",
            range=[len(sensor_order) - 0.5, -0.5],  # top sensor at top
        ),
        title=dict(
            text="SHAP Beeswarm",
            font=dict(color="white", size=13),
            x=0.01, y=0.98,
        ),
    )
    return fig


# ─────────────────────────────────────────────
#  SHAP TREND LINE CHART
# ─────────────────────────────────────────────

def build_shap_trend_chart(cycles: list, shap_history: list[list[dict]], top_n: int = 5) -> go.Figure:
    """
    Line chart showing SHAP values over cycles for the top N contributing sensors.
    shap_history: list of shap_data per cycle (same order as cycles list).
    """
    if not shap_history or not cycles:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            annotations=[dict(text="Insufficient data for SHAP trend", xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False,
                              font=dict(color="rgba(168,212,255,0.5)", size=14))]
        )
        return fig

    # Identify top N sensors by average |score| across history
    sensor_scores = {}
    for snapshot in shap_history:
        if not snapshot:
            continue
        for entry in snapshot:
            name = entry["sensor"]
            sensor_scores.setdefault(name, []).append(abs(entry["score"]))

    avg_scores = {s: np.mean(vals) for s, vals in sensor_scores.items()}
    top_sensors = sorted(avg_scores.keys(), key=lambda s: avg_scores[s], reverse=True)[:top_n]

    # Build time-series per sensor
    color_palette = ["#4a9eff", "#ff4d4d", "#ffd93d", "#00c875", "#7b61ff",
                     "#ff9f43", "#a8d4ff", "#ff6b6b", "#54e0c7", "#c084fc"]

    fig = go.Figure()
    for idx, sensor in enumerate(top_sensors):
        y_values = []
        for snapshot in shap_history:
            val = 0.0
            if snapshot:
                for entry in snapshot:
                    if entry["sensor"] == sensor:
                        val = entry["score"]
                        break
            y_values.append(val)

        fig.add_trace(go.Scatter(
            x=cycles, y=y_values,
            mode="lines+markers",
            name=sensor,
            line=dict(color=color_palette[idx % len(color_palette)], width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>{sensor}</b><br>Cycle: %{{x}}<br>Score: %{{y:.4f}}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=20, t=40, b=50),
        height=320,
        legend=dict(
            font=dict(color="rgba(168,212,255,0.8)", size=11),
            bgcolor="rgba(0,0,0,0)",
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        ),
        xaxis=dict(
            title="Cycle",
            title_font=dict(color="rgba(168,212,255,0.7)", size=11),
            tickfont=dict(color="rgba(168,212,255,0.6)", size=10),
            gridcolor="rgba(74,158,255,0.1)",
        ),
        yaxis=dict(
            title="SHAP Attribution Score",
            title_font=dict(color="rgba(168,212,255,0.7)", size=11),
            tickfont=dict(color="rgba(168,212,255,0.6)", size=10),
            gridcolor="rgba(74,158,255,0.1)",
            zeroline=True, zerolinecolor="rgba(74,158,255,0.2)", zerolinewidth=1,
        ),
        title=dict(
            text="SHAP Value Trend Over Cycles (Top Sensors)",
            font=dict(color="white", size=13),
            x=0.01, y=0.98,
        ),
    )
    return fig


# ─────────────────────────────────────────────
#  LLM EXPLANATION (Gemini Flash)
# ─────────────────────────────────────────────

def _build_llm_prompt(degradation_type: str, confidence: float,
                      top_features: list[dict], sensor_trends: dict | None = None) -> str:
    """
    Construct a tightly-scoped prompt for Gemini Flash.
    Includes domain knowledge so the LLM can explain *why* sensor patterns
    indicate specific degradation, rather than just restating the inputs.
    """
    # Sensor domain knowledge for contextual explanation
    sensor_context = {
        "T24": "LPC outlet temperature — rises indicate compressor inefficiency",
        "T30": "HPC outlet temperature — elevated values suggest compressor degradation or fouling",
        "T50": "LPT outlet temperature — changes reflect turbine blade wear or thermal fatigue",
        "P30": "HPC outlet pressure — drop indicates compressor blade erosion or tip clearance increase",
        "Nf": "Fan speed — reduction suggests fan blade damage or increased aerodynamic drag",
        "Nc": "Core speed — decline indicates HPC performance loss, possible blade erosion",
        "Ps30": "HPC static pressure — deviation signals compressor stall margin reduction",
        "phi": "Fuel-flow-to-Ps30 ratio — increase means the engine burns more fuel for same output (efficiency loss)",
        "NRf": "Corrected fan speed — normalizes for ambient conditions; drop = true fan degradation",
        "NRc": "Corrected core speed — normalizes for conditions; decline = true HPC degradation",
        "BPR": "Bypass ratio — shift indicates fan vs core thrust balance changing",
        "htBleed": "Bleed enthalpy — changes reflect thermal state of compressor bleed air",
        "W31": "HPT coolant bleed flow — increase may indicate turbine thermal protection response",
        "W32": "LPT coolant bleed flow — increase suggests downstream thermal stress",
    }

    features_detail = []
    for f in top_features[:5]:
        name = f["sensor"]
        score = f["score"]
        direction = "reducing RUL" if score < 0 else "slightly increasing RUL"
        context = sensor_context.get(name, "sensor function unknown")
        features_detail.append(f"  • {name} (score: {score:+.3f}, {direction}): {context}")

    features_str = "\n".join(features_detail)

    trend_str = ""
    if sensor_trends:
        trend_str = "\nSENSOR SLOPE DATA (recent rolling trend):\n" + "\n".join(
            f"  • {s}: slope = {v:+.5f} per cycle" for s, v in sensor_trends.items()
        )

    prompt = (
        f"You are an aircraft engine prognostics expert writing a degradation briefing "
        f"for a maintenance engineer. Based on the analysis below, explain:\n"
        f"1. What physical degradation mechanism the sensor pattern suggests\n"
        f"2. Why these specific sensors are the strongest indicators\n"
        f"3. What the engineer should inspect or monitor next\n\n"
        f"ANALYSIS RESULTS:\n"
        f"- Detected fault mode: {degradation_type}\n"
        f"- Confidence score: {confidence:.1%}\n"
        f"- Top contributing sensors (SHAP attribution — negative = drives predicted RUL down):\n"
        f"{features_str}\n"
        f"{trend_str}\n\n"
        f"RULES:\n"
        f"- You MUST mention the fault mode '{degradation_type}' and confidence '{confidence:.1%}' verbatim.\n"
        f"- Explain the physical meaning: what is likely happening inside the engine.\n"
        f"- Be specific to the sensors listed — don't give generic advice.\n"
        f"- Suggest 1-2 concrete inspection actions relevant to the fault mode.\n"
        f"- Keep it to 4-6 sentences. Professional tone, no hedging.\n"
    )
    return prompt


def _validate_llm_output(text: str, degradation_type: str, confidence: float) -> bool:
    """
    Lightweight validation: confirm that the LLM output contains the
    fault-mode label and confidence value that were passed in.
    """
    if not text:
        return False
    # Check fault mode label present (case-insensitive)
    if degradation_type.lower() not in text.lower():
        return False
    # Check confidence value appears (allow ±1% formatting variance)
    conf_pct = f"{confidence * 100:.0f}%"
    conf_pct_1 = f"{confidence * 100:.1f}%"
    conf_decimal = f"{confidence:.2f}"
    if (conf_pct not in text and conf_pct_1 not in text
            and conf_decimal not in text and f"{confidence:.1%}" not in text):
        return False
    return True


def _fallback_explanation(degradation_type: str, confidence: float,
                          top_features: list[dict]) -> str:
    """Templated fallback when LLM output fails validation or API is unavailable."""
    sensor_meanings = {
        "T24": "LPC outlet temperature (compressor inefficiency)",
        "T30": "HPC outlet temperature (compressor fouling/degradation)",
        "T50": "LPT outlet temperature (turbine wear)",
        "P30": "HPC outlet pressure (blade erosion)",
        "Nf": "Fan speed (fan blade damage)",
        "Nc": "Core speed (HPC performance loss)",
        "Ps30": "HPC static pressure (stall margin reduction)",
        "phi": "Fuel efficiency ratio (efficiency loss)",
        "NRf": "Corrected fan speed (fan degradation)",
        "NRc": "Corrected core speed (HPC degradation)",
        "BPR": "Bypass ratio (thrust balance shift)",
        "htBleed": "Bleed enthalpy (compressor thermal state)",
        "W31": "HPT coolant bleed (turbine thermal stress)",
        "W32": "LPT coolant bleed (downstream thermal stress)",
    }

    top3 = top_features[:3]
    details = []
    for f in top3:
        meaning = sensor_meanings.get(f["sensor"], f["sensor"])
        direction = "declining" if f["score"] < 0 else "elevated"
        details.append(f"{f['sensor']} — {meaning}, {direction}")

    details_str = "; ".join(details)

    if "HPC" in degradation_type:
        mechanism = (
            "This pattern is consistent with high-pressure compressor blade erosion "
            "or fouling, leading to reduced compression efficiency and increased fuel consumption. "
            "Recommend borescope inspection of HPC stages and review of compressor wash history."
        )
    elif "Fan" in degradation_type:
        mechanism = (
            "This pattern suggests fan blade surface degradation or foreign object damage "
            "reducing aerodynamic efficiency. "
            "Recommend fan blade visual inspection and vibration signature analysis."
        )
    else:
        mechanism = (
            "Multiple degradation pathways are active simultaneously. "
            "Recommend comprehensive inspection of both HPC and fan sections."
        )

    return (
        f"Detected fault mode: {degradation_type} (confidence: {confidence:.1%}). "
        f"Key indicators: {details_str}. {mechanism}"
    )


def generate_llm_explanation(degradation_type: str, confidence: float,
                             top_features: list[dict],
                             sensor_trends: dict | None = None) -> str:
    """
    Call Gemini Flash API to generate natural language explanation.
    Falls back to a templated string if the API is unavailable or validation fails.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return _fallback_explanation(degradation_type, confidence, top_features)

    prompt = _build_llm_prompt(degradation_type, confidence, top_features, sensor_trends)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=300,
            ),
        )
        text = response.text.strip() if response.text else ""

        # Post-generation validation
        if _validate_llm_output(text, degradation_type, confidence):
            return text
        else:
            print(f"[DEGRAD] LLM output failed validation, using fallback.")
            return _fallback_explanation(degradation_type, confidence, top_features)

    except ImportError:
        print("[DEGRAD] google-generativeai package not installed. Using fallback.")
        return _fallback_explanation(degradation_type, confidence, top_features)
    except Exception as e:
        print(f"[DEGRAD] Gemini API error: {e}")
        return _fallback_explanation(degradation_type, confidence, top_features)


# ─────────────────────────────────────────────
#  PAGE LAYOUT
# ─────────────────────────────────────────────

def create_degradation_analysis_layout(supabase=None, engine_db_id=None):
    """Build the full Degradation Analysis page layout."""

    # ── Fetch engine metadata ──
    engine_label = "No engine selected"
    degradation_type = None
    model_type = None
    cached_explanation = None
    cached_explanation_ts = None

    if supabase and engine_db_id:
        try:
            resp = supabase.table("engines") \
                .select("engine_id, degradation_type, model_type, llm_explanation, llm_explanation_updated_at") \
                .eq("id", engine_db_id) \
                .single() \
                .execute()
            if resp.data:
                engine_label = f"Engine #{resp.data.get('engine_id', engine_db_id)}"
                degradation_type = resp.data.get("degradation_type")
                model_type = resp.data.get("model_type", "")
                cached_explanation = resp.data.get("llm_explanation")
                cached_explanation_ts = resp.data.get("llm_explanation_updated_at")
        except Exception:
            pass

    # ── Display values ──
    deg_type_display = degradation_type or "No degradation detected"
    deg_color = "#ff4d4d" if degradation_type else "rgba(168,212,255,0.5)"

    # ── Header section (simplified - just page title + engine label) ──
    header = html.Div(
        style={
            "display": "flex", "alignItems": "center",
            "padding": "20px 28px 0px 28px", "gap": "12px",
        },
        children=[
            icon_shap(),
            html.Div(children=[
                html.Div("DEGRADATION ANALYSIS", style={
                    "color": "rgba(168,212,255,0.5)", "fontSize": "10px",
                    "fontWeight": "700", "letterSpacing": "1.2px", "marginBottom": "2px",
                }),
                html.Span(engine_label, style={
                    "color": "white", "fontSize": "18px", "fontWeight": "700",
                }),
            ]),
        ]
    )

    # ── Row 1: Status Overview Card | 3D Engine Model | SHAP Beeswarm ──
    row1 = html.Div(
        style={"display": "flex", "gap": "20px", "padding": "20px 28px", "flexWrap": "nowrap"},
        children=[
            # Column 1: Status Overview card (flex: 1)
            html.Div(
                style={
                    "flex": "1", "minWidth": "0",
                    "background": "rgba(13,32,69,0.6)",
                    "border": "1px solid rgba(74,158,255,0.15)",
                    "borderRadius": "12px", "padding": "20px",
                    "display": "flex", "flexDirection": "column", "gap": "16px",
                },
                children=[
                    # Section 1: Status Overview + Fault Mode
                    html.Div(children=[
                        html.Div("STATUS OVERVIEW", style={
                            "color": "rgba(168,212,255,0.5)", "fontSize": "10px",
                            "fontWeight": "700", "letterSpacing": "1.2px", "marginBottom": "4px",
                        }),
                        html.Div("DETECTED FAULT MODE", style={
                            "color": "rgba(168,212,255,0.6)", "fontSize": "10px",
                            "fontWeight": "600", "marginBottom": "10px",
                        }),
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "gap": "10px"},
                            children=[
                                html.Span(
                                    id="da-fault-mode-label",
                                    children=deg_type_display.upper(),
                                    style={
                                        "color": "white", "fontSize": "16px", "fontWeight": "800",
                                    }
                                ),
                                # Red indicator dot
                                html.Div(style={
                                    "width": "10px", "height": "10px", "borderRadius": "50%",
                                    "background": "#ff4d4d" if degradation_type else "rgba(168,212,255,0.3)",
                                    "boxShadow": "0 0 8px rgba(255,77,77,0.6)" if degradation_type else "none",
                                }),
                            ]
                        ),
                    ]),

                    # Divider
                    html.Div(style={"height": "1px", "background": "rgba(74,158,255,0.12)"}),

                    # Section 2: Confidence + donut ring (space-between)
                    html.Div(children=[
                        html.Div(
                            style={"display": "flex", "alignItems": "center",
                                   "justifyContent": "space-between"},
                            children=[
                                html.Div(children=[
                                    html.Div("CONFIDENCE", style={
                                        "color": "rgba(168,212,255,0.5)", "fontSize": "10px",
                                        "fontWeight": "700", "letterSpacing": "1.2px", "marginBottom": "10px",
                                    }),
                                    html.Span("—", id="da-confidence-value", style={
                                        "color": "white", "fontSize": "36px", "fontWeight": "800",
                                    }),
                                ]),
                                # SVG donut ring for confidence
                                html.Div(
                                    id="da-confidence-ring",
                                    style={"width": "100px", "height": "100px"},
                                ),
                            ]
                        ),
                    ]),

                    # Divider
                    html.Div(style={"height": "1px", "background": "rgba(74,158,255,0.12)"}),

                    # Section 3: Time to EOL (predicted RUL) + mini chart
                    html.Div(children=[
                        html.Div("TIME TO EOL (CYCLES)", style={
                            "color": "rgba(168,212,255,0.5)", "fontSize": "10px",
                            "fontWeight": "700", "letterSpacing": "1.2px", "marginBottom": "10px",
                        }),
                        html.Div(
                            style={"display": "flex", "alignItems": "center",
                                   "justifyContent": "space-between"},
                            children=[
                                html.Span("—", id="da-rul-value", style={
                                    "color": "white", "fontSize": "36px", "fontWeight": "800",
                                }),
                                # Mini RUL sparkline chart
                                dcc.Graph(
                                    id="da-rul-sparkline",
                                    config={"displayModeBar": False, "staticPlot": True},
                                    style={"width": "50%", "height": "50px", "minWidth": "0"},
                                ),
                            ]
                        ),
                    ]),
                ]
            ),
            # Column 2: Top Drivers chart (flex: 2)
            html.Div(
                style={
                    "flex": "2", "minWidth": "0",
                    "background": "rgba(13,32,69,0.5)",
                    "border": "1px solid rgba(74,158,255,0.15)",
                    "borderRadius": "12px", "padding": "16px",
                    "display": "flex", "flexDirection": "column",
                },
                children=[
                    # Header with title + filter selector (space-between)
                    html.Div(
                        style={"display": "flex", "alignItems": "center",
                               "justifyContent": "space-between", "marginBottom": "12px"},
                        children=[
                            html.Div("Top Drivers", style={
                                "color": "white", "fontSize": "14px", "fontWeight": "700",
                            }),
                            html.Div(
                                style={"display": "flex", "gap": "6px"},
                                children=[
                                    html.Div("All", id="da-filter-all", n_clicks=0, style={
                                        "padding": "4px 12px", "borderRadius": "6px",
                                        "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                                        "background": "rgba(74,158,255,0.25)", "color": "white",
                                        "border": "1px solid rgba(74,158,255,0.5)",
                                    }),
                                    html.Div("Top 5", id="da-filter-5", n_clicks=0, style={
                                        "padding": "4px 12px", "borderRadius": "6px",
                                        "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                                        "background": "transparent", "color": "rgba(168,212,255,0.6)",
                                        "border": "1px solid rgba(74,158,255,0.25)",
                                    }),
                                    html.Div("Top 10", id="da-filter-10", n_clicks=0, style={
                                        "padding": "4px 12px", "borderRadius": "6px",
                                        "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
                                        "background": "transparent", "color": "rgba(168,212,255,0.6)",
                                        "border": "1px solid rgba(74,158,255,0.25)",
                                    }),
                                ]
                            ),
                        ]
                    ),
                    dcc.Store(id="da-top-drivers-filter", data="all"),
                    # Top drivers bar chart
                    dcc.Graph(
                        id="da-top-drivers-chart",
                        config={"displayModeBar": False},
                        style={"flex": "1", "minHeight": "0"},
                    ),
                ]
            ),
            # Column 3: SHAP beeswarm chart (flex: 2)
            html.Div(
                style={
                    "flex": "2", "minWidth": "0",
                    "background": "rgba(13,32,69,0.5)",
                    "border": "1px solid rgba(74,158,255,0.15)",
                    "borderRadius": "12px", "padding": "16px",
                },
                children=[
                    dcc.Graph(id="da-shap-beeswarm", config={"displayModeBar": False},
                              figure=build_shap_beeswarm([])),
                ]
            ),
        ]
    )

    # ── Row 2: SHAP trend chart (5:1 ratio) + AI explanation ──
    row2 = html.Div(
        style={"display": "flex", "gap": "20px", "padding": "0 28px 28px"},
        children=[
            # SHAP trend chart (flex: 5)
            html.Div(
                style={
                    "flex": "5", "minWidth": "0",
                    "background": "rgba(13,32,69,0.5)",
                    "border": "1px solid rgba(74,158,255,0.15)",
                    "borderRadius": "12px", "padding": "16px",
                },
                children=[
                    dcc.Graph(id="da-shap-trend", config={"displayModeBar": False},
                              figure=build_shap_trend_chart([], [])),
                ]
            ),
            # AI Explanation (flex: 1)
            html.Div(
                style={
                    "flex": "1", "minWidth": "200px",
                    "background": "rgba(13,32,69,0.5)",
                    "border": "1px solid rgba(74,158,255,0.15)",
                    "borderRadius": "12px", "padding": "20px",
                    "display": "flex", "flexDirection": "column",
                },
                children=[
                    html.Div(style={"display": "flex", "flexDirection": "column", "gap": "8px",
                                    "marginBottom": "14px"}, children=[
                        html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=[
                            html.Div("AI EXPLANATION", style={
                                "color": "rgba(168,212,255,0.7)", "fontSize": "11px",
                                "fontWeight": "700", "letterSpacing": "1px",
                            }),
                            html.Span("Gemini Flash", style={
                                "color": "rgba(74,158,255,0.6)", "fontSize": "10px",
                                "background": "rgba(74,158,255,0.1)",
                                "borderRadius": "4px", "padding": "2px 6px",
                            }),
                        ]),
                        html.Button(
                            "Generate",
                            id="da-generate-btn",
                            n_clicks=0,
                            style={
                                "background": "linear-gradient(135deg, #4a9eff, #7b61ff)",
                                "border": "none", "color": "white", "fontSize": "11px",
                                "fontWeight": "700", "padding": "6px 14px",
                                "borderRadius": "6px", "cursor": "pointer",
                                "letterSpacing": "0.5px", "width": "fit-content",
                            },
                        ),
                    ]),
                    html.Div(
                        id="da-llm-explanation",
                        style={
                            "color": "rgba(168,212,255,0.8)", "fontSize": "12px",
                            "lineHeight": "1.7", "flex": "1", "overflowY": "auto",
                        },
                        children=[
                            html.Div(cached_explanation, style={"marginBottom": "8px"})
                            if cached_explanation else
                            html.Div("Click 'Generate' to request an AI-powered analysis."),
                            html.Div(
                                f"Last generated: {cached_explanation_ts[:16].replace('T', ' ')}"
                                if cached_explanation_ts else "",
                                style={"color": "rgba(168,212,255,0.4)", "fontSize": "10px",
                                       "marginTop": "8px"},
                            ) if cached_explanation else None,
                        ]
                    ),
                ]
            ),
        ]
    )

    # ── Stores ──
    stores = html.Div([
        dcc.Store(id="da-engine-db-id", data=engine_db_id),
        dcc.Store(id="da-degradation-type", data=degradation_type),
        dcc.Store(id="da-model-type", data=model_type),
        dcc.Interval(id="da-interval", interval=5_000, n_intervals=0),  # poll every 5s (same as overview)
    ])

    # ── Assemble full page ──
    return html.Div(
        style={"height": "100vh", "background": "#0a1628", "display": "flex",
               "flexDirection": "column", "overflow": "hidden"},
        children=[
            build_topbar(),
            html.Div(style={"flex": "1", "display": "flex", "flexDirection": "row",
                            "overflow": "hidden", "minHeight": "0"}, children=[
                build_sidebar(active_page="degradation_analysis", engine_db_id=engine_db_id),
                html.Div(style={"flex": "1", "overflowY": "auto", "display": "flex",
                                "flexDirection": "column", "minWidth": "0"}, children=[
                    header,
                    row1,
                    row2,
                    stores,
                ]),
            ]),
        ]
    )


# ─────────────────────────────────────────────
#  CALLBACKS
# ─────────────────────────────────────────────

def register_degradation_analysis_callbacks(app, supabase=None):
    """Register all callbacks for the Degradation Analysis page."""

    def _build_confidence_ring(confidence_pct: int):
        """Build an SVG donut ring showing confidence percentage."""
        # SVG circle math: circumference = 2*pi*r, r=25, C≈157
        radius = 25
        circumference = 2 * 3.14159 * radius
        filled = (confidence_pct / 100) * circumference
        gap = circumference - filled

        # Gradient from blue to magenta/pink
        svg_str = f'''
        <svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="ring-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#4a9eff"/>
              <stop offset="50%" stop-color="#9933cc"/>
              <stop offset="100%" stop-color="#ff0066"/>
            </linearGradient>
          </defs>
          <circle cx="30" cy="30" r="{radius}" fill="none" stroke="rgba(74,158,255,0.15)" stroke-width="5"/>
          <circle cx="30" cy="30" r="{radius}" fill="none" stroke="url(#ring-grad)" stroke-width="5"
                  stroke-dasharray="{filled:.1f} {gap:.1f}" stroke-linecap="round"
                  transform="rotate(-90 30 30)"/>
          <text x="30" y="34" text-anchor="middle" fill="white" font-size="11" font-weight="700">{confidence_pct}%</text>
        </svg>'''
        b64 = base64.b64encode(svg_str.strip().encode("utf-8")).decode("utf-8")
        return html.Img(
            src=f"data:image/svg+xml;base64,{b64}",
            style={"width": "100px", "height": "100px"},
        )

    def _build_rul_sparkline(predicted_ruls: list):
        """Build a tiny sparkline chart for predicted RUL."""
        fig = go.Figure()
        if predicted_ruls:
            x = list(range(len(predicted_ruls)))
            fig.add_trace(go.Scatter(
                x=x, y=predicted_ruls,
                mode="lines",
                line=dict(color="#9933cc", width=2),
                fill="none",
                showlegend=False,
            ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=50,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            hovermode=False,
        )
        return fig

    @app.callback(
        Output("da-shap-beeswarm", "figure"),
        Output("da-shap-trend", "figure"),
        Output("da-confidence-value", "children"),
        Output("da-confidence-ring", "children"),
        Output("da-rul-value", "children"),
        Output("da-rul-sparkline", "figure"),
        Output("da-fault-mode-label", "children"),
        Output("da-top-drivers-chart", "figure"),
        Output("da-interval", "disabled"),
        Input("da-interval", "n_intervals"),
        State("da-engine-db-id", "data"),
        State("da-degradation-type", "data"),
        State("da-model-type", "data"),
        State("da-top-drivers-filter", "data"),
        prevent_initial_call=False,
    )
    def update_charts(n_intervals, engine_db_id, degradation_type, model_type, top_n_filter):
        """
        Poll callback: fetch SHAP history, compute confidence, update charts.
        Disables the interval once the prediction cycle is complete.
        Does NOT call the LLM — that is triggered only by button click.
        """
        from engine_simulation_manager import is_running as _sim_is_running

        empty_sparkline = _build_rul_sparkline([])

        if not supabase or not engine_db_id:
            return (
                build_shap_beeswarm([]),
                build_shap_trend_chart([], []),
                "—",
                _build_confidence_ring(0),
                "—",
                empty_sparkline,
                "NO DEGRADATION DETECTED",
                build_top_drivers_chart(None),
                False,
            )

        # ── Check if simulation is still running ──
        sim_active = _sim_is_running(engine_db_id)

        # ── Fetch prediction + SHAP history ──
        cycles_list = []
        shap_history = []
        latest_shap = []
        predicted_ruls = []

        try:
            resp = supabase.table("rul_predictions") \
                .select("cycle, predicted_rul, shap_values") \
                .eq("engine_id", engine_db_id) \
                .order("cycle", desc=False) \
                .execute()

            for row in (resp.data or []):
                cycle = row.get("cycle")
                raw_shap = row.get("shap_values")
                parsed_shap = []
                if raw_shap:
                    try:
                        parsed_shap = _json.loads(raw_shap) if isinstance(raw_shap, str) else raw_shap
                    except Exception:
                        parsed_shap = []
                cycles_list.append(cycle)
                shap_history.append(parsed_shap)
                pred_rul = row.get("predicted_rul")
                predicted_ruls.append(float(pred_rul) if pred_rul is not None else None)

            # Latest valid SHAP snapshot
            for snapshot in reversed(shap_history):
                if snapshot:
                    latest_shap = snapshot
                    break

        except Exception as e:
            print(f"[DEGRAD] Error fetching SHAP data: {e}")
            return (
                build_shap_beeswarm([]),
                build_shap_trend_chart([], []),
                "—",
                _build_confidence_ring(0),
                "—",
                empty_sparkline,
                "NO DEGRADATION DETECTED",
                build_top_drivers_chart(None),
                not sim_active,
            )

        # ── Re-fetch degradation_type (may have updated since page load) ──
        if supabase and engine_db_id:
            try:
                eng_resp = supabase.table("engines") \
                    .select("degradation_type") \
                    .eq("id", engine_db_id) \
                    .single() \
                    .execute()
                if eng_resp.data:
                    degradation_type = eng_resp.data.get("degradation_type") or degradation_type
            except Exception:
                pass

        # ── Compute confidence ──
        confidence = compute_confidence_score(degradation_type, latest_shap)
        confidence_pct = int(round(confidence * 100)) if confidence is not None else 0
        confidence_display = f"{confidence_pct}%"

        # ── Latest RUL value ──
        latest_rul = None
        for v in reversed(predicted_ruls):
            if v is not None:
                latest_rul = v
                break
        rul_display = str(int(round(latest_rul))) if latest_rul is not None else "—"

        # ── Fault mode label ──
        fault_label = degradation_type.upper() if degradation_type else "NO DEGRADATION DETECTED"

        # ── Build charts ──
        beeswarm_fig = build_shap_beeswarm(latest_shap, shap_history=shap_history)
        trend_fig = build_shap_trend_chart(cycles_list, shap_history, top_n=5)
        sparkline_fig = _build_rul_sparkline([v for v in predicted_ruls if v is not None])
        top_drivers_fig = build_top_drivers_chart(latest_shap, top_n=top_n_filter or "all")

        return (
            beeswarm_fig,
            trend_fig,
            confidence_display,
            _build_confidence_ring(confidence_pct),
            rul_display,
            sparkline_fig,
            fault_label,
            top_drivers_fig,
            not sim_active,
        )

    @app.callback(
        Output("da-llm-explanation", "children"),
        Input("da-generate-btn", "n_clicks"),
        State("da-engine-db-id", "data"),
        State("da-degradation-type", "data"),
        prevent_initial_call=True,
    )
    def generate_explanation_on_click(n_clicks, engine_db_id, degradation_type):
        """
        Triggered ONLY by the 'Generate Explanation' button click.
        Calls Gemini Flash API once per click, then caches the result
        in engines.llm_explanation to avoid repeat API calls.
        """
        if not n_clicks or not supabase or not engine_db_id:
            raise dash.exceptions.PreventUpdate

        # Fetch latest SHAP + degradation type
        latest_shap = []
        try:
            resp = supabase.table("rul_predictions") \
                .select("shap_values") \
                .eq("engine_id", engine_db_id) \
                .order("cycle", desc=True) \
                .limit(1) \
                .execute()
            if resp.data:
                raw_shap = resp.data[0].get("shap_values")
                if raw_shap:
                    latest_shap = _json.loads(raw_shap) if isinstance(raw_shap, str) else raw_shap
        except Exception as e:
            return f"Error fetching SHAP data: {e}"

        # Re-fetch degradation_type
        try:
            eng_resp = supabase.table("engines") \
                .select("degradation_type") \
                .eq("id", engine_db_id) \
                .single() \
                .execute()
            if eng_resp.data:
                degradation_type = eng_resp.data.get("degradation_type") or degradation_type
        except Exception:
            pass

        if not degradation_type:
            return (
                "No degradation pattern has been detected for this engine. "
                "The engine is operating within normal parameters."
            )

        if not latest_shap:
            return "Insufficient SHAP data to generate analysis. Awaiting more prediction cycles."

        confidence = compute_confidence_score(degradation_type, latest_shap)
        if confidence is None:
            confidence = 0.0

        explanation = generate_llm_explanation(
            degradation_type=degradation_type,
            confidence=confidence,
            top_features=latest_shap[:5],
            sensor_trends=None,  # TODO: compute rolling slopes from sensor data
        )

        # ── Cache to engines table ──
        try:
            supabase.table("engines") \
                .update({
                    "llm_explanation": explanation,
                    "llm_explanation_updated_at": datetime.utcnow().isoformat(),
                }) \
                .eq("id", engine_db_id) \
                .execute()
        except Exception as e:
            print(f"[DEGRAD] Failed to cache LLM explanation: {e}")

        return explanation

    # ── Top drivers filter callback (instant response on button click) ──
    @app.callback(
        Output("da-top-drivers-chart", "figure", allow_duplicate=True),
        Output("da-top-drivers-filter", "data"),
        Output("da-filter-all", "style"),
        Output("da-filter-5", "style"),
        Output("da-filter-10", "style"),
        Input("da-filter-all", "n_clicks"),
        Input("da-filter-5", "n_clicks"),
        Input("da-filter-10", "n_clicks"),
        State("da-engine-db-id", "data"),
        prevent_initial_call=True,
    )
    def update_top_drivers_filter(n_all, n_5, n_10, engine_db_id):
        """Re-render top drivers chart when filter button is clicked."""
        from dash import callback_context as _ctx

        active_style = {
            "padding": "4px 12px", "borderRadius": "6px",
            "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
            "background": "rgba(74,158,255,0.25)", "color": "white",
            "border": "1px solid rgba(74,158,255,0.5)",
        }
        inactive_style = {
            "padding": "4px 12px", "borderRadius": "6px",
            "fontSize": "11px", "fontWeight": "700", "cursor": "pointer",
            "background": "transparent", "color": "rgba(168,212,255,0.6)",
            "border": "1px solid rgba(74,158,255,0.25)",
        }

        triggered = _ctx.triggered[0]["prop_id"].split(".")[0] if _ctx.triggered else "da-filter-all"
        if triggered == "da-filter-5":
            top_n = "5"
            styles = (inactive_style, active_style, inactive_style)
        elif triggered == "da-filter-10":
            top_n = "10"
            styles = (inactive_style, inactive_style, active_style)
        else:
            top_n = "all"
            styles = (active_style, inactive_style, inactive_style)

        if not supabase or not engine_db_id:
            return build_top_drivers_chart(None), top_n, *styles

        try:
            resp = supabase.table("rul_predictions") \
                .select("shap_values") \
                .eq("engine_id", engine_db_id) \
                .order("cycle", desc=True) \
                .limit(1) \
                .execute()
            if resp.data:
                raw_shap = resp.data[0].get("shap_values")
                if raw_shap:
                    latest_shap = _json.loads(raw_shap) if isinstance(raw_shap, str) else raw_shap
                    return build_top_drivers_chart(latest_shap, top_n=top_n), top_n, *styles
        except Exception:
            pass

        return build_top_drivers_chart(None), top_n, *styles

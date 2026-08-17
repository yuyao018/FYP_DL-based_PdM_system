"""
Degradation Analysis page — SHAP beeswarm, LLM explanation, SHAP trend over cycles.

Replaces the former "Explainability AI" page.  Provides:
  • Header: engine selector, detected degradation pattern, pattern similarity score
  • Row 1 col 1: SHAP beeswarm-style horizontal bar chart (feature impact on RUL)
  • Row 1 col 2: LLM-generated natural language explanation (Groq Llama)
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
from pathlib import Path
from assets.components import (build_sidebar, build_topbar, icon_shap)

# ─────────────────────────────────────────────
#  PATTERN SIMILARITY SCORE (cosine-based)
# ─────────────────────────────────────────────
#
# The simulation loop now stores both the pattern label ("HPC Degradation",
# "HPC + Fan Degradation", "Pattern Ambiguous", "Insufficient Signal") and
# the cosine similarity score (pattern_similarity) in the engines table.
#
# compute_pattern_similarity() prefers the stored value that was computed at
# inference time.  It recomputes from SHAP data only when the stored value is
# absent (e.g. for predictions made before the pipeline upgrade).
#
# Terminology note:
#   "pattern_similarity" / "similarity score" is used throughout instead of
#   "confidence" or "fault detection confidence" because this method identifies
#   similarity to a known degradation profile — it does not confirm a fault.

# Sensor ordering must match _PATTERN_SENSORS in engine_simulation_manager.py
_PATTERN_SENSORS = [
    "T24", "T30", "T50", "P30", "Nf",  "Nc",
    "Ps30", "phi", "NRf", "NRc", "BPR", "htBleed", "W31", "W32",
]

# Reference signatures are shared via the same JSON file used by the sim loop.
# Load them once here for the fallback recompute path.
_DA_SIGNATURES:  dict = {}
_DA_REF_VECS:    dict = {}

def _load_da_signatures() -> None:
    """
    Load reference signatures into module-level caches for this page.

    Resolution order:
      1. Local  data/shap_signatures.json
      2. Supabase Storage bucket "SHAP"
    """
    global _DA_SIGNATURES, _DA_REF_VECS
    sig_path = Path(os.path.join(os.path.dirname(__file__), "data", "shap_signatures.json"))

    if not sig_path.exists():
        try:
            from storage_utils import _get_supabase_admin
            sb = _get_supabase_admin()
            if sb:
                data = sb.storage.from_("SHAP").download("shap_signatures.json")
                sig_path.parent.mkdir(parents=True, exist_ok=True)
                sig_path.write_bytes(data)
                print(f"[DEGRAD] Downloaded shap_signatures.json from Storage → {sig_path}")
        except Exception as e:
            print(f"[DEGRAD] Could not download shap_signatures.json: {e}")

    if not sig_path.exists():
        return

    try:
        with open(sig_path, encoding="utf-8") as f:
            _DA_SIGNATURES = _json.load(f)
        for name, sig in _DA_SIGNATURES.items():
            mean_map = sig.get("mean_abs_shap", {})
            vec = np.array([mean_map.get(s, 0.0) for s in _PATTERN_SENSORS], dtype=np.float64)
            norm = np.linalg.norm(vec)
            _DA_REF_VECS[name] = vec / (norm + 1e-9)
    except Exception as e:
        print(f"[DEGRAD] Could not load shap_signatures.json: {e}")

_load_da_signatures()


def compute_pattern_similarity(
    pattern_label: str | None,
    shap_data: list[dict],
    stored_similarity: float | None = None,
    model_type: str | None = None,
) -> float | None:
    """
    Return the pattern similarity score (cosine similarity, 0–1) for the
    current degradation pattern label.

    Prefers *stored_similarity* written by the simulation loop at inference time.
    Falls back to recomputing cosine similarity from shap_data when the stored
    value is absent (e.g. legacy predictions before the pipeline upgrade).

    Returns None if the pattern label indicates no actionable pattern
    ("Insufficient Signal", None) or if SHAP data is unavailable.
    """
    # No pattern — nothing to score
    if not pattern_label or pattern_label == "Insufficient Signal":
        return None

    # Prefer the value already computed at inference time
    if stored_similarity is not None:
        return round(float(stored_similarity), 4)

    # Fallback: recompute from SHAP data
    if not shap_data or not _DA_REF_VECS:
        return None

    shap_map = {d["sensor"]: abs(d["score"]) for d in shap_data}
    current_vec = np.array(
        [shap_map.get(s, 0.0) for s in _PATTERN_SENSORS], dtype=np.float64
    )
    norm = np.linalg.norm(current_vec)
    if norm < 1e-9:
        return 0.0
    current_vec_norm = current_vec / norm

    # Select candidate group based on model_type (or pattern label as fallback)
    if model_type in ("FD001", "FD003"):
        candidates = [k for k in _DA_REF_VECS if k in ("FD001", "FD003")]
    elif model_type in ("FD002", "FD004"):
        candidates = [k for k in _DA_REF_VECS if k in ("FD002", "FD004")]
    else:
        candidates = list(_DA_REF_VECS.keys())

    if not candidates:
        return None

    best_score = max(
        float(np.dot(current_vec_norm, _DA_REF_VECS[name]))
        for name in candidates
    )
    return round(min(best_score, 1.0), 4)


# Keep backward-compatible alias so any external caller using the old name
# does not break immediately.
def compute_confidence_score(
    degradation_type: str | None,
    shap_data: list[dict],
    stored_similarity: float | None = None,
    model_type: str | None = None,
) -> float | None:
    """Backward-compatible alias for compute_pattern_similarity."""
    return compute_pattern_similarity(
        degradation_type, shap_data,
        stored_similarity=stored_similarity,
        model_type=model_type,
    )


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

def build_shap_waterfall(shap_data: list[dict], cycle_label: str = "Latest",
                         base_value: float = None) -> go.Figure:
    """
    SHAP waterfall — arrow-tipped bars, hover to see values, no overlapping labels.
    Blue = negative SHAP, Red = positive. Cumulative from E[f(x)] to f(x).
    """
    if not shap_data:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            annotations=[dict(text="No SHAP data available", xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False,
                              font=dict(color="rgba(168,212,255,0.5)", size=14))]
        )
        return fig

    sorted_data = sorted(shap_data, key=lambda d: abs(d["score"]), reverse=True)
    sensors = [d["sensor"] for d in sorted_data]
    scores  = [d["score"]  for d in sorted_data]
    n = len(sensors)

    base = base_value if base_value is not None else 0.0
    final_value = base + sum(scores)

    # Cumulative offsets
    offsets = []
    running = base
    for s in scores:
        offsets.append(running)
        running += s

    tips = [offsets[i] + scores[i] for i in range(n)]

    # X axis: cluster around where most bars are (tips + offsets for large bars only)
    # Exclude the base offset since it can be far from the action (e.g. base=94, f(x)=27)
    # The largest bar's full extent (offset→tip) must always be visible
    max_abs_score = max(abs(s) for s in scores)
    x_candidates = list(tips) + [final_value]
    for o, s in zip(offsets, scores):
        # Only include offset if it's not the isolated base outlier
        # i.e. include offset only for bars where tip is near the cluster
        x_candidates.append(o)
    # Remove extreme outliers: any value more than 3x range away from the median tip
    import statistics as _stats
    med = _stats.median(tips)
    spread = max(abs(t - med) for t in tips) or 1.0
    x_candidates = [x for x in x_candidates if abs(x - med) <= spread * 4 + max_abs_score]
    x_min_data = min(x_candidates) if x_candidates else min(tips)
    x_max_data = max(x_candidates) if x_candidates else max(tips)
    x_span = max(x_max_data - x_min_data, 1.0)
    x_pad  = x_span * 0.08
    x_min  = x_min_data - x_pad
    x_max  = x_max_data + x_pad

    bar_colors = ["#ff4d4d" if s > 0 else "#4a9eff" for s in scores]
    bar_half_h = 0.28
    arrow_base = x_span * 0.018

    fig = go.Figure()

    for i, (sensor, score, offset, tip, color) in enumerate(
            zip(sensors, scores, offsets, tips, bar_colors)):
        y = i
        bar_width = abs(score)
        a = min(max(arrow_base, abs(score) * 0.10), bar_width * 0.6)

        if score >= 0:
            x0, x1 = offset, tip - a
            px = [x0, x1, tip, x1,  x0, x0]
            py = [y - bar_half_h, y - bar_half_h, y,
                  y + bar_half_h, y + bar_half_h, y - bar_half_h]
        else:
            x0, x1 = tip + a, offset
            px = [x1, x0, tip, x0,  x1, x1]
            py = [y - bar_half_h, y - bar_half_h, y,
                  y + bar_half_h, y + bar_half_h, y - bar_half_h]

        cum_val = tip  # running model output after this feature
        fig.add_trace(go.Scatter(
            x=px, y=py,
            fill="toself",
            fillcolor=color,
            line=dict(color="rgba(0,0,0,0)", width=0),
            mode="none",
            hoverinfo="skip",
            showlegend=False,
        ))

        # Invisible hover marker at bar center — this is what triggers the tooltip
        bar_center_x = (offset + tip) / 2
        fig.add_trace(go.Scatter(
            x=[bar_center_x],
            y=[y],
            mode="markers",
            marker=dict(size=max(12, abs(score) * 0.5), color="rgba(0,0,0,0)",
                        line=dict(width=0)),
            hovertemplate=(
                f"<b>{sensor}</b><br>"
                f"SHAP: <b>{score:+.4f}</b><br>"
                f"Running output: <b>{cum_val:.2f}</b>"
                f"<extra></extra>"
            ),
            showlegend=False,
        ))

    # f(x) annotation
    fig.add_annotation(
        x=final_value, xref="x", y=1.06, yref="paper",
        text=f"f(x) = {round(final_value):.0f}",
        showarrow=False,
        font=dict(color="white", size=11, family="monospace"),
        xanchor="center",
    )

    # E[f(x)] annotation — place near the final_value since base may be off-screen
    fig.add_annotation(
        x=final_value, xref="x", y=-0.07, yref="paper",
        text=f"E[f(x)] = {base:.2f}",
        showarrow=False,
        font=dict(color="rgba(168,212,255,0.55)", size=9, family="monospace"),
        xanchor="center",
    )

    # Dotted line at f(x)
    fig.add_vline(x=final_value, line_width=1, line_dash="dot",
                  line_color="rgba(255,255,255,0.2)")

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=20, t=35, b=45),
        height=380,
        xaxis=dict(
            title="Model output (cumulative SHAP)",
            title_font=dict(color="rgba(168,212,255,0.7)", size=11),
            tickfont=dict(color="rgba(168,212,255,0.6)", size=10),
            gridcolor="rgba(74,158,255,0.08)",
            zeroline=False,
            showline=False,
            range=[x_min, x_max],
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(n)),
            ticktext=sensors,
            tickfont=dict(color="rgba(168,212,255,0.85)", size=10),
            showgrid=False,
            zeroline=False,
            range=[n - 0.5, -0.5],
        ),
        hovermode="closest",
        hoverlabel=dict(
            bgcolor="#0d1e3a",
            bordercolor="rgba(74,158,255,0.4)",
            font=dict(color="white", size=12),
        ),
    )
    return fig


# ─────────────────────────────────────────────
#  SHAP TREND LINE CHART
# ─────────────────────────────────────────────

def build_shap_trend_chart(cycles: list, shap_history: list[list[dict]], top_n: int = None) -> go.Figure:
    """
    Line chart showing SHAP values over cycles for all contributing sensors.
    shap_history: list of shap_data per cycle (same order as cycles list).
    top_n is kept for backwards compatibility but ignored — all sensors are shown.
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

    # Collect all sensors, ordered by average |score| descending
    sensor_scores = {}
    for snapshot in shap_history:
        if not snapshot:
            continue
        for entry in snapshot:
            name = entry["sensor"]
            sensor_scores.setdefault(name, []).append(abs(entry["score"]))

    avg_scores = {s: np.mean(vals) for s, vals in sensor_scores.items()}
    top_sensors = sorted(avg_scores.keys(), key=lambda s: avg_scores[s], reverse=True)

    # Build time-series per sensor
    color_palette = [
        "#4a9eff", "#ff4d4d", "#ffd93d", "#00c875", "#7b61ff",
        "#ff9f43", "#a8d4ff", "#ff6b6b", "#54e0c7", "#c084fc",
        "#f9ca24", "#6ab04c", "#e056fd", "#22a6b3", "#eb4d4b",
        "#be2edd", "#4834d4", "#f0932b", "#badc58", "#30336b",
    ]

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
        margin=dict(l=50, r=20, t=60, b=40),
        height=380,
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
    )
    return fig


# ─────────────────────────────────────────────
#  LLM EXPLANATION (Groq — Llama 3.3 70B)
# ─────────────────────────────────────────────

def _build_llm_prompt(degradation_type: str, confidence: float,
                      top_features: list[dict], sensor_trends: dict | None = None) -> str:
    """
    Construct a tightly-scoped prompt for Groq (Llama 3.3 70B).
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
        f"- Detected degradation profile: {degradation_type}\n"
        f"- Pattern similarity score: {confidence:.1%} "
        f"(cosine similarity to the {degradation_type} reference profile)\n"
        f"- Top contributing sensors (SHAP attribution — negative = drives predicted RUL down):\n"
        f"{features_str}\n"
        f"{trend_str}\n\n"
        f"RULES:\n"
        f"- You MUST mention the degradation profile '{degradation_type}' and "
        f"pattern similarity '{confidence:.1%}' verbatim.\n"
        f"- Clarify that this identifies similarity to a known degradation profile, "
        f"not a confirmed fault diagnosis.\n"
        f"- Explain the physical meaning: what is likely happening inside the engine.\n"
        f"- Be specific to the sensors listed — don't give generic advice.\n"
        f"- Suggest 1-2 concrete inspection actions relevant to the degradation profile.\n"
        f"- Keep it to 4-6 sentences. Professional tone, no hedging.\n"
    )
    return prompt


def _validate_llm_output(text: str, degradation_type: str, confidence: float) -> bool:
    """
    Lightweight validation: confirm that the LLM output contains the
    degradation profile label and pattern similarity value that were passed in.
    """
    if not text:
        return False
    # Check degradation profile label present (case-insensitive)
    if degradation_type.lower() not in text.lower():
        return False
    # Check similarity value appears (allow ±1% formatting variance)
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

    if "HPC" in degradation_type and "Fan" in degradation_type:
        mechanism = (
            "The sensor importance pattern is consistent with combined HPC and fan degradation, "
            "suggesting simultaneous compressor blade erosion and fan aerodynamic efficiency loss. "
            "Recommend borescope inspection of HPC stages, fan blade visual inspection, and "
            "vibration signature analysis."
        )
    elif "HPC" in degradation_type:
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
            "Multiple degradation pathways may be active. "
            "Recommend comprehensive inspection of both HPC and fan sections."
        )

    return (
        f"Degradation profile: {degradation_type} "
        f"(pattern similarity: {confidence:.1%}). "
        f"Key indicators: {details_str}. {mechanism} "
        f"Note: this identifies similarity to a known degradation profile; "
        f"physical confirmation requires inspection."
    )


def generate_llm_explanation(degradation_type: str, confidence: float,
                             top_features: list[dict],
                             sensor_trends: dict | None = None) -> str:
    """
    Call Groq API (Llama 3.3 70B) to generate natural language explanation.
    Falls back to a templated string if the API is unavailable or validation fails.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return _fallback_explanation(degradation_type, confidence, top_features)

    prompt = _build_llm_prompt(degradation_type, confidence, top_features, sensor_trends)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        text = response.choices[0].message.content.strip() if response.choices else ""

        if _validate_llm_output(text, degradation_type, confidence):
            return text
        else:
            print("[DEGRAD] LLM output failed validation, using fallback.")
            return _fallback_explanation(degradation_type, confidence, top_features)

    except ImportError:
        print("[DEGRAD] groq package not installed. Using fallback.")
        return _fallback_explanation(degradation_type, confidence, top_features)
    except Exception as e:
        print(f"[DEGRAD] Groq API error: {e}")
        return _fallback_explanation(degradation_type, confidence, top_features)


# ─────────────────────────────────────────────
#  PAGE LAYOUT
# ─────────────────────────────────────────────

def create_degradation_analysis_layout(supabase=None, engine_db_id=None):
    """Build the full Degradation Analysis page layout."""

    # ── Fetch engine metadata ──
    engine_label = "No engine selected"
    degradation_type = None
    degradation_confidence = None
    model_type = None
    cached_explanation = None
    cached_explanation_ts = None

    if supabase and engine_db_id:
        try:
            resp = supabase.table("engines") \
                .select("engine_id, degradation_type, degradation_confidence, model_type, llm_explanation, llm_explanation_updated_at") \
                .eq("id", engine_db_id) \
                .single() \
                .execute()
            if resp.data:
                engine_label = f"Engine #{resp.data.get('engine_id', engine_db_id)}"
                degradation_type = resp.data.get("degradation_type")
                degradation_confidence = resp.data.get("degradation_confidence")
                model_type = resp.data.get("model_type", "")
                cached_explanation = resp.data.get("llm_explanation")
                cached_explanation_ts = resp.data.get("llm_explanation_updated_at")
        except Exception:
            pass

    # ── Display values ──
    deg_type_display = degradation_type or "No pattern detected"
    # Colour coding: confirmed patterns = red, ambiguous = amber, none = dim blue
    if degradation_type in ("HPC Degradation", "HPC + Fan Degradation"):
        deg_color = "#ff4d4d"
        deg_dot_color = "#ff4d4d"
        deg_dot_shadow = "0 0 8px rgba(255,77,77,0.6)"
    else:
        deg_color = "rgba(168,212,255,0.5)"
        deg_dot_color = "rgba(168,212,255,0.3)"
        deg_dot_shadow = "none"

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
                    "display": "flex", "flexDirection": "column",
                    "justifyContent": "space-between", "gap": "12px",
                },
                children=[
                    # Section 1: Status Overview + Fault Mode
                    html.Div(children=[
                        html.Div("STATUS OVERVIEW", style={
                            "color": "rgba(168,212,255,0.5)", "fontSize": "10px",
                            "fontWeight": "700", "letterSpacing": "1.2px", "marginBottom": "4px",
                        }),
                        html.Div("DEGRADATION PATTERN", style={
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
                                    "background": deg_dot_color,
                                    "boxShadow": deg_dot_shadow,
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
                                    html.Div("PATTERN SIMILARITY", style={
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
                                "color": "white", "fontSize": "16px", "fontWeight": "700"
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
            # Column 3: SHAP waterfall chart (flex: 2)
            html.Div(
                style={
                    "flex": "2", "minWidth": "0",
                    "background": "rgba(13,32,69,0.5)",
                    "border": "1px solid rgba(74,158,255,0.15)",
                    "borderRadius": "12px", "padding": "16px",
                    "display": "flex", "flexDirection": "column",
                },
                children=[
                    # Header: title + cycle selector
                    html.Div(
                        style={"display": "flex", "alignItems": "center",
                               "justifyContent": "space-between", "marginBottom": "10px"},
                        children=[
                            html.Div("SHAP Waterfall", style={
                                "color": "white", "fontSize": "16px", "fontWeight": "700",
                            }),
                            dcc.Dropdown(
                                id="da-cycle-selector",
                                options=[{"label": "Latest", "value": "latest"}],
                                value="latest",
                                clearable=False,
                                className="dark-dropdown",
                                style={
                                    "width": "130px",
                                    "background": "rgba(10,20,45,0.8)",
                                    "border": "1.5px solid rgba(74,158,255,0.4)",
                                    "borderRadius": "8px",
                                    "color": "white",
                                    "fontSize": "12px",
                                },
                            ),
                        ]
                    ),
                    dcc.Graph(
                        id="da-shap-waterfall",
                        config={"displayModeBar": False},
                        figure=build_shap_waterfall([]),
                        style={"flex": "1", "minHeight": "0", "height": "380px"},
                    ),
                ]
            ),
        ]
    )

    # ── Row 2: SHAP trend chart (5:1 ratio) + AI explanation ──
    row2 = html.Div(
        style={"display": "flex", "gap": "20px", "padding": "0 28px 28px",
               "alignItems": "stretch"},
        children=[
            # SHAP trend chart (flex: 5)
            html.Div(
                style={
                    "flex": "5", "minWidth": "0",
                    "background": "rgba(13,32,69,0.5)",
                    "border": "1px solid rgba(74,158,255,0.15)",
                    "borderRadius": "12px", "padding": "16px", "height": "auto",
                },
                children=[
                    html.Div("SHAP Value Trend Over Cycles", style={
                                "color": "white", "fontSize": "16px", "fontWeight": "700",
                            }),
                    dcc.Graph(id="da-shap-trend", config={"displayModeBar": False},
                              figure=build_shap_trend_chart([], [])),
                ]
            ),
            # AI Explanation (flex: 1) — matches chart height, content scrolls
            html.Div(
                style={
                    "flex": "1", "minWidth": "200px",
                    "background": "rgba(13,32,69,0.5)",
                    "border": "1px solid rgba(74,158,255,0.15)",
                    "borderRadius": "12px", "padding": "20px",
                    "display": "flex", "flexDirection": "column",
                    "overflow": "hidden", "height": "350px",
                },
                children=[
                    html.Div(style={"display": "flex", "flexDirection": "column", "gap": "8px",
                                    "marginBottom": "14px", "flexShrink": "0"}, children=[
                        html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=[
                            html.Div("AI EXPLANATION", style={
                                "color": "rgba(168,212,255,0.7)", "fontSize": "11px",
                                "fontWeight": "700", "letterSpacing": "1px",
                            }),
                            html.Span("Llama 3.3 70B", style={
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
                    dcc.Loading(
                        id="da-llm-loading",
                        type="circle",
                        color="#4a9eff",
                        style={"flex": "1", "minHeight": "0", "overflow": "hidden",
                               "display": "flex", "flexDirection": "column"},
                        children=[
                            html.Div(
                                id="da-llm-explanation",
                                style={
                                    "color": "rgba(168,212,255,0.8)", "fontSize": "12px",
                                    "lineHeight": "1.7",
                                    "overflowY": "auto",
                                    "maxHeight": "200px",
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
            ),
        ]
    )

    # ── Stores ──
    stores = html.Div([
        dcc.Store(id="da-engine-db-id", data=engine_db_id),
        dcc.Store(id="da-degradation-type", data=degradation_type),
        dcc.Store(id="da-degradation-confidence", data=degradation_confidence),
        dcc.Store(id="da-model-type", data=model_type),
        dcc.Store(id="da-shap-history-store", data={"cycles": [], "history": []}),
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
        Output("da-shap-waterfall", "figure"),
        Output("da-shap-trend", "figure"),
        Output("da-confidence-value", "children"),
        Output("da-confidence-ring", "children"),
        Output("da-rul-value", "children"),
        Output("da-rul-sparkline", "figure"),
        Output("da-fault-mode-label", "children"),
        Output("da-top-drivers-chart", "figure"),
        Output("da-interval", "disabled"),
        Output("da-shap-history-store", "data"),
        Output("da-cycle-selector", "options"),
        Input("da-interval", "n_intervals"),
        State("da-engine-db-id", "data"),
        State("da-degradation-type", "data"),
        State("da-degradation-confidence", "data"),
        State("da-model-type", "data"),
        State("da-top-drivers-filter", "data"),
        prevent_initial_call=False,
    )
    def update_charts(n_intervals, engine_db_id, degradation_type,
                      stored_similarity, model_type, top_n_filter):
        """
        Poll callback: fetch SHAP history, compute pattern similarity, update charts.
        Disables the interval once the prediction cycle is complete.
        Does NOT call the LLM — that is triggered only by button click.
        """
        from engine_simulation_manager import is_running as _sim_is_running

        empty_sparkline = _build_rul_sparkline([])

        if not supabase or not engine_db_id:
            return (
                build_shap_waterfall([]),
                build_shap_trend_chart([], []),
                "—",
                _build_confidence_ring(0),
                "—",
                empty_sparkline,
                "NO PATTERN DETECTED",
                build_top_drivers_chart(None),
                False,
                {"cycles": [], "history": []},
                [{"label": "Latest", "value": "latest"}],
            )

        # ── Check if simulation is still running ──
        sim_active = _sim_is_running(engine_db_id)

        # ── Fetch prediction + SHAP history ──
        cycles_list = []
        shap_history = []
        latest_shap = []
        predicted_ruls = []
        shap_base_values = []

        try:
            resp = supabase.table("rul_predictions") \
                .select("cycle, predicted_rul, shap_values, shap_base_value") \
                .eq("engine_id", engine_db_id) \
                .order("cycle", desc=False) \
                .execute()

            for row in (resp.data or []):
                shap = _json.loads(row["shap_values"]) if isinstance(row["shap_values"], str) else row["shap_values"]
                total_shap = sum(d["score"] for d in shap) if shap else None
                # print(f"cycle={row['cycle']:>3}  predicted_rul={row['predicted_rul']:>8}  "
                    #   f"base={row['shap_base_value']:>8}  sum(shap)={total_shap}")
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
                base_val = row.get("shap_base_value")
                shap_base_values.append(float(base_val) if base_val is not None else 0.0)

            # Debug: show how many rows have shap_values populated
            rows_with_shap = sum(1 for s in shap_history if s)
            print(f"[DEGRAD] engine={engine_db_id}: {len(cycles_list)} prediction rows, "
                  f"{rows_with_shap} with shap_values")

            # Latest valid SHAP snapshot
            for snapshot in reversed(shap_history):
                if snapshot:
                    latest_shap = snapshot
                    break

            # Latest base value
            latest_base = 0.0
            for bv in reversed(shap_base_values):
                if bv != 0.0:
                    latest_base = bv
                    break

        except Exception as e:
            print(f"[DEGRAD] Error fetching SHAP data: {e}")
            return (
                build_shap_waterfall([]),
                build_shap_trend_chart([], []),
                "—",
                _build_confidence_ring(0),
                "—",
                empty_sparkline,
                "NO PATTERN DETECTED",
                build_top_drivers_chart(None),
                not sim_active,
                {"cycles": [], "history": []},
                [{"label": "Latest", "value": "latest"}],
            )

        # ── Re-fetch degradation_type and stored similarity (may have updated) ──
        if supabase and engine_db_id:
            try:
                eng_resp = supabase.table("engines") \
                    .select("degradation_type, degradation_confidence, model_type") \
                    .eq("id", engine_db_id) \
                    .single() \
                    .execute()
                if eng_resp.data:
                    degradation_type   = eng_resp.data.get("degradation_type") or degradation_type
                    stored_similarity  = eng_resp.data.get("degradation_confidence") or stored_similarity
                    model_type         = eng_resp.data.get("model_type") or model_type
            except Exception:
                pass

        # ── Pattern similarity score ──────────────────────────────────────────
        similarity = compute_pattern_similarity(
            degradation_type, latest_shap,
            stored_similarity=stored_similarity,
            model_type=model_type,
        )
        similarity_pct = int(round(similarity * 100)) if similarity is not None else 0
        similarity_display = f"{similarity_pct}%" if similarity is not None else "—"

        # ── Latest RUL value ──
        latest_rul = None
        for v in reversed(predicted_ruls):
            if v is not None:
                latest_rul = v
                break
        rul_display = str(int(round(latest_rul))) if latest_rul is not None else "—"

        # ── Fault mode label — surface insufficient state clearly ──
        if degradation_type == "Insufficient Signal":
            fault_label = "INSUFFICIENT SIGNAL"
        elif degradation_type:
            fault_label = degradation_type.upper()
        else:
            fault_label = "NO PATTERN DETECTED"

        # ── Build charts ──
        waterfall_fig    = build_shap_waterfall(latest_shap, cycle_label="Latest", base_value=latest_base)
        trend_fig        = build_shap_trend_chart(cycles_list, shap_history, top_n=5)
        sparkline_fig    = _build_rul_sparkline([v for v in predicted_ruls if v is not None])
        top_drivers_fig  = build_top_drivers_chart(latest_shap, top_n=top_n_filter or "all")

        # ── Build cycle selector options ──
        cycle_options = [{"label": "Latest", "value": "latest"}] + [
            {"label": f"Cycle {c}", "value": str(i)}
            for i, c in enumerate(cycles_list) if c is not None
        ]

        return (
            waterfall_fig,
            trend_fig,
            similarity_display,
            _build_confidence_ring(similarity_pct),
            rul_display,
            sparkline_fig,
            fault_label,
            top_drivers_fig,
            not sim_active,
            {"cycles": cycles_list, "history": shap_history, "base_values": shap_base_values},
            cycle_options,
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
        Calls Groq API once per click, then caches the result
        in engines.llm_explanation to avoid repeat API calls.
        """
        if not n_clicks or not supabase or not engine_db_id:
            raise dash.exceptions.PreventUpdate

        # Fetch latest SHAP + degradation type + stored similarity
        latest_shap = []
        stored_similarity = None
        model_type_fetched = None
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

        # Re-fetch degradation_type, stored similarity and model_type
        try:
            eng_resp = supabase.table("engines") \
                .select("degradation_type, degradation_confidence, model_type") \
                .eq("id", engine_db_id) \
                .single() \
                .execute()
            if eng_resp.data:
                degradation_type   = eng_resp.data.get("degradation_type") or degradation_type
                stored_similarity  = eng_resp.data.get("degradation_confidence")
                model_type_fetched = eng_resp.data.get("model_type")
        except Exception:
            pass

        # Don't generate if pattern is ambiguous, insufficient, or absent
        if not degradation_type or degradation_type == "Insufficient Signal":
            return (
                "No degradation pattern has been identified for this engine. "
                "The engine is operating within normal parameters or the signal "
                "is not yet strong enough to report."
            )

        if not latest_shap:
            return "Insufficient SHAP data to generate analysis. Awaiting more prediction cycles."

        similarity = compute_pattern_similarity(
            degradation_type, latest_shap,
            stored_similarity=stored_similarity,
            model_type=model_type_fetched,
        )
        if similarity is None:
            similarity = 0.0

        explanation = generate_llm_explanation(
            degradation_type=degradation_type,
            confidence=similarity,
            top_features=latest_shap[:5],
            sensor_trends=None,
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

    @app.callback(
        Output("da-shap-waterfall", "figure", allow_duplicate=True),
        Input("da-cycle-selector", "value"),
        State("da-shap-history-store", "data"),
        prevent_initial_call=True,
    )
    def update_waterfall_on_cycle_select(selected_value, store_data):
        """Re-render the waterfall chart when the user picks a specific cycle."""
        if not store_data:
            return build_shap_waterfall([])

        cycles      = store_data.get("cycles", [])
        history     = store_data.get("history", [])
        base_values = store_data.get("base_values", [])

        if selected_value == "latest" or not selected_value:
            # Show latest valid snapshot
            latest_shap = []
            latest_base = 0.0
            for i, snapshot in enumerate(reversed(history)):
                if snapshot:
                    latest_shap = snapshot
                    idx = len(history) - 1 - i
                    latest_base = base_values[idx] if idx < len(base_values) else 0.0
                    break
            return build_shap_waterfall(latest_shap, cycle_label="Latest", base_value=latest_base)

        # Selected value is the index into cycles/history
        try:
            idx = int(selected_value)
            shap_data   = history[idx] if idx < len(history) else []
            base_val    = base_values[idx] if idx < len(base_values) else 0.0
            cycle_label = f"Cycle {cycles[idx]}" if idx < len(cycles) else f"Cycle {idx}"
            return build_shap_waterfall(shap_data, cycle_label=cycle_label, base_value=base_val)
        except (ValueError, IndexError):
            return build_shap_waterfall([])

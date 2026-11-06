import numpy as np

import engine_simulation_manager as sim
from conftest import make_cycles, run_storage_loop


def test_shap_explanation_returns_sensor_scores_for_a_model_window(env):
    model = sim._load_model("FD001", supabase=env)
    values = np.zeros((1, 45, 42), dtype=np.float32)
    shap_data, base_value = sim._compute_feature_importance(
        model, values, 14, pred_raw=0.5, rul_cap=float(sim.RUL_CAP)
    )
    assert len(shap_data) == 14
    assert all(set(item) == {"sensor", "score"} for item in shap_data)
    assert all(np.isfinite(item["score"]) for item in shap_data)
    assert np.isfinite(base_value)


def test_reference_shap_pattern_maps_to_expected_degradation():
    reference = sim._REF_VECS["FD001"]
    shap_data = [
        {"sensor": sensor, "score": float(score)}
        for sensor, score in zip(sim._PATTERN_SENSORS, reference)
    ]
    label, similarity = sim._detect_degradation_type("FD001", shap_data, 25, 50)
    assert label == "HPC Degradation"
    assert similarity is not None and similarity > 0.99


def test_no_shap_signal_is_reported_as_insufficient():
    shap_data = [{"sensor": sensor, "score": 0.0} for sensor in sim._PATTERN_SENSORS]
    label, similarity = sim._detect_degradation_type("FD001", shap_data, 25, 50)
    assert label == "Insufficient Signal"
    assert similarity == 0.0


def test_shap_pattern_result_is_persisted_with_prediction(tmp_path, env, monkeypatch):
    reference = sim._REF_VECS["FD001"]
    data = [
        {"sensor": sensor, "score": float(score)}
        for sensor, score in zip(sim._PATTERN_SENSORS, reference)
    ]
    monkeypatch.setattr(sim, "SHAP_INTERVAL", 1)
    monkeypatch.setattr(sim, "_compute_feature_importance", lambda *a, **k: (data, 0.25))
    run_storage_loop(tmp_path, env, monkeypatch, make_cycles(45))
    assert env.predictions[0]["shap_base_value"] == 0.25
    assert env.engines["e1"]["degradation_type"] == "HPC Degradation"
    assert env.engines["e1"]["degradation_confidence"] > 0.99


def test_fallback_mentions_only_current_shap_sensors_and_uses_raw_slope_direction(monkeypatch):
    import degradation_analysis as analysis

    features = [
        {"sensor": "Nc", "score": -0.4}, {"sensor": "phi", "score": -0.3},
        {"sensor": "NRc", "score": -0.2}, {"sensor": "BPR", "score": 0.1},
        {"sensor": "T50", "score": 0.05},
    ]
    explanation = analysis._fallback_explanation(
        "HPC Degradation", 0.88, features, sensor_trends={"Nc": 0.2},
        predicted_rul=48, warn_threshold=50, crit_threshold=30,
    )
    why = explanation.split("### Engineering Interpretation")[0]
    assert "**Nc**" in why and "contributes toward lower predicted RUL" in why
    assert "measured value increased" in why
    assert "declining" not in explanation.lower()
    assert "elevated" not in explanation.lower()
    assert "P30" not in explanation
    assert "[Priority" not in explanation


def test_raw_sensor_slope_for_nc_uses_core_speed_measurements(monkeypatch):
    import degradation_analysis as analysis

    rows = [
        {"cycle": cycle, "sensors": {"s9": 9100 - cycle * 2}}
        for cycle in range(1, 6)
    ]
    monkeypatch.setattr(sim, "get_sensor_history", lambda _engine_id: rows)
    slopes = analysis._get_raw_sensor_slopes("e1", ["Nc"])
    assert slopes["Nc"] < 0

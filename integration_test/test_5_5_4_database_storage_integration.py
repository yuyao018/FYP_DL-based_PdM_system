import json
import threading

import httpx

import engine_simulation_manager as sim
import storage_utils
from conftest import FakeClock, make_cycles, run_storage_loop


def test_prediction_is_persisted_with_model_version_and_cycle_data(tmp_path, env, monkeypatch):
    monkeypatch.setattr(sim, "SHAP_INTERVAL", 1)
    monkeypatch.setattr(sim, "_compute_feature_importance", lambda *a, **k: ([{"sensor": "s2", "score": 0.1}], 0.25))
    run_storage_loop(tmp_path, env, monkeypatch, make_cycles(45))
    prediction = env.predictions[0]
    assert prediction["engine_id"] == "e1"
    assert prediction["cycle"] == 45
    assert prediction["model_version_id"] == "v1"
    assert 0 <= prediction["predicted_rul"] <= sim.RUL_CAP
    assert json.loads(prediction["shap_values"])[0]["sensor"] == "s2"


def test_transient_prediction_insert_failure_is_retried(tmp_path, env, monkeypatch):
    original_insert = sim.db.insert_records
    attempts = 0

    def fail_once(client, table, data):
        nonlocal attempts
        if table == "rul_predictions":
            attempts += 1
            if attempts == 1:
                raise httpx.ReadError("temporary connection drop")
        return original_insert(client, table, data)

    monkeypatch.setattr(sim.db, "insert_records", fail_once)
    monkeypatch.setattr(sim.time, "sleep", lambda _seconds: None)
    run_storage_loop(tmp_path, env, monkeypatch, make_cycles(47))
    assert attempts == 4  # one retry for cycle 45, then inserts for cycles 46 and 47
    assert [prediction["cycle"] for prediction in env.predictions] == [45, 46, 47]


def test_engine_cycle_rows_are_fetched_from_supabase_storage(tmp_path, env, monkeypatch):
    requested = []
    original_download = sim.db.download_file

    def track_download(client, bucket, path):
        requested.append((bucket, path))
        return original_download(client, bucket, path)

    monkeypatch.setattr(sim.db, "download_file", track_download)
    run_storage_loop(tmp_path, env, monkeypatch, make_cycles(2))
    assert ("engine-data", "FD001/engine_e1.json") in requested
    assert env.engines["e1"]["current_cycle"] == 2


def test_missing_storage_object_does_not_advance_engine(tmp_path, env, monkeypatch):
    monkeypatch.setattr(sim.db, "download_file", lambda *a: (_ for _ in ()).throw(RuntimeError("storage unavailable")))
    monkeypatch.setattr(storage_utils, "_get_supabase_admin", lambda: env)
    monkeypatch.setattr(storage_utils, "_CACHE_DIR", tmp_path / "empty-cache")
    absent_path = tmp_path / "engines" / "FD001" / "engine_e1.json"
    sim._simulation_loop("e1", str(absent_path), "FD001", env, threading.Event(), FakeClock())
    assert env.engines["e1"]["current_cycle"] == 0
    assert env.predictions == []


def test_unavailable_model_storage_produces_no_prediction(tmp_path, env, monkeypatch):
    monkeypatch.setattr(sim.db, "download_file", lambda client, bucket, path: (
        env.storage_files[path] if bucket == "engine-data" else (_ for _ in ()).throw(RuntimeError("model storage unavailable"))
    ))
    run_storage_loop(tmp_path, env, monkeypatch, make_cycles(45))
    assert env.engines["e1"]["current_cycle"] == 45
    assert env.predictions == []

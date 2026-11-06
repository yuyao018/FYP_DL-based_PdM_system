import threading
import time
import numpy as np
import pytest
import email_notifications
from email_notifications import check_and_send_threshold_alert as send_threshold_alert
import engine_simulation_manager as sim
import storage_utils
from conftest import FakeClock, make_cycles, run_storage_loop
from simulation_clock import SimulationClock


class FixedRulModel:
    def __init__(self, rul): self.rul = rul
    def predict(self, values, verbose=0): return np.array([[self.rul]], dtype=np.float32)


@pytest.mark.parametrize("rul, status", [(30, "critical"), (31, "warning"), (50, "warning"), (51, "healthy")])
def test_rul_thresholds_update_engine_condition(tmp_path, env, monkeypatch, rul, status):
    monkeypatch.setattr(sim, "_load_model", lambda *a, **k: FixedRulModel(rul))
    monkeypatch.setattr(sim, "_compute_feature_importance", lambda *a, **k: ([], 0.0))
    monkeypatch.setattr(sim, "_fetch_thresholds", lambda *a, **k: (50.0, 30.0))
    run_storage_loop(tmp_path, env, monkeypatch, make_cycles(45))
    assert env.engines["e1"]["condition_status"] == status


def test_warning_and_critical_alerts_log_threshold_snapshot(env, monkeypatch):
    logged = []
    original_insert = email_notifications.db.insert_records

    def capture_alert(client, table, data):
        if table == "alert_logs": logged.append(dict(data))
        return original_insert(client, table, data)

    monkeypatch.setattr(email_notifications.db, "insert_records", capture_alert)
    monkeypatch.setattr(email_notifications, "_get_alert_recipients", lambda *a, **k: [])
    import maintenance_recommendations
    monkeypatch.setattr(maintenance_recommendations, "email_section", lambda *a, **k: "")
    monkeypatch.setattr(email_notifications, "_send_email", lambda *a, **k: False)
    email_notifications._alert_state.clear()
    send_threshold_alert(env, "e1", "01", 25, 50, 30, trigger_cycle=45)
    assert logged[0]["severity"] == "critical"
    assert logged[0]["predicted_rul"] == 25
    assert logged[0]["trigger_cycle"] == 45


def test_maintenance_completion_starts_simulation_paused_for_verification(tmp_path, env, monkeypatch):
    env.maintenance_schedules = [{"status": "completed"}]
    env.storage_files["FD001/engine_e1.json"] = __import__("json").dumps(make_cycles(1)).encode()
    monkeypatch.setattr(storage_utils, "_get_supabase_admin", lambda: env)
    monkeypatch.setattr(storage_utils, "_CACHE_DIR", tmp_path / "maintenance-cache")
    path = tmp_path / "engines" / "FD001" / "engine_e1.json"
    started = sim.start_engine_simulation("e1", str(path), "FD001", env)
    try:
        assert started is True
        state = sim.get_simulation_state("e1")
        assert state["awaiting_verification"] is True
        assert state["maintenance_status"] == "pending_verification"
        assert state["paused"] is True
        assert sim.configure_simulation("e1", paused=False) is False
    finally:
        sim.stop_engine_simulation("e1")
        entry = sim._RUNNING_SIMULATIONS.get("e1")
        if entry:
            entry["thread"].join(timeout=2)
            sim._RUNNING_SIMULATIONS.pop("e1", None)


def test_paused_clock_waits_until_resumed(monkeypatch):
    import simulation_clock
    monkeypatch.setattr(simulation_clock, "BASE_CYCLE_SECONDS", 0.05)
    clock = SimulationClock()
    clock.configure(paused=True)
    stopped, completed = threading.Event(), threading.Event()
    worker = threading.Thread(target=lambda: completed.set() if clock.wait_cycle(stopped) else None)
    worker.start()
    time.sleep(0.05)
    assert not completed.is_set()
    clock.configure(paused=False)
    worker.join(timeout=1)
    assert completed.is_set()


def test_simulation_uses_warning_threshold_of_50_by_default(env, monkeypatch):
    monkeypatch.setattr(sim.db, "get_alert_thresholds", lambda *a, **k: type("Response", (), {"data": []})())
    assert sim._fetch_thresholds(env) == (50.0, 30.0)
    assert sim._rul_to_status(50) == "warning"
    assert sim._rul_to_status(50.01) == "healthy"

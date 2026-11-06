import threading

import engine_simulation_manager as sim
import storage_utils
from conftest import FakeClock, make_cycles, run_storage_loop


class StopAfterCycles(FakeClock):
    def __init__(self, count):
        super().__init__()
        self.count = count
        self.waits = 0

    def wait_cycle(self, stop_event):
        self.waits += 1
        if self.waits > self.count:
            stop_event.set()
            return False
        return not stop_event.is_set()


# def test_resume_skips_saved_cycles_and_restores_prediction_window(tmp_path, env, monkeypatch):
#     env.engines["e1"]["current_cycle"] = 50
#     run_storage_loop(tmp_path, env, monkeypatch, make_cycles(60))
#     assert [p["cycle"] for p in env.predictions] == list(range(51, 61))


def test_interrupted_run_resumes_without_duplicate_predictions(tmp_path, env, monkeypatch):
    cycles = make_cycles(50)
    stop = threading.Event()
    run_storage_loop(tmp_path, env, monkeypatch, cycles, stop_event=stop, clock=StopAfterCycles(47))
    assert env.engines["e1"]["current_cycle"] == 47
    run_storage_loop(tmp_path, env, monkeypatch, cycles)
    assert [p["cycle"] for p in env.predictions] == list(range(45, 51))


def test_missing_sensor_cycle_is_skipped_without_ending_loop(tmp_path, env, monkeypatch):
    cycles = make_cycles(60)
    del cycles[10]["sensors"]["s2"]
    run_storage_loop(tmp_path, env, monkeypatch, cycles)
    assert env.engines["e1"]["current_cycle"] == 60
    assert [p["cycle"] for p in env.predictions] == list(range(46, 61))


def test_concurrent_engines_keep_progress_and_sensor_buffers_separate(tmp_path, env, monkeypatch):
    cycles1, cycles2 = make_cycles(45), make_cycles(45)
    for row in cycles2:
        row["sensors"]["s2"] += 1000
    env.storage_files["FD001/engine_e1.json"] = __import__("json").dumps(cycles1).encode()
    env.storage_files["FD001/engine_e2.json"] = __import__("json").dumps(cycles2).encode()
    monkeypatch.setattr(storage_utils, "_get_supabase_admin", lambda: env)
    cache_dir = tmp_path / "cache"
    (cache_dir / "engine-data").mkdir(parents=True)
    monkeypatch.setattr(storage_utils, "_CACHE_DIR", cache_dir)
    workers = [
        threading.Thread(target=sim._simulation_loop,
            args=(eid, str(tmp_path / "engines" / "FD001" / f"engine_{eid}.json"),
                  "FD001", env, threading.Event(), FakeClock()))
        for eid in ("e1", "e2")
    ]
    for worker in workers: worker.start()
    for worker in workers: worker.join(timeout=30)
    assert all(not worker.is_alive() for worker in workers)
    assert env.engines["e1"]["current_cycle"] == env.engines["e2"]["current_cycle"] == 45
    assert {(p["engine_id"], p["cycle"]) for p in env.predictions} == {("e1", 45), ("e2", 45)}
    assert sim.get_sensor_history("e1")[0]["sensors"]["s2"] != sim.get_sensor_history("e2")[0]["sensors"]["s2"]


def test_starting_an_active_engine_does_not_create_a_second_worker(env):
    engine_id = "active-engine"
    release = threading.Event()
    worker = threading.Thread(target=release.wait)
    worker.start()
    sim._RUNNING_SIMULATIONS[engine_id] = {"thread": worker, "stop": threading.Event(), "model_type": "FD001"}
    try:
        assert sim.start_engine_simulation(engine_id, "unused.json", "FD001", env) is False
        assert sim._RUNNING_SIMULATIONS[engine_id]["thread"] is worker
    finally:
        release.set(); worker.join(timeout=1)
        sim._RUNNING_SIMULATIONS.pop(engine_id, None)

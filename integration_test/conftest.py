# conftest.py
import io, json, threading, types
import h5py, numpy as np, pytest, torch
import engine_simulation_manager as sim

class Resp:  # mimics supabase response
    def __init__(self, data): self.data = data

class FakeDB:
    def __init__(self, model_bytes):
        self.model_bytes = model_bytes
        self.engines = {
            "e1": {"id": "e1", "current_cycle": 0, "condition_status": "healthy", "engine_id": 1},
            "e2": {"id": "e2", "current_cycle": 0, "condition_status": "healthy", "engine_id": 2},
        }
        self.predictions = []
        self.storage_files = {}
        self.active_model_id = "v1"
        self.maintenance_schedules = []
        self.alert_logs = []

    def fetch_records(self, sb, table, cols, filters=None, limit=None, order_by=None):
        if table == "model_versions":
            return Resp([{"id": self.active_model_id, "filename": f"{self.active_model_id}.h5"}])
        if table == "maintenance_schedules":
            return Resp(self.maintenance_schedules)
        if table == "alert_logs":
            return Resp(self.alert_logs)
        if table == "engines":
            return Resp(list(self.engines.values()))
        return Resp([])
    def get_engine(self, sb, eid, cols): return Resp(self.engines[eid])
    def update_records(self, sb, table, data, filters=None):
        if table == "engines":
            engine_id = next((value for op, key, value in (filters or []) if key == "id"), "e1")
            self.engines[str(engine_id)].update(data)
        return Resp([])
    def insert_records(self, sb, table, data):
        if table == "rul_predictions": self.predictions.append(data)
        if table == "alert_logs": self.alert_logs.append(data)
        return Resp([data])
    def download_file(self, sb, bucket, path):
        if bucket == "engine-data":
            return self.storage_files[path]
        return self.model_bytes
    def get_alert_thresholds(self, sb, cols):
        return Resp([{"warning_threshold": 50, "critical_threshold": 30}])

class FakeClock:
    def __init__(self): self._cond, self.cycle = "healthy", 0
    def wait_cycle(self, stop): return not stop.is_set()
    def observe(self, cond, cycle): self._cond, self.cycle = cond, cycle
    def snapshot(self): return {"condition": self._cond, "cycle": self.cycle}
    def configure(self, **kw): pass

def make_h5(num_features=42, window=45, seq=45):
    cfg = dict(d_model=16, num_heads=2, num_layers=1, ff_dim=32,
               hidden_dim_gru=8, dropout=0.0, window_attn=3)
    m = sim._build_model(num_features, seq_len=seq, **cfg)
    buf = io.BytesIO()
    with h5py.File(buf, "w") as f:
        meta = f.create_group("metadata")
        for k, v in dict(num_features=num_features, window_size=window, **cfg).items():
            meta.attrs[k] = v
        meta.attrs["bias_shift"] = 0.0
        w = f.create_group("weights")
        for k, v in m.state_dict().items():
            w.create_dataset(k, data=v.numpy())
    return buf.getvalue()

@pytest.fixture
def env(monkeypatch):
    fake = FakeDB(make_h5())
    # Keep integration tests focused on the simulation; no background SMTP
    # thread should be started by threshold crossings.
    import email_notifications
    monkeypatch.setattr(email_notifications, "check_and_send_threshold_alert", lambda **kwargs: None)
    email_notifications._alert_state.clear()
    for name in ["fetch_records","get_engine","update_records","insert_records",
                 "download_file","get_alert_thresholds"]:
        monkeypatch.setattr(sim.db, name, getattr(fake, name))
    for c in (sim._MODEL_CACHE, sim._MODEL_VERSION_CACHE, sim._SCALER_CACHE,
              sim._CLUSTER_CACHE, sim._BIAS_CACHE, sim._SENSOR_BUFFER):
        c.clear()
    # Exercise SHAP output at least once without running the expensive
    # explainer on every integration-test prediction.
    monkeypatch.setattr(sim, "SHAP_INTERVAL", 15)
    return fake

def make_cycles(n=60):
    rng = np.random.default_rng(0)
    return [{"cycle": i+1, "sensors": {c: float(rng.normal()) for c in sim.SENSOR_COLS}}
            for i in range(n)]

def run_storage_loop(tmp_path, env, monkeypatch, cycles, engine_id="e1", model_type="FD001",
                     stop_event=None, clock=None):
    """Run the simulation using cycle JSON returned by the fake Supabase Storage API."""
    import storage_utils
    storage_path = f"{model_type}/engine_{engine_id}.json"
    env.storage_files[storage_path] = json.dumps(cycles).encode("utf-8")
    monkeypatch.setattr(storage_utils, "_get_supabase_admin", lambda: env)
    monkeypatch.setattr(storage_utils, "_CACHE_DIR", tmp_path / "storage-cache")
    missing_local_path = tmp_path / "engines" / model_type / f"engine_{engine_id}.json"
    assert not missing_local_path.exists()
    sim._simulation_loop(engine_id, str(missing_local_path), model_type, env,
                         stop_event or threading.Event(), clock or FakeClock())

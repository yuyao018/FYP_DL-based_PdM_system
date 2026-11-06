import engine_simulation_manager as sim
from conftest import make_h5
from conftest import Resp


def test_active_model_version_is_loaded_from_database_and_cached(env, monkeypatch):
    requested = []
    original_download = sim.db.download_file

    def track_download(client, bucket, path):
        requested.append((bucket, path))
        return original_download(client, bucket, path)

    monkeypatch.setattr(sim.db, "download_file", track_download)
    first = sim._load_model("FD001", supabase=env)
    again = sim._load_model("FD001", supabase=env)

    assert first is not None and again is first
    assert requested == [("models", "FD001/v1.h5")]
    assert sim._MODEL_VERSION_CACHE["FD001"] == "v1"


def test_model_reload_picks_up_new_active_version(env, monkeypatch):
    first = sim._load_model("FD001", supabase=env)
    env.active_model_id = "v2"
    env.model_bytes = make_h5()
    requested = []
    original_download = sim.db.download_file

    def track_download(client, bucket, path):
        requested.append(path)
        return original_download(client, bucket, path)

    monkeypatch.setattr(sim.db, "download_file", track_download)
    reloaded = sim.reload_model("FD001", supabase=env)

    assert reloaded is not None and reloaded is not first
    assert requested == ["FD001/v2.h5"]
    assert sim._MODEL_VERSION_CACHE["FD001"] == "v2"


def test_ambiguous_active_models_are_rejected(env, monkeypatch):
    original_fetch = sim.db.fetch_records

    def two_active_models(client, table, cols, **kwargs):
        if table == "model_versions":
            return Resp([{"id": "v1"}, {"id": "v2"}])
        return original_fetch(client, table, cols, **kwargs)

    monkeypatch.setattr(sim.db, "fetch_records", two_active_models)
    assert sim._load_model("FD001", supabase=env) is None


def test_unavailable_model_storage_does_not_return_a_model(env, monkeypatch):
    monkeypatch.setattr(sim.db, "download_file", lambda *a: (_ for _ in ()).throw(RuntimeError("storage down")))
    assert sim.reload_model("FD001", supabase=env) is None

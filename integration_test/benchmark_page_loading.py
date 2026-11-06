"""Controlled page-construction benchmark; no live accounts or database writes.

Each simulated cloud read takes 200ms. This does not measure a real connection
or browser rendering and must not be treated as a production latency guarantee.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import contextlib
import io
import time
from types import SimpleNamespace
from unittest.mock import patch
from assets import database_integration as db
import engine_management
import dashboard
import overview
import user_management

engine = {"id": "e1", "engine_id": 1, "responsible_by": "u1", "condition_status": "healthy",
          "model_type": "FD001", "created_at": "2026-10-29", "is_deleted": True}
user = {"id": "u1", "username": "user", "first_name": "Test", "last_name": "User",
        "role": "user", "status": "active", "is_deleted": True}
def read(client, table, columns="*", **kwargs):
    time.sleep(.2)
    rows = {"engines": [engine], "users": [user],
            "alert_thresholds": [{"warning_threshold": 50, "critical_threshold": 30}],
            "rul_predictions": [{"engine_id": "e1", "predicted_rul": 80, "cycle": 1}]}.get(table, [])
    return SimpleNamespace(data=(rows[0] if rows else {}) if kwargs.get("single") else rows)

pages = {
    "Engine Management": lambda: engine_management.create_engine_management_layout(object(), org_id="org"),
    "Dashboard (admin, charts load separately)": lambda: dashboard.create_dashboard_layout(object(), org_id="org", role="admin"),
    "Engine Overview": lambda: overview.create_overview_layout(object(), engine_db_id="e1"),
    "User Management": lambda: user_management.create_user_management_layout(object(), org_id="org"),
}
with patch.object(db, "fetch_records", side_effect=read):
    for name, build in pages.items():
        started = time.perf_counter()
        with contextlib.redirect_stdout(io.StringIO()):
            build()
        # Add one 200ms read for the live route permission check.
        elapsed = time.perf_counter() - started + .2
        print(f"{name}: {elapsed:.2f}s (includes simulated 200ms permission check)")

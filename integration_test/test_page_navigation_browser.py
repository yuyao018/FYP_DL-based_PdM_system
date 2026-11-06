"""Verify sidebar navigation keeps the document and renders with simulated cloud latency."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch
import dash
from dash import dcc, html, Input, Output
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server, WSGIRequestHandler
from assets import database_integration as db
import engine_management
import user_management
import dashboard
import auth_security

class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass

app = dash.Dash(__name__, assets_folder=str(Path(__file__).resolve().parents[1] / 'assets'), suppress_callback_exceptions=True)
app.layout = html.Div([dcc.Location(id='url', refresh=False), html.Div(id='page-content')])
with patch.object(auth_security, 'require_trusted_role', return_value={'organization_id':'org'}):
    dashboard.register_dashboard_callbacks(app, supabase=object())
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def route(path):
    time.sleep(.2)  # Simulated live permission check.
    if path == '/dashboard':
        return dashboard.create_dashboard_layout(object(), org_id='org', role='admin')
    if path == '/user-management':
        return user_management.create_user_management_layout(object(), org_id='org')
    return engine_management.create_engine_management_layout(object(), org_id='org')

def read(client, table, columns='*', **kwargs):
    time.sleep(.2)
    rows = {
        'engines': [{'id':'e1', 'engine_id':1, 'condition_status':'healthy', 'model_type':'FD001', 'is_deleted':True}],
        'users': [{'id':'u1', 'username':'test_user', 'first_name':'Test', 'last_name':'User', 'role':'user', 'status':'active', 'is_deleted':True}],
        'alert_thresholds': [{'warning_threshold':50, 'critical_threshold':30}],
        'rul_predictions': [{'engine_id':'e1', 'predicted_rul':80}],
    }.get(table, [])
    return SimpleNamespace(data=rows)

server = make_server('127.0.0.1', 0, app.server, threaded=True, request_handler=QuietHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with patch.object(db, 'fetch_records', side_effect=read), sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'http://127.0.0.1:{server.server_port}/engine-management')
        page.get_by_role('heading', name='ENGINE MANAGEMENT', exact=True).wait_for()
        page.evaluate('window.__navigationSentinel = 12345')
        for label, heading in [('User Management', 'USER MANAGEMENT'), ('Engine Management', 'ENGINE MANAGEMENT')]:
            started = time.perf_counter()
            page.locator('#sidebar').get_by_text(label, exact=True).click()
            page.get_by_role('heading', name=heading, exact=True).wait_for()
            elapsed = time.perf_counter() - started
            assert page.evaluate('window.__navigationSentinel') == 12345
            assert page.evaluate("performance.getEntriesByType('navigation').length") == 1
            print(f'PASS: {label}: {elapsed:.2f}s; document preserved', flush=True)
        started = time.perf_counter()
        page.locator('#sidebar').get_by_text('Dashboard', exact=True).click()
        page.locator('#dashboard-total-count').wait_for(state='visible')
        print(f'PASS: Dashboard: {time.perf_counter()-started:.2f}s; charts load separately', flush=True)
        assert page.evaluate('window.__navigationSentinel') == 12345
        page.locator('#admin-alert-trend .js-plotly-plot').wait_for(state='visible')
        print('PASS: deferred dashboard charts finish loading', flush=True)
        browser.close()
finally:
    server.shutdown()

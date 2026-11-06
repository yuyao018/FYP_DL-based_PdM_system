"""Exercise the real browser transition from saving to success and auto-close."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import threading
from types import SimpleNamespace
from unittest.mock import patch

import dash
from dash import html
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server
import engine_management as management

app = dash.Dash(__name__, assets_folder=str(Path(__file__).resolve().parents[1] / 'assets'))
app.layout = html.Div(management.build_engine_management_body([
    {'id': 'a', 'engine_id': 1, 'condition_status': 'healthy', 'is_deleted': True}
]))
management.register_engine_management_callbacks(app, supabase=object())
server = make_server('127.0.0.1', 0, app.server, threaded=True)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with patch.object(management, 'require_trusted_role', return_value={'organization_id': 'org'}), \
         patch.object(management.db, 'update_records', return_value=SimpleNamespace(data=[{'id': 'a'}])), \
         sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'http://127.0.0.1:{server.server_port}')
        page.get_by_role('button', name='Remove', exact=True).click()
        toast = page.locator('#engine-action-status')
        toast.get_by_text('Engine removed.', exact=True).wait_for(state='visible')
        toast.wait_for(state='hidden', timeout=6000)
        print('PASS: removal success notification auto-dismisses')
        page.get_by_role('button', name='Restore', exact=True).click()
        toast.get_by_text('Engine restored.', exact=True).wait_for(state='visible')
        toast.wait_for(state='hidden', timeout=6000)
        print('PASS: next success notification restarts timer and auto-dismisses')
        # A new pending message must cancel the previous success timer.
        page.evaluate("window.dash_clientside.set_props('engine-action-status', {children:'Success', is_open:true}); window.dash_clientside.set_props('engine-action-dismiss-delay', {data:100})")
        page.wait_for_timeout(30)
        page.evaluate("window.dash_clientside.set_props('engine-action-status', {children:'Saving', is_open:true}); window.dash_clientside.set_props('engine-action-dismiss-delay', {data:null})")
        page.wait_for_timeout(200)
        assert toast.is_visible()
        print('PASS: pending notification cancels stale dismissal')
        page.evaluate("window.dash_clientside.set_props('engine-action-status', {children:'Error', duration:null, is_open:true})")
        page.wait_for_timeout(3700)
        assert toast.is_visible()
        print('PASS: error remains visible')
        browser.close()
finally:
    server.shutdown()

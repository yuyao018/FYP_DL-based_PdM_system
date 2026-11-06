"""Browser test: destination renders locally despite slow protected page reads."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import threading
import time
import dash
from dash import dcc, html
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server, WSGIRequestHandler
from assets.components import build_admin_sidebar, build_topbar
from page_navigation import navigation_components, register_page_navigation

class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass

app = dash.Dash(__name__, assets_folder=str(Path(__file__).resolve().parents[1] / 'assets'), suppress_callback_exceptions=True)
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', data={'user_id':'test-admin', 'role':'admin', 'organization_id':'test-org'}),
    html.Div(id='page-content'), *navigation_components(),
])
def slow_page(path, search, session):
    time.sleep(3 if path == '/engine-management' else 1.5)
    return html.Div([
        build_topbar(), build_admin_sidebar(),
        html.Div(id='page-data-ready', children=path),
    ])
register_page_navigation(app, slow_page)
server = make_server('127.0.0.1', 0, app.server, threaded=True, request_handler=QuietHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://127.0.0.1:{server.server_port}/user-management')
        page.locator('#page-data-ready').wait_for(timeout=15000)
        page.evaluate('window.__keepDocument = 123')
        start = time.perf_counter()
        page.locator('#sidebar').get_by_text('Engine Management', exact=True).click()
        page.locator('.page-loading-spinner').wait_for(state='visible')
        elapsed = time.perf_counter()-start
        assert elapsed < 1, elapsed
        assert page.locator('.navigation-skeleton-card').count() == 0
        assert page.get_by_text('Loading live data…', exact=True).count() == 0
        assert page.locator('.page-loading-spinner').evaluate("el => getComputedStyle(el).animationName") == 'page-loading-spin'
        assert page.locator('#page-data-ready').count() == 0
        print(f'PASS: circular loader visible in {elapsed:.2f}s with a 3s backend delay', flush=True)
        page.go_back()
        page.wait_for_url('**/user-management')
        page.locator('.page-loading-spinner').wait_for(state='visible')
        page.locator('#page-data-ready').get_by_text('/user-management', exact=True).wait_for()
        page.wait_for_timeout(2000)
        assert page.locator('#page-data-ready').inner_text() == '/user-management'
        assert page.evaluate('window.__keepDocument') == 123
        assert page.locator('.page-loading-spinner').count() == 0
        assert not errors, errors
        print('PASS: late engine response cannot replace the latest user page; document preserved', flush=True)
        browser.close()
finally:
    server.shutdown()

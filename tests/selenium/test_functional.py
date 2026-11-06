"""Browser checks mapped to the sixteen functional-testing checklist areas.

Account credentials come only from environment variables. Every test has a fresh
browser; skipped tests explicitly describe missing fixtures. Use a test database.
"""
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException


class UI:
    def __init__(self, browser, base_url):
        self.d = browser
        self.base = base_url.rstrip("/")
        self.wait = WebDriverWait(browser, float(os.getenv("SELENIUM_TIMEOUT", "30")))

    def go(self, route):
        self.d.get(self.base + route)

    def visible(self, selector):
        return self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))

    def click(self, selector):
        # Route changes can leave the app's full-screen loading layer above
        # otherwise visible/clickable controls for a short time.
        loader = (By.CSS_SELECTOR, ".page-loading-screen")
        self.wait.until(EC.invisibility_of_element_located(loader))
        element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        self.d.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        try:
            element.click()
        except ElementClickInterceptedException:
            # The loader may have appeared between the wait and the click.
            self.wait.until(EC.invisibility_of_element_located(loader))
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector))).click()

    def fill(self, selector, value):
        element = self.visible(selector)
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(value)
        element.send_keys(Keys.TAB)

    def text(self, selector):
        return self.visible(selector).text

    def contains(self, selector, text):
        self.wait.until(lambda _: text.lower() in self.text(selector).lower())

    def dropdown(self, selector, label):
        self.click(selector)
        self.wait.until(EC.element_to_be_clickable((By.XPATH,
            f"//*[@role='option' or contains(@class,'Select-option') "
            f"or contains(@class,'dash-dropdown-option') "
            f"or contains(@class,'dash-options-list-option')]"
            f"[normalize-space(.)='{label}']"))).click()

    def chart(self, chart_id):
        self.visible(f"#{chart_id}.js-plotly-plot, #{chart_id} .js-plotly-plot")
        self.wait.until(lambda d: d.execute_script(
            "const host=document.getElementById(arguments[0]);"
            "const p=host && (host.matches('.js-plotly-plot') ? host : host.querySelector('.js-plotly-plot'));"
            "return !!(p && p._fullLayout && Array.isArray(p.data));", chart_id))

    def login(self, role="user", prefix=None, allow_change=False):
        prefix = prefix or role.upper()
        username = os.getenv(f"SELENIUM_{prefix}_USERNAME")
        password = os.getenv(f"SELENIUM_{prefix}_PASSWORD")
        if not username or not password:
            pytest.skip(f"Set SELENIUM_{prefix}_USERNAME and SELENIUM_{prefix}_PASSWORD")
        dev = role == "developer"
        self.go("/dev-login" if dev else "/")
        if role == "admin":
            self.click("#role-admin")
        self.fill("#dev-username-input" if dev else "#username-input", username)
        self.fill("#dev-password-input" if dev else "#password-input", password)
        self.click("#dev-signin-btn" if dev else "#signin-btn")
        expected = "/change-password" if allow_change else ("/dev-dashboard" if dev else "/dashboard")
        try:
            self.wait.until(lambda d: urlparse(d.current_url).path == expected)
        except TimeoutException as exc:
            status_selector = "#dev-login-status" if dev else "#login-status"
            status_elements = self.d.find_elements(By.CSS_SELECTOR, status_selector)
            status = status_elements[0].text.strip() if status_elements else "(login status unavailable)"
            actual_path = urlparse(self.d.current_url).path
            raise AssertionError(
                f"{role} login did not reach {expected}; current page is {actual_path}; "
                f"login message: {status}"
            ) from exc

    def expect_role_login_rejected(self, account_role, login_mode):
        """Try an account through the wrong role entry point and expect rejection."""
        prefix = account_role.upper()
        username = os.getenv(f"SELENIUM_{prefix}_USERNAME")
        password = os.getenv(f"SELENIUM_{prefix}_PASSWORD")
        if not username or not password:
            pytest.skip(f"Set SELENIUM_{prefix}_USERNAME and SELENIUM_{prefix}_PASSWORD")
        developer_entry = login_mode == "developer"
        self.go("/dev-login" if developer_entry else "/")
        if login_mode == "admin":
            self.click("#role-admin")
        self.fill("#dev-username-input" if developer_entry else "#username-input", username)
        self.fill("#dev-password-input" if developer_entry else "#password-input", password)
        self.click("#dev-signin-btn" if developer_entry else "#signin-btn")
        status = "#dev-login-status" if developer_entry else "#login-status"
        self.contains(status, "Invalid username or password")
        assert urlparse(self.d.current_url).path == ("/dev-login" if developer_entry else "/")

    def engine(self, page):
        engine = os.getenv("SELENIUM_ENGINE_ID")
        if not engine:
            self.go("/dashboard")
            self.visible("#engines-grid")
            links = self.d.find_elements(By.CSS_SELECTOR, 'a[href^="/overview/"]')
            if not links:
                try:
                    self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, 'a[href^="/overview/"]'))
                except TimeoutException:
                    pytest.skip("Seed an assigned engine or set SELENIUM_ENGINE_ID to its database UUID")
                links = self.d.find_elements(By.CSS_SELECTOR, 'a[href^="/overview/"]')
            engine = urlparse(links[0].get_attribute("href")).path.split("/")[-1]
        self.go(f"/{page}/{engine}")
        return engine


@pytest.fixture(scope="session")
def running_app(request):
    url = request.config.getoption("--base-url")
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            assert response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        pytest.skip(f"Application unavailable at {url}: {exc}. Start the app or supply --base-url.")
    return url


@pytest.fixture
def ui(running_app, request):
    name = request.node.name
    prefix = None
    if name.startswith("test_01_valid_login"):
        prefix = request.node.callspec.params["role"].upper()
    elif name.startswith("test_01_rbac"):
        prefix = request.node.callspec.params["account_role"].upper()
    elif name.startswith("test_02"):
        prefix = "FIRST_LOGIN"
    elif name.startswith(("test_11", "test_12", "test_13")):
        prefix = "ADMIN"
    elif name.startswith("test_14"):
        prefix = "DEVELOPER"
    elif not name.startswith(("test_01_login_", "test_16_anonymous")):
        prefix = "USER"
    if prefix and not all(os.getenv(f"SELENIUM_{prefix}_{field}") for field in ("USERNAME", "PASSWORD")):
        pytest.skip(f"Set SELENIUM_{prefix}_USERNAME and SELENIUM_{prefix}_PASSWORD")
    browser = request.getfixturevalue("browser")
    return UI(browser, running_app)


def test_01_login_empty_fields(ui):
    ui.go("/")
    ui.click("#signin-btn")
    ui.contains("#login-status", "Please fill in your username and password")
    assert urlparse(ui.d.current_url).path == "/"


def test_01_login_invalid_credentials(ui):
    ui.go("/")
    ui.fill("#username-input", "selenium_nonexistent_account")
    ui.fill("#password-input", "InvalidPassword123!")
    ui.click("#signin-btn")
    ui.contains("#login-status", "Invalid username or password")
    assert urlparse(ui.d.current_url).path == "/"


@pytest.mark.parametrize("role", ["user", "admin", "developer"])
def test_01_valid_login(ui, role):
    ui.login(role)


@pytest.mark.parametrize("account_role,login_mode", [
    ("user", "admin"),
    ("user", "developer"),
    ("admin", "user"),
    ("admin", "developer"),
    ("developer", "user"),
    ("developer", "admin"),
])
def test_01_rbac_rejects_wrong_login_role(ui, account_role, login_mode):
    ui.expect_role_login_rejected(account_role, login_mode)


def test_01_logout(ui):
    """Logout returns to login and the dashboard stays blocked after refresh."""
    ui.login()
    ui.click("#user-menu-trigger")
    ui.click("#logout-btn")
    ui.wait.until(lambda d: urlparse(d.current_url).path == "/",
                  message="Logout did not return to the login URL")
    ui.visible("#signin-btn")
    ui.wait.until(EC.invisibility_of_element_located((By.ID, "user-menu-trigger")))
    ui.go("/dashboard")
    # The route guard renders the login form at this URL; it need not redirect.
    ui.visible("#signin-btn")
    ui.wait.until(EC.invisibility_of_element_located((By.ID, "engines-grid")))
    ui.d.refresh()
    ui.visible("#signin-btn")
    ui.wait.until(EC.invisibility_of_element_located((By.ID, "engines-grid")))


def test_02_password_validation(ui):
    ui.login(prefix="FIRST_LOGIN", allow_change=True)
    ui.fill("#change-pw-new", "weak")
    ui.fill("#change-pw-confirm", "different")
    ui.click("#change-pw-btn")
    ui.wait.until(lambda _: bool(ui.text("#change-pw-status")))
    assert urlparse(ui.d.current_url).path == "/change-password"


def test_03_dashboard_summary_and_filter(ui):
    ui.login()
    counts = [int(ui.text(f"#dashboard-{name}-count")) for name in ("total", "healthy", "warning", "critical")]
    assert counts[0] == sum(counts[1:]), f"Inconsistent summary counts: {counts}"
    ui.visible("#engines-grid")
    ui.dropdown("#engine-status-filter", "Healthy")
    ui.wait.until(lambda _: all("healthy" in e.text.lower() for e in ui.d.find_elements(By.CSS_SELECTOR, '[id*="engine-card"]')))


def test_04_navigation_and_refresh(ui):
    ui.login()
    engine = ui.engine("overview")
    ui.click(f'a[href="/sensor-trends/{engine}"]')
    ui.visible("#sensor-chart")
    ui.d.refresh()
    ui.visible("#sensor-chart")
    ui.d.back()
    ui.visible("#rul-line-chart")
    ui.d.forward()
    ui.visible("#sensor-chart")
    ui.go("/selenium-page-does-not-exist")
    ui.contains("body", "Page not found")


def test_05_engine_overview(ui):
    ui.login()
    ui.engine("overview")
    for selector in ("#engine-status-badge", "#rul-value-display", "#degradation-display", "#engine-3d-iframe"):
        ui.visible(selector)
    for chart in ("rul-line-chart", "shap-chart", "sensor-mini-all"):
        ui.chart(chart)


def test_06_sensor_selection_and_normalization(ui):
    ui.login()
    ui.engine("sensor-trends")
    ui.chart("sensor-chart")
    ui.click("#select-all-btn")
    ui.contains("#select-all-btn", "Deselect all")
    ui.wait.until(lambda d: all(e.is_selected() for e in d.find_elements(By.CSS_SELECTOR, '[id*="sensor-check"] input')))
    before = ui.visible("#toggle-knob").get_attribute("style")
    ui.click("#normalize-toggle")
    ui.wait.until(lambda _: ui.visible("#toggle-knob").get_attribute("style") != before)
    ui.click("#select-all-btn")
    ui.contains("#select-all-btn", "Select all")
    ui.wait.until(lambda d: not any(e.is_selected() for e in d.find_elements(By.CSS_SELECTOR, '[id*="sensor-check"] input')))


def test_07_degradation_charts_and_filters(ui):
    ui.login()
    ui.engine("degradation-analysis")
    for chart in ("da-top-drivers-chart", "da-shap-waterfall", "da-shap-trend"):
        ui.chart(chart)
    ui.visible("#da-fault-mode-label")
    ui.visible("#da-confidence-value")
    for selector in ("#da-filter-5", "#da-filter-10", "#da-filter-all", "#da-trend-filter-10", "#da-trend-filter-all"):
        ui.click(selector)
    ui.visible("#da-cycle-selector")


def test_07_ai_explanation(ui):
    ui.login()
    ui.engine("degradation-analysis")
    ui.click("#da-generate-btn")
    WebDriverWait(ui.d, 120).until(lambda _: bool(ui.text("#da-llm-timestamp")))
    assert len(ui.text("#da-llm-explanation").strip()) > 40


def test_08_alert_search_and_filters(ui):
    ui.login()
    ui.engine("alert-log")
    ui.visible("#alert-table-body")
    ui.dropdown("#alert-severity-filter", "Critical")
    ui.fill("#alert-search-input", "selenium_no_matching_alert_918273")
    ui.contains("#alert-table-body", "No alerts matching filter")
    ui.fill("#alert-search-input", "")
    ui.visible("#alert-status-filter")


def test_09_calendar_navigation_and_modal(ui):
    ui.login()
    ui.engine("schedule-maintenance")
    label = ui.text("#sm-week-label")
    ui.click("#sm-nav-next")
    ui.wait.until(lambda _: ui.text("#sm-week-label") != label)
    ui.click("#sm-nav-today")
    ui.wait.until(lambda _: ui.text("#sm-week-label") == label)
    ui.click("#sm-new-btn")
    ui.visible("#sm-modal-overlay")
    for selector in ("#sm-modal-date", "#sm-modal-start-time", "#sm-modal-end-time"):
        ui.visible(selector)
    ui.click("#sm-modal-cancel")
    ui.wait.until(EC.invisibility_of_element_located((By.ID, "sm-modal-overlay")))


def test_10_completed_report_and_pdf(ui):
    ui.login()
    if not os.getenv("SELENIUM_COMPLETED_REPORT_ENGINE_ID"):
        pytest.skip("Set SELENIUM_COMPLETED_REPORT_ENGINE_ID to an engine whose current action is View Report")
    ui.go("/alert-log/" + os.environ["SELENIUM_COMPLETED_REPORT_ENGINE_ID"])
    ui.contains("#al-engine-action-btn", "View Report")
    ui.click("#al-engine-action-btn")
    ui.visible("#al-report-modal-overlay")
    ui.click("#al-report-export-pdf")
    ui.wait.until(lambda _: any(p.stat().st_size > 0 for p in ui.d.download_directory.glob("*.pdf")))
    pdf = next(ui.d.download_directory.glob("*.pdf"))
    assert pdf.read_bytes().startswith(b"%PDF")


def test_11_engine_form_inputs_and_buttons(ui):
    ui.login("admin")
    ui.go("/engine-management")
    ui.visible("#engines-table-body")
    ui.click("#add-engine-btn")
    for selector, value in (("#new-engine-id", "2052"),
                            ("#new-engine-location", "Selenium Test Hangar"),
                            ("#new-engine-notes", "Form input check only")):
        ui.fill(selector, value)
        assert ui.visible(selector).get_attribute("value") == value
    # A four-digit engine ID now infers its dataset automatically.
    ui.contains("#new-engine-model", "FD002")
    ui.dropdown("#new-engine-model", "FD002")
    ui.contains("#new-engine-model", "FD002")
    ui.click("#new-engine-assign-to")
    ui.d.switch_to.active_element.send_keys(Keys.ESCAPE)
    # Check readiness without invoking the database-writing callback.
    ui.wait.until(EC.element_to_be_clickable((By.ID, "create-engine-btn")))
    assert urlparse(ui.d.current_url).path == "/add-engine"
    ui.click("#cancel-add-engine-btn")
    ui.visible("#engines-table-body")


def test_12_user_form_inputs_and_buttons(ui):
    ui.login("admin")
    ui.go("/user-management")
    ui.visible("#users-table-body")
    ui.click("#add-user-btn")
    for selector, value in (("#new-user-first-name", "Selenium"),
                            ("#new-user-last-name", "Tester"),
                            ("#new-user-email", "selenium@example.test"),
                            ("#new-user-department", "Test Department")):
        ui.fill(selector, value)
        assert ui.visible(selector).get_attribute("value") == value
    # Generated credentials are intentionally disabled on the new-user form.
    assert not ui.visible("#new-user-username").is_enabled()
    assert not ui.visible("#new-user-password").is_enabled()
    ui.wait.until(EC.element_to_be_clickable((By.ID, "create-user-btn")))
    assert urlparse(ui.d.current_url).path == "/add-user"
    ui.click("#cancel-add-user-btn")
    ui.visible("#users-table-body")


def test_13_threshold_preview(ui):
    ui.login("admin")
    ui.go("/alert-thresholds")
    before = ui.text("#status-preview-container")
    warn = float(ui.visible("#warn-threshold-input-display").get_attribute("value"))
    ui.fill("#warn-threshold-input-display", str(int(warn + 1)))
    ui.wait.until(lambda _: ui.text("#status-preview-container") != before)
    ui.visible("#threshold-bar-container")


def test_14_model_upload_invalid_file(ui):
    ui.login("developer")
    ui.go("/model-upload")
    ui.visible("#model-type-dropdown")
    ui.visible("#active-model-panel-container")
    assert not ui.visible("#deploy-model-btn").is_enabled()
    invalid = ui.d.download_directory / "invalid_model.txt"
    invalid.write_text("This is not a model.")
    ui.d.find_element(By.CSS_SELECTOR, '#model-upload-dropzone input[type="file"]').send_keys(str(invalid))
    ui.contains("#staged-file-container", "Only .h5 files are accepted")
    assert not ui.visible("#deploy-model-btn").is_enabled()


def test_15_simulation_controls_visible(ui):
    ui.login()
    ui.engine("overview")
    ui.visible("#simulation-widget")
    ui.click("#simulation-widget-details summary")
    for selector in ("#simulation-state", "#simulation-speed", "#simulation-apply", "#simulation-pause", "#simulation-resume", "#simulation-auto"):
        ui.visible(selector)


@pytest.mark.parametrize("route", ["/dashboard", "/user-management", "/engine-management", "/alert-thresholds", "/model-upload"])
def test_16_anonymous_access_blocked(ui, route):
    ui.go(route)
    ui.wait.until(lambda d: d.find_elements(By.ID, "signin-btn") or "access denied" in d.find_element(By.TAG_NAME, "body").text.lower())


def test_16_user_cannot_access_developer_models(ui):
    ui.login()
    ui.go("/model-upload")
    ui.contains("body", "Access Denied")

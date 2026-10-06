import secrets
import string
import threading
import unicodedata
from html import escape

from assets import database_integration as db
from email_notifications import _cfg, _send_email

_creation_lock = threading.Lock()


def username_prefix(first_name, last_name):
    def letters(name):
        normalized = unicodedata.normalize("NFKD", name or "")
        return "".join(c for c in normalized.upper() if c in string.ascii_uppercase)
    first, last = letters(first_name), letters(last_name)
    if not first or not last:
        raise ValueError("Please include Latin letters in both names to generate the username.")
    # Repeat a single-letter name so the prefix always contains four name letters.
    return (first * 2)[:2] + (last * 2)[:2]


def generate_username(client, first_name, last_name):
    prefix = username_prefix(first_name, last_name)
    candidates = [f"{prefix}{n:02d}" for n in range(100)]
    response = db.fetch_records(client, "users", "username",
                                filters=[("in_", "username", candidates)])
    used = {row["username"] for row in (response.data or [])}
    available = [name for name in candidates if name not in used]
    if not available:
        raise ValueError("All 100 usernames for these initials are taken. Please use a fuller or alternative name.")
    return secrets.choice(available)


def generate_password():
    groups = (string.ascii_uppercase, string.ascii_lowercase, string.digits, "!@#$%&*?-_")
    chars = [secrets.choice(group) for group in groups]
    chars.extend(secrets.choice("".join(groups)) for _ in range(8))
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def send_welcome_email(email, first_name, username, password):
    url = _cfg("DASHBOARD_URL", "https://fyp-dl-based-pdm-system.onrender.com").rstrip("/") + "/"
    body = f"""<html><body style="font-family:Arial,sans-serif;line-height:1.6">
    <h2>Your monitoring system account</h2>
    <p>Hello {escape(first_name)},</p>
    <p>Your account is ready. Use these temporary credentials for your first login:</p>
    <p><strong>Username:</strong> {escape(username)}<br>
    <strong>Temporary password:</strong> {escape(password)}</p>
    <p>You must change your password before accessing the system.</p>
    <p><a href="{escape(url, quote=True)}">Log in to your account</a></p>
    <p>Keep these credentials private. This is an automated message.</p>
    </body></html>"""
    return _send_email("Your monitoring system account — first login", body,
                       recipients_override=[email])


def create_user_with_credentials(client, admin_client, *, first_name, last_name,
                                 email, department, role, organization_id):
    """Return (username, delivered); no temporary password is returned to the UI."""
    if not _cfg("EMAIL_SENDER") or not (_cfg("RESEND_API_KEY") or _cfg("EMAIL_PASSWORD")):
        raise ValueError("Configure outgoing email before creating accounts.")
    # Serializes allocation in this process; the database username unique constraint
    # remains the authority for concurrent app instances.
    with _creation_lock:
        username = generate_username(admin_client, first_name, last_name)
        password = generate_password()
        response = admin_client.auth.admin.create_user({
            "email": email, "password": password, "email_confirm": True,
            "user_metadata": {"must_change_password": True},
        })
        user_id = response.user.id
        try:
            db.insert_records(client, "users", {
                "id": user_id, "username": username,
                "first_name": first_name, "last_name": last_name,
                "email_address": email, "department": department,
                "role": role, "organization_id": organization_id,
                "status": "active", "last_login_at": None,
                "created_at": "now()",
            })
        except Exception:
            # This auth account was created by this operation; no profile was saved.
            admin_client.auth.admin.delete_user(user_id)
            raise
    try:
        delivered = send_welcome_email(email, first_name, username, password)
    except Exception:
        delivered = False
    return username, delivered

"""Supabase Auth backed sessions for Dash callbacks.

Auth credentials and profile claims stay in Flask-Session's server-side store.
Production must set a long random FLASK_SECRET_KEY and serve HTTPS.
"""
from __future__ import annotations

import base64
import json
import os
import time
from typing import Any
import bcrypt

from flask import g, session as flask_session
from supabase import create_client

from assets import database_integration as db


def _decode_exp(token: str) -> int:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return int(json.loads(base64.urlsafe_b64decode(payload)).get("exp", 0))
    except Exception:
        return 0


def configure_flask_session(server) -> None:
    secret = os.getenv("FLASK_SECRET_KEY")
    if not secret:
        raise RuntimeError("Set FLASK_SECRET_KEY to a long random value before starting the app")
    server.secret_key = secret
    try:
        from flask_session import Session
    except ImportError as exc:
        raise RuntimeError("Install Flask-Session and configure a server-side session store") from exc
    session_type = os.getenv("FLASK_SESSION_TYPE", "filesystem").lower()
    session_config = {
        "SESSION_TYPE": session_type,
        "SESSION_PERMANENT": True,
        "SESSION_USE_SIGNER": True,
        "SESSION_ID_LENGTH": 32,
        "SESSION_SERIALIZATION_FORMAT": "json",
    }
    if session_type == "redis":
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise RuntimeError("Set REDIS_URL when FLASK_SESSION_TYPE=redis")
        from redis import Redis
        session_config["SESSION_REDIS"] = Redis.from_url(redis_url)
    elif session_type == "filesystem":
        if os.getenv("APP_ENV", "development").lower() == "production":
            raise RuntimeError("Use Redis sessions in production; local filesystem sessions are single-instance only")
        session_config["SESSION_FILE_DIR"] = os.getenv("FLASK_SESSION_FILE_DIR", ".flask_session")
    else:
        raise RuntimeError("FLASK_SESSION_TYPE must be redis or filesystem")
    server.config.update(session_config)
    Session(server)
    server.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "true").lower() not in {"0", "false", "no"},
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 7,
    )


def _configured_supabase_client():
    url, key = os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError("Supabase URL and anon key must be configured")
    return create_client(url, key)


def authenticate_username(username: str, password: str, selected_role: str,
                          admin_client, supabase_url: str, anon_key: str) -> dict[str, Any]:
    """Resolve username privately, authenticate with Auth, then bind profile ID."""
    found = db.fetch_records(
        admin_client, "users",
        "id,username,email_address,first_name,last_name,role,organization_id,status,is_deleted,last_login_at",
        filters=[("eq", "username", username)], limit=2,
    ).data or []
    if len(found) != 1:
        raise ValueError("Invalid username or password")
    profile = found[0]
    # `status` is also used for online/offline presence and is inactive after
    # normal logout, so it must not prevent a legitimate Auth sign-in.
    # Legacy schema convention: true means active; false means soft-deleted.
    if profile.get("is_deleted") is not True:
        raise ValueError("Invalid username or password")
    if (profile.get("role") or "user").lower() != (selected_role or "user").lower():
        raise ValueError("Invalid username or password")
    email = profile.get("email_address")
    if not email:
        raise ValueError("This account needs an email address before Auth login")

    # A new client per attempt prevents one user's Auth state leaking to another.
    if not supabase_url or not anon_key:
        raise RuntimeError("Supabase Auth is not configured")
    auth_client = create_client(supabase_url, anon_key)
    try:
        auth_response = auth_client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as auth_error:
        # One-time bridge for accounts created before Supabase Auth became the
        # source of password verification. Hash reads stay service-role-only;
        # successful verification updates Auth so later logins use Auth alone.
        try:
            legacy = db.fetch_records(admin_client, "users", "password_hash",
                                      filters=[("eq", "id", str(profile["id"]))], limit=1).data or []
            encoded_hash = (legacy[0].get("password_hash") if legacy else None) or ""
            if not encoded_hash or not bcrypt.checkpw(password.encode("utf-8"), encoded_hash.encode("utf-8")):
                raise ValueError("Invalid username or password") from auth_error
            admin_client.auth.admin.update_user_by_id(str(profile["id"]), {"password": password})
            auth_response = auth_client.auth.sign_in_with_password({"email": email, "password": password})
        except ValueError:
            raise
        except Exception as migration_error:
            raise ValueError("Invalid username or password") from migration_error
    auth_user = getattr(auth_response, "user", None)
    auth_session = getattr(auth_response, "session", None)
    if not auth_user or not auth_session or str(auth_user.id) != str(profile["id"]):
        raise ValueError("Invalid username or password")
    confirmed = admin_client.auth.admin.get_user_by_id(str(auth_user.id))
    confirmed_user = getattr(confirmed, "user", None)
    if not confirmed_user or str(confirmed_user.id) != str(profile["id"]):
        raise ValueError("Invalid username or password")

    auth_metadata = getattr(auth_user, "user_metadata", {}) or {}
    first_login = bool(auth_metadata.get("must_change_password"))
    # Auth has verified this identity; update status through the server-only client.
    fields = {"status": "active",
              "last_login_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    db.update_records(admin_client, "users", fields,
                      filters=[("eq", "id", str(auth_user.id))])

    flask_session.clear()
    flask_session.permanent = True
    flask_session["auth_access_token"] = auth_session.access_token
    flask_session["auth_user_metadata"] = getattr(auth_user, "user_metadata", {}) or {}
    flask_session["auth_refresh_token"] = auth_session.refresh_token
    flask_session["auth_expires_at"] = int(getattr(auth_session, "expires_at", 0) or _decode_exp(auth_session.access_token))
    flask_session["auth_user_id"] = str(auth_user.id)
    flask_session["auth_role"] = (profile.get("role") or "user").lower()
    flask_session["auth_org_id"] = str(profile.get("organization_id") or "")
    flask_session["auth_must_change_password"] = first_login
    flask_session["auth_username"] = profile.get("username", username)
    flask_session["auth_first_name"] = profile.get("first_name", "")
    flask_session["auth_last_name"] = profile.get("last_name", "")
    # Harmless profile values for rendering only; authorization always uses the
    # signed server session and/or database RLS, never these browser values.
    return {
        "user_id": str(auth_user.id),
        "username": profile.get("username", username),
        "first_name": profile.get("first_name", ""),
        "last_name": profile.get("last_name", ""),
        "role": (profile.get("role") or "user").lower(),
        "organization_id": str(profile.get("organization_id") or ""),
        "must_change_password": first_login,
    }


def refresh_auth_session_if_needed() -> None:
    """Refresh the Supabase token before it expires; clear invalid sessions."""
    access = flask_session.get("auth_access_token")
    refresh = flask_session.get("auth_refresh_token")
    expires_at = int(flask_session.get("auth_expires_at") or 0)
    if not access or not refresh or expires_at > int(time.time()) + 90:
        return
    try:
        auth_client = _configured_supabase_client()
        refresh_response = auth_client.auth.set_session(access, refresh)
        refreshed = getattr(refresh_response, "session", None) or refresh_response
        refreshed_user = getattr(refresh_response, "user", None) or getattr(refreshed, "user", None)
        if not refreshed or not refreshed_user or str(refreshed_user.id) != flask_session.get("auth_user_id"):
            raise ValueError("Supabase Auth identity changed")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not service_key:
            raise ValueError("Server profile verification is unavailable")
        admin_client = create_client(os.getenv("SUPABASE_URL", ""), service_key)
        identity = admin_client.auth.admin.get_user_by_id(str(refreshed_user.id))
        if not getattr(identity, "user", None) or str(identity.user.id) != flask_session.get("auth_user_id"):
            raise ValueError("Unable to verify Supabase Auth identity")
        flask_session["auth_access_token"] = refreshed.access_token
        flask_session["auth_refresh_token"] = refreshed.refresh_token
        flask_session["auth_expires_at"] = int(getattr(refreshed, "expires_at", 0) or _decode_exp(refreshed.access_token))
        flask_session.modified = True
    except Exception:
        flask_session.clear()


def user_supabase_client():
    """Return a request-local anon-key client carrying this user's Auth JWT."""
    token = flask_session.get("auth_access_token")
    if not token:
        return None
    expires_at = int(flask_session.get("auth_expires_at") or 0)
    if expires_at <= int(time.time()):
        raise PermissionError("Supabase session expired")
    cached = getattr(g, "auth_supabase_client", None)
    if cached is not None:
        return cached
    client = _configured_supabase_client()
    # Bind Auth as well as PostgREST so password updates use this user's JWT.
    client.auth.set_session(token, flask_session["auth_refresh_token"])
    token = flask_session.get("auth_access_token")
    client.postgrest.auth(token)
    try:
        client.storage.set_auth(token)
    except AttributeError:
        pass
    g.auth_supabase_client = client
    return client


def trusted_profile() -> dict[str, Any] | None:
    """Return verified Flask session claims, never client-provided dcc.Store data."""
    cached = getattr(g, "trusted_auth_profile", None)
    if cached is not None:
        return dict(cached)
    user_id = flask_session.get("auth_user_id")
    if not user_id or not flask_session.get("auth_access_token"):
        return None
    if int(flask_session.get("auth_expires_at") or 0) <= int(time.time()):
        return None
    profile = {
        "user_id": user_id,
        "username": flask_session.get("auth_username", ""),
        "first_name": flask_session.get("auth_first_name", ""),
        "last_name": flask_session.get("auth_last_name", ""),
        "role": flask_session.get("auth_role", "user"),
        "organization_id": flask_session.get("auth_org_id", ""),
        "must_change_password": bool(flask_session.get("auth_must_change_password")),
        "user_metadata": flask_session.get("auth_user_metadata", {}),
    }
    admin_client = getattr(g, "auth_profile_admin", None)
    if admin_client is None:
        url, key = os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if url and key:
            admin_client = create_client(url, key)
            g.auth_profile_admin = admin_client
    if admin_client is None:
        return None
    rows = db.fetch_records(admin_client, "users", "id,role,organization_id,status,is_deleted",
                            filters=[("eq", "id", user_id)], limit=1).data or []
    if (len(rows) != 1 or rows[0].get("status") != "active" or rows[0].get("is_deleted") is not True):
        flask_session.clear()
        return None
    profile.update(role=(rows[0].get("role") or "user").lower(),
                   organization_id=str(rows[0].get("organization_id") or ""))
    flask_session["auth_role"] = profile["role"]
    flask_session["auth_org_id"] = profile["organization_id"]
    profile["must_change_password"] = bool(flask_session.get("auth_must_change_password"))
    g.trusted_auth_profile = dict(profile)
    return dict(profile)


class RequestSupabaseProxy:
    """Resolve DB calls against the JWT client for this HTTP request only."""
    def __getattr__(self, name):
        client = user_supabase_client()
        if client is None:
            # Anonymous requests remain anonymous; RLS/grants must deny data.
            client = _configured_supabase_client()
        return getattr(client, name)


def require_trusted_role(*allowed_roles: str) -> dict[str, Any]:
    """Require the live profile role, which trusted_profile verifies per request."""
    profile = trusted_profile()
    if not profile or profile.get("role") not in set(allowed_roles):
        raise PermissionError("This action is not permitted for the current account")
    return profile


def revoke_auth_session() -> None:
    """Revoke the refresh token at Supabase Auth and clear the signed cookie."""
    access, refresh = flask_session.get("auth_access_token"), flask_session.get("auth_refresh_token")
    try:
        if access and refresh:
            client = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", ""))
            client.auth.set_session(access, refresh)
            client.auth.sign_out({"scope": "local"})
    finally:
        flask_session.clear()

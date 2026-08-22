"""
Enterprise Security, Password Hashing, JWT RBAC & Audit Module with Persistent Storage.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from fastapi import Depends, HTTPException, Header, Request, status

from .config import settings
from .db.repositories.users import user_repo
from .db.repositories.audit import audit_repo

PASSWORD_SALT_BYTES = 16
PBKDF2_ITERATIONS = 600000


@dataclass
class User:
    id: str
    email: str
    name: str
    password_hash: str
    role: str  # 'admin' | 'specialist' | 'reviewer' | 'viewer'
    created_at: float = field(default_factory=time.time)
    avatar_color: str = "from-cyan-500 to-blue-600"
    token_version: int = 1
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "avatar_color": self.avatar_color,
            "created_at": self.created_at,
            "token_version": self.token_version,
            "is_active": self.is_active,
        }


def validate_production_security() -> None:
    """Validate environment credentials before accepting requests in production."""
    env = os.getenv("ENVIRONMENT", settings.environment).lower().strip()
    if env == "production":
        secret = os.getenv("JWT_SECRET", settings.jwt_secret).strip()
        insecure_secrets = [
            "f9c2d1b8e4a7360592c81e7d3a5b6c8f1029384756a1b2c3d4e5f60718293a4b",
            "dev-insecure-secret-key-change-in-production",
            "secret",
            "changeme",
        ]
        if not secret or secret in insecure_secrets or len(secret) < 32:
            raise RuntimeError(
                "Production security violation: Insecure, default, or weak JWT_SECRET detected. "
                "You must configure a strong JWT_SECRET (>= 32 chars) in production."
            )

        admin_email = (os.getenv("ADMIN_INITIAL_EMAIL", settings.admin_initial_email or "")).strip()
        admin_pwd = (os.getenv("ADMIN_INITIAL_PASSWORD", settings.admin_initial_password or "")).strip()

        if not admin_email or not admin_pwd or admin_pwd == "Admin@123456" or len(admin_pwd) < 8:
            raise RuntimeError(
                "Production security violation: Insecure or missing ADMIN_INITIAL_EMAIL / ADMIN_INITIAL_PASSWORD. "
                "Explicit strong production admin credentials must be configured (min 8 chars) when ENVIRONMENT=production."
            )


# ============================================================================
# Security Event Audit Logger
# ============================================================================

class SecurityAuditLogger:
    """Thread-safe security logger that records to both memory and SQLite audit trail."""
    def __init__(self, max_entries: int = 1000) -> None:
        self.max_entries = max_entries
        self.events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def log_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        level: str = "INFO",
        user_email: str = "system",
        role: str = "system",
        request_id: Optional[str] = None
    ) -> None:
        event = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "level": level,
            "event_type": event_type,
            "details": details,
        }
        with self._lock:
            self.events.append(event)
            if len(self.events) > self.max_entries:
                self.events.pop(0)

        # Also persist to database audit logs
        try:
            audit_repo.record_action(
                user_email=user_email,
                role=role,
                action=event_type,
                entity_type="security_event",
                entity_id=details.get("user_id", "system"),
                after_state=details,
                reason=f"Security event: {event_type}",
                request_id=request_id,
            )
        except Exception:
            pass

    def get_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            return list(reversed(self.events[-limit:]))


security_logger = SecurityAuditLogger()


# ============================================================================
# Sliding Window Rate Limiter
# ============================================================================

class LoginRateLimiter:
    """In-memory sliding window rate limiter to mitigate brute-force password guessing."""
    def __init__(self, max_attempts: int = 5, window_seconds: int = 60) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def check_rate_limit(self, key: str) -> None:
        now = time.time()
        with self._lock:
            timestamps = self._attempts.get(key, [])
            timestamps = [t for t in timestamps if now - t < self.window_seconds]
            self._attempts[key] = timestamps
            if len(timestamps) >= self.max_attempts:
                retry_after = int(self.window_seconds - (now - timestamps[0]))
                security_logger.log_event(
                    "LOGIN_RATE_LIMIT_EXCEEDED",
                    {"key": key, "attempts": len(timestamps), "retry_after": retry_after},
                    level="WARNING"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed attempts. Throttled for {max(1, retry_after)} seconds.",
                    headers={"Retry-After": str(max(1, retry_after))},
                )

    def record_failed_attempt(self, key: str) -> None:
        now = time.time()
        with self._lock:
            timestamps = self._attempts.get(key, [])
            timestamps = [t for t in timestamps if now - t < self.window_seconds]
            timestamps.append(now)
            self._attempts[key] = timestamps

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)


login_rate_limiter = LoginRateLimiter(max_attempts=5, window_seconds=60)
enrichment_rate_limiter = LoginRateLimiter(max_attempts=20, window_seconds=60)


# ============================================================================
# Password Hashing & Verification (PBKDF2-HMAC-SHA256)
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_hex = salt.hex()
    key_hex = key.hex()
    return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}${salt_hex}${key_hex}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash."""
    try:
        header, salt_hex, key_hex = hashed_password.split("$")
        algorithm, iterations_str = header.split(":")[-2:]
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)

        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(computed_key, expected_key)
    except Exception:
        return False


# ============================================================================
# JWT Token Generation & Verification (RFC 7519 HS256)
# ============================================================================

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64url_decode(data_str: str) -> bytes:
    padding = "=" * (4 - (len(data_str) % 4)) if len(data_str) % 4 != 0 else ""
    return base64.urlsafe_b64decode((data_str + padding).encode("utf-8"))


def create_access_token(user: User, expires_in: Optional[int] = None) -> str:
    """Create an RFC 7519 compliant JSON Web Token signed with HMAC-SHA256."""
    expires_in_sec = expires_in if expires_in is not None else settings.jwt_expiration_seconds
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "ver": getattr(user, "token_version", 1),
        "iat": now,
        "exp": now + expires_in_sec,
    }

    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Verify and decode an access token. Enforces algorithm, expiry, and token version."""
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT token structure",
            headers={"WWW-Authenticate": "Bearer"},
        )

    header_b64, payload_b64, signature_b64 = parts

    try:
        header = json.loads(_base64url_decode(header_b64).decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if header.get("alg") != settings.jwt_algorithm:
        security_logger.log_event(
            "JWT_ALGORITHM_MISMATCH",
            {"expected": settings.jwt_algorithm, "received": header.get("alg")},
            level="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported token algorithm: '{header.get('alg')}'. Only {settings.jwt_algorithm} accepted.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Verify Cryptographic Signature
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    expected_signature_b64 = _base64url_encode(expected_signature)

    if not hmac.compare_digest(signature_b64, expected_signature_b64):
        security_logger.log_event("JWT_SIGNATURE_INVALID", {"received": signature_b64[:10] + "..."}, level="WARNING")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Payload & Expiry Validation
    try:
        payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = time.time()
    if "exp" in payload and payload["exp"] < now:
        security_logger.log_event("JWT_EXPIRED", {"sub": payload.get("sub"), "exp": payload.get("exp")}, level="INFO")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Token Revocation Check (token_version)
    user_id = payload.get("sub")
    if user_id:
        u_dict = user_repo.get_by_id(user_id)
        if u_dict:
            token_ver = payload.get("ver", 1)
            current_ver = u_dict.get("token_version", 1)
            if token_ver < current_ver:
                security_logger.log_event("JWT_REVOKED", {"user_id": user_id, "token_ver": token_ver, "current_ver": current_ver}, level="WARNING")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session has been revoked. Please sign in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    return payload


# ============================================================================
# Persistent User Store
# ============================================================================

class UserStore:
    """Manages users backed by SQLite database with automatic demo account bootstrap."""

    def __init__(self) -> None:
        from .db.migrations import run_migrations
        try:
            run_migrations()
        except Exception:
            pass
        self._bootstrap_initial_accounts()

    def _bootstrap_initial_accounts(self) -> None:
        """Seed default admin, specialist, reviewer, and viewer accounts in development only."""
        env = os.getenv("ENVIRONMENT", settings.environment).lower().strip()
        if env == "production":
            # In production, seed ONLY the explicitly configured admin credentials if provided
            admin_email = (os.getenv("ADMIN_INITIAL_EMAIL", settings.admin_initial_email) or "").lower().strip()
            admin_pwd = os.getenv("ADMIN_INITIAL_PASSWORD", settings.admin_initial_password)
            admin_name = os.getenv("ADMIN_INITIAL_NAME", settings.admin_initial_name) or "System Administrator"
            if admin_email and admin_pwd:
                existing = user_repo.get_by_email(admin_email)
                if not existing:
                    user_repo.create_user(
                        email=admin_email,
                        name=admin_name,
                        password_hash=hash_password(admin_pwd),
                        role="admin",
                        avatar_color="from-cyan-500 to-blue-600",
                    )
            return

        demo_profiles = [
            ("admin@unilog.com", "Admin@123456", "System Administrator", "admin", "from-cyan-500 to-blue-600"),
            ("specialist@unilog.com", "Specialist@123456", "Data Specialist", "specialist", "from-blue-500 to-indigo-600"),
            ("reviewer@unilog.com", "Reviewer@123456", "Catalog Reviewer", "reviewer", "from-emerald-500 to-teal-600"),
            ("viewer@unilog.com", "Viewer@123456", "Executive Viewer", "viewer", "from-slate-500 to-zinc-600"),
        ]

        if settings.admin_initial_email and settings.admin_initial_password:
            demo_profiles[0] = (
                settings.admin_initial_email.lower().strip(),
                settings.admin_initial_password,
                settings.admin_initial_name or "System Administrator",
                "admin",
                "from-cyan-500 to-blue-600"
            )

        for email, pwd, name, role, color in demo_profiles:
            clean_email = email.lower().strip()
            existing = user_repo.get_by_email(clean_email)
            if not existing:
                user_repo.create_user(
                    email=clean_email,
                    name=name,
                    password_hash=hash_password(pwd),
                    role=role,
                    avatar_color=color,
                )

    def get_by_email(self, email: str) -> Optional[User]:
        d = user_repo.get_by_email(email)
        if not d:
            return None
        return User(
            id=d["id"],
            email=d["email"],
            name=d["name"],
            password_hash=d["password_hash"],
            role=d["role"],
            created_at=d["created_at"],
            avatar_color=d["avatar_color"],
            token_version=d["token_version"],
            is_active=bool(d["is_active"]),
        )

    def get_by_id(self, user_id: str) -> Optional[User]:
        d = user_repo.get_by_id(user_id)
        if not d:
            return None
        return User(
            id=d["id"],
            email=d["email"],
            name=d["name"],
            password_hash=d["password_hash"],
            role=d["role"],
            created_at=d["created_at"],
            avatar_color=d["avatar_color"],
            token_version=d["token_version"],
            is_active=bool(d["is_active"]),
        )

    def create_user(self, email: str, password: str, name: str, role: str = "viewer") -> User:
        clean_email = email.lower().strip()
        existing = user_repo.get_by_email(clean_email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{email}' already exists",
            )
        valid_roles = {"admin", "specialist", "reviewer", "viewer"}
        if role not in valid_roles:
            role = "viewer"

        color_map = {
            "admin": "from-cyan-500 to-blue-600",
            "specialist": "from-blue-500 to-indigo-600",
            "reviewer": "from-emerald-500 to-teal-600",
            "viewer": "from-slate-500 to-zinc-600",
        }
        hashed = hash_password(password)
        d = user_repo.create_user(
            email=clean_email,
            name=name.strip() or clean_email.split("@")[0].capitalize(),
            password_hash=hashed,
            role=role,
            avatar_color=color_map.get(role, "from-slate-500 to-zinc-600"),
        )
        security_logger.log_event("USER_CREATED", {"user_id": d["id"], "email": clean_email, "role": role})
        return self.get_by_id(d["id"])

    def update_user_role(self, user_id: str, new_role: str) -> User:
        """Update user role and increment token version to force session refresh."""
        valid_roles = {"admin", "specialist", "reviewer", "viewer"}
        clean_role = new_role.lower().strip()
        if clean_role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role '{new_role}'. Permitted roles: {list(valid_roles)}",
            )
        updated = user_repo.update_role(user_id, clean_role)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found.",
            )
        security_logger.log_event("USER_ROLE_UPDATED", {"user_id": user_id, "new_role": clean_role})
        return self.get_by_id(user_id)

    def list_all(self) -> List[User]:
        raw_list = user_repo.list_users()
        return [
            User(
                id=d["id"],
                email=d["email"],
                name=d["name"],
                password_hash=d.get("password_hash", ""),
                role=d["role"],
                created_at=d["created_at"],
                avatar_color=d["avatar_color"],
                token_version=d["token_version"],
                is_active=bool(d["is_active"]),
            )
            for d in raw_list
        ]


user_store = UserStore()


# ============================================================================
# FastAPI Dependency Injectors for RBAC
# ============================================================================

def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> User:
    """Extract and validate JWT token from Bearer header or secure HttpOnly cookie."""
    token = None
    from_cookie = False

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
    elif "unilog_auth_token" in request.cookies:
        token = request.cookies.get("unilog_auth_token")
        from_cookie = True

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Cookie sessions require a double-submit CSRF token. Bearer-token API
    # clients remain supported and do not use this browser-only protection.
    if from_cookie and request.method in ("POST", "PUT", "PATCH", "DELETE"):
        csrf_cookie = request.cookies.get("unilog_csrf_token", "")
        csrf_header = request.headers.get("X-CSRF-Token", "")
        if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-Site Request Forgery (CSRF) protection triggered.",
            )

    payload = decode_access_token(token)
    user_id = payload.get("sub")
    user = user_store.get_by_id(user_id) if user_id else None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(allowed_roles: List[str]):
    """Enforce Role-Based Access Control (RBAC)."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            security_logger.log_event(
                "RBAC_ACCESS_DENIED",
                {"user_id": current_user.id, "role": current_user.role, "required_roles": allowed_roles},
                level="WARNING",
                user_email=current_user.email,
                role=current_user.role
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of roles: {', '.join(allowed_roles)}. Your role is '{current_user.role}'.",
            )
        return current_user
    return role_checker


# Convenient role access checkers
require_viewer = require_roles(["viewer", "specialist", "reviewer", "admin"])
require_specialist = require_roles(["specialist", "reviewer", "admin"])
require_reviewer = require_roles(["reviewer", "admin"])
require_admin = require_roles(["admin"])

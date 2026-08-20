"""Enterprise Security, Password Hashing & JWT RBAC Module.

Zero-dependency standard library implementation of PBKDF2-HMAC-SHA256 password hashing,
RFC 7519 JWT HMAC-SHA256 token encoding/decoding, and Role-Based Access Control (RBAC).
Configuration and secrets are loaded securely from environment variables.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from fastapi import Depends, HTTPException, Header, status

from .config import settings

PASSWORD_SALT_BYTES = 16
PBKDF2_ITERATIONS = 100000


@dataclass
class User:
    id: str
    email: str
    name: str
    password_hash: str
    role: str  # 'admin' | 'specialist' | 'reviewer' | 'viewer'
    created_at: float = field(default_factory=time.time)
    avatar_color: str = "from-cyan-500 to-blue-600"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "avatar_color": self.avatar_color,
            "created_at": self.created_at,
        }


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
    """Verify and decode an access token. Raises HTTPException on invalid/expired token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT token structure",
            headers={"WWW-Authenticate": "Bearer"},
        )

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()

    try:
        provided_sig = _base64url_decode(signature_b64)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Expiration check
    if "exp" in payload and payload["exp"] < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


# ============================================================================
# User Store (In-Memory with Environment-Configured Bootstrap)
# ============================================================================

class UserStore:
    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self._email_index: Dict[str, str] = {}
        self._bootstrap_initial_admin()

    def _bootstrap_initial_admin(self) -> None:
        """Bootstrap initial administrative user from environment variables if configured."""
        if settings.admin_initial_email and settings.admin_initial_password:
            email = settings.admin_initial_email.lower().strip()
            user_id = f"usr_{secrets.token_hex(4)}"
            user = User(
                id=user_id,
                email=email,
                name=settings.admin_initial_name or "System Administrator",
                password_hash=hash_password(settings.admin_initial_password),
                role="admin",
                avatar_color="from-cyan-500 to-blue-600",
            )
            self._users[user_id] = user
            self._email_index[email] = user_id

    def get_by_email(self, email: str) -> Optional[User]:
        clean_email = email.lower().strip()
        user_id = self._email_index.get(clean_email)
        if user_id:
            return self._users.get(user_id)
        return None

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def create_user(self, email: str, password: str, name: str, role: str = "specialist") -> User:
        clean_email = email.lower().strip()
        if clean_email in self._email_index:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{email}' already exists",
            )
        valid_roles = {"admin", "specialist", "reviewer", "viewer"}
        if role not in valid_roles:
            role = "specialist"

        user_id = f"usr_{secrets.token_hex(4)}"
        color_map = {
            "admin": "from-cyan-500 to-blue-600",
            "specialist": "from-blue-500 to-indigo-600",
            "reviewer": "from-emerald-500 to-teal-600",
            "viewer": "from-slate-500 to-zinc-600",
        }
        user = User(
            id=user_id,
            email=clean_email,
            name=name.strip() or clean_email.split("@")[0].capitalize(),
            password_hash=hash_password(password),
            role=role,
            avatar_color=color_map.get(role, "from-cyan-500 to-blue-600"),
        )
        self._users[user_id] = user
        self._email_index[clean_email] = user_id
        return user

    def list_all(self) -> List[User]:
        return list(self._users.values())


user_store = UserStore()


# ============================================================================
# FastAPI Dependency Injectors for RBAC
# ============================================================================

def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """Extract user from Authorization: Bearer <token> if present, otherwise return None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ")[1].strip()
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id:
            return user_store.get_by_id(user_id)
    except HTTPException:
        pass
    return None


def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Require valid JWT token in Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split("Bearer ")[1].strip()
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of roles: {', '.join(allowed_roles)}. Your role is '{current_user.role}'.",
            )
        return current_user
    return role_checker

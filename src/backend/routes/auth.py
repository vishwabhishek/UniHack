import os
import secrets
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from ..config import settings
from ..auth import (
    User,
    create_access_token,
    get_current_user,
    login_rate_limiter,
    require_roles,
    security_logger,
    user_store,
    verify_password,
)
from ..db.repositories.users import user_repo

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


class LoginRequest(BaseModel):
    email: str = Field(..., description="User corporate email address")
    password: str = Field(..., description="Plaintext user password")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User corporate email address")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    name: str = Field(..., min_length=2, description="Full Name")
    role: Optional[str] = Field(default="viewer", description="Role: defaults to viewer. Elevated roles require admin assignment.")


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(..., description="New role: admin, specialist, reviewer, viewer")


class AuthResponse(BaseModel):
    token: str
    token_type: str = "Bearer"
    user: Dict[str, Any]


def _set_auth_cookie(response: Response, token: str, request: Request) -> None:
    is_prod = os.getenv("ENVIRONMENT", settings.environment).lower().strip() == "production"
    is_https = request.url.scheme == "https"
    response.set_cookie(
        key="unilog_auth_token",
        value=token,
        max_age=settings.jwt_expiration_seconds,
        path="/",
        samesite="lax",
        httponly=True,
        secure=is_prod or is_https,
    )
    # The JWT remains HttpOnly. This separate value supports the browser
    # double-submit CSRF check for mutating cookie-authenticated requests.
    response.set_cookie(
        key="unilog_csrf_token",
        value=secrets.token_urlsafe(32),
        max_age=settings.jwt_expiration_seconds,
        path="/",
        samesite="lax",
        httponly=False,
        secure=is_prod or is_https,
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response) -> AuthResponse:
    """Authenticate with corporate email and password to receive a JWT session token with brute-force rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{payload.email.lower().strip()}"

    # 1. Enforce sliding window rate limit (Max 5 attempts / min)
    login_rate_limiter.check_rate_limit(rate_key)

    user = user_store.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        login_rate_limiter.record_failed_attempt(rate_key)
        security_logger.log_event(
            "LOGIN_FAILED",
            {"email": payload.email, "client_ip": client_ip},
            level="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid corporate email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset failed attempts upon successful login
    login_rate_limiter.reset(rate_key)
    security_logger.log_event(
        "LOGIN_SUCCESS",
        {"user_id": user.id, "email": user.email, "role": user.role, "client_ip": client_ip}
    )

    token = create_access_token(user)
    _set_auth_cookie(response, token, request)
    return AuthResponse(
        token=token,
        token_type="Bearer",
        user=user.to_dict(),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, response: Response) -> AuthResponse:
    """
    Register a new enterprise user.
    Public registration is strictly restricted: elevated roles (admin, reviewer) cannot be self-assigned.
    """
    requested_role = (payload.role or "viewer").lower().strip()
    if requested_role in ("admin", "reviewer"):
        security_logger.log_event(
            "PRIVILEGE_ESCALATION_ATTEMPT",
            {"email": payload.email, "attempted_role": requested_role, "client_ip": request.client.host if request.client else "unknown"},
            level="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Self-registration cannot grant elevated role '{requested_role}'. Public accounts are limited to 'viewer' or 'specialist'.",
        )

    assigned_role = requested_role if requested_role in ("specialist", "viewer") else "viewer"

    user = user_store.create_user(
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=assigned_role,
    )
    token = create_access_token(user)
    _set_auth_cookie(response, token, request)
    return AuthResponse(
        token=token,
        token_type="Bearer",
        user=user.to_dict(),
    )


@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """Log out by invalidating active sessions and removing session cookies."""
    user_repo.increment_token_version(current_user.id)
    response.delete_cookie(key="unilog_auth_token", path="/")
    response.delete_cookie(key="unilog_csrf_token", path="/")
    security_logger.log_event("LOGOUT", {"user_id": current_user.id, "email": current_user.email})
    return {"status": "success", "message": "Successfully logged out and session revoked."}


@router.get("/me", response_model=Dict[str, Any])
def get_current_user_profile(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieve profile and permissions for the currently authenticated user."""
    return current_user.to_dict()


@router.get("/users", response_model=List[Dict[str, Any]])
def list_users(current_user: User = Depends(require_roles(["admin"]))) -> List[Dict[str, Any]]:
    """List all registered platform users (Admin-only RBAC)."""
    return [u.to_dict() for u in user_store.list_all()]


@router.put("/users/{user_id}/role", response_model=Dict[str, Any])
def update_user_role(
    user_id: str,
    payload: UpdateUserRoleRequest,
    current_user: User = Depends(require_roles(["admin"]))
) -> Dict[str, Any]:
    """Update a user's role (Admin-only). Automatically invalidates active tokens with stale roles."""
    updated_user = user_store.update_user_role(user_id=user_id, new_role=payload.role)
    return {
        "status": "success",
        "message": f"User '{updated_user.email}' role updated to '{updated_user.role}'.",
        "user": updated_user.to_dict(),
    }


@router.get("/security-events", response_model=List[Dict[str, Any]])
def get_security_events(current_user: User = Depends(require_roles(["admin"]))) -> List[Dict[str, Any]]:
    """Retrieve security audit event trail (Admin-only RBAC)."""
    return security_logger.get_events(limit=100)

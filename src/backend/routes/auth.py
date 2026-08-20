"""Authentication, User Management & Security Event API Routes."""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request, status

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

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


class LoginRequest(BaseModel):
    email: str = Field(..., description="User corporate email address")
    password: str = Field(..., description="Plaintext user password")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User corporate email address")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    name: str = Field(..., min_length=2, description="Full Name")
    role: str = Field(default="specialist", description="Role: admin, specialist, reviewer, viewer")


class AuthResponse(BaseModel):
    token: str
    token_type: str = "Bearer"
    user: Dict[str, Any]


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request) -> AuthResponse:
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
    return AuthResponse(
        token=token,
        token_type="Bearer",
        user=user.to_dict(),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> AuthResponse:
    """Register a new enterprise user and issue an initial JWT session token."""
    user = user_store.create_user(
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=payload.role,
    )
    token = create_access_token(user)
    return AuthResponse(
        token=token,
        token_type="Bearer",
        user=user.to_dict(),
    )


@router.get("/me", response_model=Dict[str, Any])
def get_current_user_profile(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieve profile and permissions for the currently authenticated user."""
    return current_user.to_dict()


@router.get("/users", response_model=List[Dict[str, Any]])
def list_users(current_user: User = Depends(require_roles(["admin"]))) -> List[Dict[str, Any]]:
    """List all registered platform users (Admin-only RBAC)."""
    return [u.to_dict() for u in user_store.list_all()]


@router.get("/security-events", response_model=List[Dict[str, Any]])
def get_security_events(current_user: User = Depends(require_roles(["admin"]))) -> List[Dict[str, Any]]:
    """Retrieve security audit event trail (Admin-only RBAC)."""
    return security_logger.get_events(limit=100)

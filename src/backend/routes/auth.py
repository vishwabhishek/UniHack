"""Authentication & User Management API Routes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import (
    User,
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
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


class DemoAccount(BaseModel):
    role: str
    email: str
    password: str
    name: str
    description: str


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    """Authenticate with corporate email and password to receive a JWT session token."""
    user = user_store.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid corporate email or password",
            headers={"WWW-Authenticate": "Bearer"},
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


@router.get("/demo-accounts", response_model=List[DemoAccount])
def get_demo_accounts() -> List[DemoAccount]:
    """Return list of pre-seeded demo enterprise accounts for 1-click evaluation."""
    return [
        DemoAccount(
            role="admin",
            email="admin@unilog.com",
            password="Admin2026!",
            name="Sarah Lin",
            description="Full enterprise control, catalog overrides, user management & syndication",
        ),
        DemoAccount(
            role="specialist",
            email="specialist@unilog.com",
            password="Specialist2026!",
            name="Alex Mercer",
            description="Master data curation, inline cell editing, sandbox testing & approval",
        ),
        DemoAccount(
            role="reviewer",
            email="reviewer@unilog.com",
            password="Reviewer2026!",
            name="David Vance",
            description="Quality assurance lead, HITL triage board review & validation",
        ),
        DemoAccount(
            role="viewer",
            email="viewer@unilog.com",
            password="Viewer2026!",
            name="Elena Rostova",
            description="Read-only compliance auditor & 252-column schema inspection",
        ),
    ]


@router.get("/users", response_model=List[Dict[str, Any]])
def list_users(current_user: User = Depends(require_roles(["admin"]))) -> List[Dict[str, Any]]:
    """List all registered platform users (Admin-only)."""
    return [u.to_dict() for u in user_store.list_all()]

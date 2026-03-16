import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Header
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorCollection
from passlib.context import CryptContext

from .db import get_users_collection
from .schemas import (
    AuthLoginRequest,
    AuthSignupRequest,
    AuthTokenResponse,
    ChangePasswordRequest,
    MeResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)


router = APIRouter(prefix="/auth", tags=["auth"])

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _jwt_secret() -> str:
    # For local dev we allow a default. In production set JWT_SECRET.
    return (os.getenv("JWT_SECRET") or "dev-secret-change-me").strip()


def _jwt_issuer() -> str:
    return (os.getenv("JWT_ISSUER") or "vb").strip()


def _jwt_exp_minutes() -> int:
    try:
        return int(os.getenv("JWT_EXPIRE_MINUTES") or "10080")  # 7 days
    except ValueError:
        return 10080


def _create_access_token(email: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=_jwt_exp_minutes())
    payload = {
        "sub": email,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "iss": _jwt_issuer(),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def _decode_email(token: str) -> str:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"], issuer=_jwt_issuer())
        email = payload.get("sub")
        if not isinstance(email, str) or not email.strip():
            raise HTTPException(status_code=401, detail="Invalid token.")
        return email.strip().lower()
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")


def _norm_email(email: str) -> str:
    return (email or "").strip().lower()


@router.post("/signup", response_model=AuthTokenResponse)
async def signup(payload: AuthSignupRequest, users: AsyncIOMotorCollection = Depends(get_users_collection)) -> AuthTokenResponse:
    email = _norm_email(payload.email)
    password = (payload.password or "").strip()
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    existing = await users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists. Please log in.")

    password_hash = _pwd.hash(password)
    now = datetime.now(timezone.utc)
    await users.insert_one(
        {
            "email": email,
            "password_hash": password_hash,
            "created_at": now,
            "last_login_at": now,
        }
    )

    return AuthTokenResponse(access_token=_create_access_token(email=email))


@router.post("/login", response_model=AuthTokenResponse)
async def login(payload: AuthLoginRequest, users: AsyncIOMotorCollection = Depends(get_users_collection)) -> AuthTokenResponse:
    email = _norm_email(payload.email)
    password = (payload.password or "").strip()
    user = await users.find_one({"email": email})
    if not user or not _pwd.verify(password, user.get("password_hash") or ""):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    await users.update_one({"_id": user["_id"]}, {"$set": {"last_login_at": datetime.now(timezone.utc)}})
    return AuthTokenResponse(access_token=_create_access_token(email=email))


async def require_user_email(
    authorization: str | None,
) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header.")
    return _decode_email(parts[1].strip())


@router.get("/me", response_model=MeResponse)
async def me(
    authorization: str | None = Header(default=None),
) -> MeResponse:
    email = await require_user_email(authorization)
    return MeResponse(email=email)


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    authorization: str | None = Header(default=None),
    users: AsyncIOMotorCollection = Depends(get_users_collection),
) -> ProfileResponse:
    email = await require_user_email(authorization or "")
    user = await users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ProfileResponse(
        email=email,
        name=user.get("name"),
        handle=user.get("handle"),
        bio=user.get("bio"),
    )


@router.post("/profile", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    authorization: str | None = Header(default=None),
    users: AsyncIOMotorCollection = Depends(get_users_collection),
) -> ProfileResponse:
    email = await require_user_email(authorization or "")
    user = await users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates: dict[str, object] = {}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.bio is not None:
        updates["bio"] = payload.bio.strip()
    if payload.handle is not None and not user.get("handle"):
        updates["handle"] = payload.handle.strip()

    if updates:
        await users.update_one({"_id": user["_id"]}, {"$set": updates})
        user.update(updates)

    return ProfileResponse(
        email=email,
        name=user.get("name"),
        handle=user.get("handle"),
        bio=user.get("bio"),
    )


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    authorization: str | None = Header(default=None),
    users: AsyncIOMotorCollection = Depends(get_users_collection),
) -> dict:
    email = await require_user_email(authorization or "")
    user = await users.find_one({"email": email})
    if not user or not _pwd.verify(payload.old_password, user.get("password_hash") or ""):
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    new_hash = _pwd.hash(payload.new_password.strip())
    await users.update_one({"_id": user["_id"]}, {"$set": {"password_hash": new_hash}})
    return {"ok": True}


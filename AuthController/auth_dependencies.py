# auth_dependencies.py
import os

import firebase_admin
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from DataModels.UserModel import User

bearer = HTTPBearer(auto_error=False)

# Initialize Firebase Admin SDK at startup
def init_firebase() -> None:
    if firebase_admin._apps:
        return

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is not set")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Helper function to get user by Firebase UID
async def _get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str) -> User | None:
    res = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    return res.scalar_one_or_none()

# Dependency to get Firebase identity from token
async def get_firebase_identity(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    token = creds.credentials

    try:
        decoded_token = auth.verify_id_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
        )

    firebase_uid = decoded_token.get("uid")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token payload",
        )

    return decoded_token

# Dependency to get current user from Firebase token
async def get_current_user(
    decoded_token: dict = Depends(get_firebase_identity),
    db: AsyncSession = Depends(get_db),
) -> User:
    firebase_uid = decoded_token["uid"]

    user = await _get_user_by_firebase_uid(db, firebase_uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

# Dependency to require admin access or valid device API key
async def require_admin_or_device(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    device_api_key = os.getenv("API_KEY")

    if x_api_key and device_api_key and x_api_key == device_api_key:
        return {"auth_type": "device"}

    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token or valid device API key required",
        )

    try:
        decoded_token = auth.verify_id_token(creds.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
        )

    firebase_uid = decoded_token.get("uid")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token payload",
        )

    user = await _get_user_by_firebase_uid(db, firebase_uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return {"auth_type": "admin", "user": user}
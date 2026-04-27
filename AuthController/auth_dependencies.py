# # auth_dependencies.py
# from datetime import timedelta
# from typing import Optional
# import os

# import jwt
# from fastapi import Depends, HTTPException, status, Header
# from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
# from sqlalchemy import select, update
# from sqlalchemy.ext.asyncio import AsyncSession

# from db import get_db

# from DataModels.SessionModel import ApiSession
# from DataModels.UserModel import User
# from AuthController.jwt_func import decode_access_token as decode_token, now_utc as utcnow

# bearer = HTTPBearer(auto_error=True)

# INACTIVITY_MINUTES = 15
# # Reduce DB writes: only update last_seen if older than this many seconds
# LAST_SEEN_WRITE_COOLDOWN_SECONDS = 30

# async def _get_session(db: AsyncSession, jti: str) -> Optional[ApiSession]:
#     res = await db.execute(select(ApiSession).where(ApiSession.jti == jti))
#     return res.scalar_one_or_none()

# async def get_current_user(
#     creds: HTTPAuthorizationCredentials = Depends(bearer),
#     db: AsyncSession = Depends(get_db),
# ) -> User:
#     token = creds.credentials

#     try:
#         payload = decode_token(token)  # checks signature + exp
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
#     except jwt.PyJWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

#     jti = payload.get("jti")
#     sub = payload.get("sub")
#     if not jti or not sub:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

#     now = utcnow()

#     sess = await _get_session(db, jti)
#     if not sess:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")
#     if sess.revoked:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")

#     # Hard expiry (backstop; JWT exp already checked)
#     if now > sess.expires_at:
#         sess.revoked = True
#         await db.commit()
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

#     # Inactivity timeout
#     if now - sess.last_seen > timedelta(minutes=INACTIVITY_MINUTES):
#         sess.revoked = True
#         await db.commit()
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session timed out")

#     # Update last_seen with cooldown to avoid writing every request
#     if (now - sess.last_seen).total_seconds() >= LAST_SEEN_WRITE_COOLDOWN_SECONDS:
#         await db.execute(
#             update(ApiSession)
#             .where(ApiSession.jti == jti)
#             .values(last_seen=now)
#         )
#         await db.commit()

#     # Fetch user
#     res = await db.execute(select(User).where(User.id == int(sub)))
#     user = res.scalar_one_or_none()
#     if not user:
#         # revoke session if user no longer exists
#         sess.revoked = True
#         await db.commit()
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

#     return user


# async def require_admin_or_device(
#     creds: HTTPAuthorizationCredentials | None = Depends(bearer),
#     x_api_key: str | None = Header(default=None, alias="X-API-Key"),
#     db: AsyncSession = Depends(get_db),
# ):
#     device_api_key = os.getenv("API_KEY")

#     # Allow device access via API key
#     if x_api_key and device_api_key and x_api_key == device_api_key:
#         return {"auth_type": "device"}

#     # Otherwise require JWT admin user
#     if not creds:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Admin token or valid device API key required",
#         )

#     token = creds.credentials

#     try:
#         payload = decode_token(token)  # checks signature + exp
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token expired",
#         )
#     except jwt.PyJWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token",
#         )

#     jti = payload.get("jti")
#     sub = payload.get("sub")
#     if not jti or not sub:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token payload",
#         )

#     now = utcnow()

#     sess = await _get_session(db, jti)
#     if not sess:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Session not found",
#         )
#     if sess.revoked:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Session revoked",
#         )

#     # Hard expiry
#     if now > sess.expires_at:
#         sess.revoked = True
#         await db.commit()
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Session expired",
#         )

#     # Inactivity timeout
#     if now - sess.last_seen > timedelta(minutes=INACTIVITY_MINUTES):
#         sess.revoked = True
#         await db.commit()
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Session timed out",
#         )

#     # Update last_seen with cooldown
#     if (now - sess.last_seen).total_seconds() >= LAST_SEEN_WRITE_COOLDOWN_SECONDS:
#         await db.execute(
#             update(ApiSession)
#             .where(ApiSession.jti == jti)
#             .values(last_seen=now)
#         )
#         await db.commit()

#     # Fetch user
#     res = await db.execute(select(User).where(User.id == int(sub)))
#     user = res.scalar_one_or_none()
#     if not user:
#         sess.revoked = True
#         await db.commit()
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found",
#         )

#     if not user.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Admin access required",
#         )

#     return {"auth_type": "admin", "user": user}

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


def init_firebase() -> None:
    if firebase_admin._apps:
        return

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is not set")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)


async def _get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str) -> User | None:
    res = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    return res.scalar_one_or_none()


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
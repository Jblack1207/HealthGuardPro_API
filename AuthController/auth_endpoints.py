# # auth_endpoints.py
# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
# from sqlalchemy import select, update
# from sqlalchemy.ext.asyncio import AsyncSession

# from db import get_db

# from AuthController.jwt_func import create_access_token, now_utc as utcnow, decode_access_token as decode_token

# from Schemas.AuthSchema import LoginRequest, TokenResponse
# from DataModels.SessionModel import ApiSession
# from DataModels.UserModel import User


# router = APIRouter(prefix="/auth", tags=["Auth"])
# bearer = HTTPBearer(auto_error=True)


# def verify_password(plain: str, hashed: str) -> bool:
#     # TODO: replace with bcrypt/argon2 check
#     return plain == hashed

# @router.post("/login", response_model=TokenResponse)
# async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
#     res = await db.execute(select(User).where(User.email == payload.email))
#     user = res.scalar_one_or_none()

#     if not user or not verify_password(payload.password, user.password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

#     token, jti, expires_at = create_access_token(user_id=user.id, is_admin=user.is_admin)
#     now = utcnow()

#     db.add(
#         ApiSession(
#             jti=jti,
#             user_id=user.id,
#             issued_at=now,
#             last_seen=now,
#             revoked=False,
#             expires_at=expires_at,
#         )
#     )
#     await db.commit()

#     return TokenResponse(access_token=token, email=user.email)

# @router.post("/logout")
# async def logout(
#     creds: HTTPAuthorizationCredentials = Depends(bearer),
#     db: AsyncSession = Depends(get_db),
# ):
#     # Revoke session immediately
#     try:
#         payload = decode_token(creds.credentials, verify_exp=False)
#     except Exception:
#         # If token is invalid, treat as already logged out
#         return {"Token Invalid": True}

#     jti = payload.get("jti")
#     if not jti:
#         return {"Not JTI": True}

#     await db.execute(update(ApiSession).where(ApiSession.jti == jti).values(revoked=True))
#     await db.commit()
#     return {"Logged Out": True}


# @router.get("/debug-token")
# async def debug_token(creds: HTTPAuthorizationCredentials = Depends(bearer)):
#     return decode_token(creds.credentials, verify_exp=False)

# auth_endpoints.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from DataModels.UserModel import User
from AuthController.auth_dependencies import get_current_user, get_firebase_identity
from Schemas.UserSchema import SyncUserRequest

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/sync")
async def sync_user(
    payload: SyncUserRequest,
    decoded_token: dict = Depends(get_firebase_identity),
    db: AsyncSession = Depends(get_db),
):
    firebase_uid = decoded_token["uid"]
    email = decoded_token.get("email")
    username = payload.username
    first_name = payload.first_name
    last_name = payload.last_name

    user = await db.scalar(
        User.__table__.select().where(User.firebase_uid == firebase_uid)
    )

    if not user:
        user = User(
            email=email,
            firebase_uid=firebase_uid,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_admin=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user.email = email or user.email
        user.username = payload.username or user.username
        user.first_name = payload.first_name or user.first_name
        user.last_name = payload.last_name or user.last_name

    return {
        "message": "User synced successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "firebase_uid": user.firebase_uid,
            "is_admin": user.is_admin,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        },
    }


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "firebase_uid": current_user.firebase_uid,
        "is_admin": current_user.is_admin,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name
    }

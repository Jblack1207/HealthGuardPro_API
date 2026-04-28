
# auth_endpoints.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from DataModels.UserModel import User
from AuthController.auth_dependencies import get_current_user, get_firebase_identity
from Schemas.UserSchema import SyncUserRequest

router = APIRouter(prefix="/auth", tags=["Auth"])

#SYNC USER ENDPOINT
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

#GET CURRENT USER ENDPOINT
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

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from AuthController.auth_dependencies import get_current_user
from db import get_db
from DataModels.UserModel import User
from DataModels.PushTokenModel import UserPushToken

router = APIRouter(prefix="/push-tokens", tags=["Push Tokens"])


class PushTokenRequest(BaseModel):
    push_token: str
    platform: str | None = None

#REGISTER PUSH TOKEN ENDPOINT (WAS FOR PUSH NOTIFICATIONS BUT WON'T WORK FOR IOS)
@router.post("")
async def register_push_token(
    payload: PushTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPushToken).where(
            UserPushToken.user_id == current_user.id,
            UserPushToken.push_token == payload.push_token,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.platform = payload.platform
    else:
        db.add(
            UserPushToken(
                user_id=current_user.id,
                push_token=payload.push_token,
                platform=payload.platform,
            )
        )

    await db.commit()
    return {"ok": True}

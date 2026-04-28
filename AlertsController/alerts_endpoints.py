from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from AuthController.auth_dependencies import get_current_user
from db import get_db
from DataModels.AlertModel import Alert
from DataModels.UserModel import User

router = APIRouter(prefix="/alerts", tags=["Alerts"])

#GET ALERT ENDPOINTS
@router.get("")
async def list_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert)
        .where(Alert.user_id == current_user.id)
        .order_by(Alert.created_at.desc())
    )
    return result.scalars().all()

#GET ACTIVE ALERTS ENDPOINT
@router.get("/active")
async def list_active_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert)
        .where(
            Alert.user_id == current_user.id,
            Alert.status.in_(["Active", "Acknowledged"]),
        )
        .order_by(Alert.created_at.desc())
    )
    return result.scalars().all()

#ACKNOWLEDGE ALERT ENDPOINT
@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "Acknowledged"
    alert.acknowledged_at = datetime.utcnow()
    await db.commit()

    return {"ok": True}

#RESOLVE ALERT ENDPOINT
@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "Resolved"
    alert.resolved_at = datetime.utcnow()
    await db.commit()

    return {"ok": True}

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from AuthController.auth_dependencies import require_admin_or_device, get_current_user
from db import get_db
from DataModels.FallDetectionModel import FallReading
from Schemas.FallDetectionSchema import FallReadingCreate, FallReadingResponse

router = APIRouter(prefix="/fall-detector", tags=["Fall Detector"])

#CREATE FALL READING ENDPOINT
@router.post(
    "/createReading",
    response_model=FallReadingResponse,
    dependencies=[Depends(require_admin_or_device)],
)
async def create_fall_reading(
    payload: FallReadingCreate,
    db: AsyncSession = Depends(get_db),
):
    reading = FallReading(
        device_id=payload.device_id,
        ax=payload.ax,
        ay=payload.ay,
        az=payload.az,
        gx=payload.gx,
        gy=payload.gy,
        gz=payload.gz,
        total_acc=payload.total_acc,
        tilt=payload.tilt,
        tilt_change=payload.tilt_change,
        possible_fall=payload.possible_fall,
    )

    db.add(reading)
    await db.commit()
    await db.refresh(reading)

    return FallReadingResponse(
        id=reading.id,
        device_id=reading.device_id,
        ax=reading.ax,
        ay=reading.ay,
        az=reading.az,
        gx=reading.gx,
        gy=reading.gy,
        gz=reading.gz,
        total_acc=reading.total_acc,
        tilt=reading.tilt,
        tilt_change=reading.tilt_change,
        possible_fall=reading.possible_fall,
        created_at=reading.created_at,
    )

#GET FALL READINGS ENDPOINT
@router.get(
    "/reading",
    response_model=list[FallReadingResponse],
    dependencies=[Depends(get_current_user)],
)
async def get_fall_readings(
    device_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    query = select(FallReading).order_by(FallReading.created_at.desc()).limit(limit)

    if device_id:
        query = (
            select(FallReading)
            .where(FallReading.device_id == device_id)
            .order_by(FallReading.created_at.desc())
            .limit(limit)
        )

    result = await db.execute(query)
    readings = result.scalars().all()

    return [
        FallReadingResponse(
            id=reading.id,
            device_id=reading.device_id,
            ax=reading.ax,
            ay=reading.ay,
            az=reading.az,
            gx=reading.gx,
            gy=reading.gy,
            gz=reading.gz,
            total_acc=reading.total_acc,
            tilt=reading.tilt,
            tilt_change=reading.tilt_change,
            possible_fall=reading.possible_fall,
            created_at=reading.created_at,
        )
        for reading in readings
    ]
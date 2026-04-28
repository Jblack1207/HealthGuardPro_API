from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select


from db import get_db
from DataModels.HeatRateDataModel import HeartRateReading
from Schemas.HeartRateSchema import HeartRateReadingCreate, HeartRateReadingResponse
from AuthController.auth_dependencies import require_admin_or_device, get_current_user

router = APIRouter(prefix="/heart-rate-monitor", tags=["Heart Rate"])

#CREATE HEART RATE READING ENDPOINT
@router.post(
    "/createReading",
    response_model=HeartRateReadingResponse,
    dependencies=[Depends(require_admin_or_device)],
)
async def create_heart_rate_reading(
    payload: HeartRateReadingCreate,
    db: AsyncSession = Depends(get_db),
):
    if payload.heart_rate < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="heart_rate must be 0 or greater",
        )

    if payload.spo2 < 0 or payload.spo2 > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="spo2 must be between 0 and 100",
        )

    reading = HeartRateReading(
        device_id=payload.device_id,
        heart_rate=payload.heart_rate,
        spo2=payload.spo2,
        temperature=payload.temperature,
    )

    db.add(reading)
    await db.commit()
    await db.refresh(reading)

    return HeartRateReadingResponse(
        id=reading.id,
        device_id=reading.device_id,
        heart_rate=reading.heart_rate,
        spo2=reading.spo2,
        temperature=reading.temperature,
        created_at=reading.created_at,
    )

#GET HEART RATE READINGS ENDPOINT
@router.get(
    "/reading",
    response_model=list[HeartRateReadingResponse],
    dependencies=[Depends(get_current_user)],
)
async def get_heart_rate_readings(
    device_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    query = select(HeartRateReading).order_by(HeartRateReading.created_at.desc()).limit(limit)

    if device_id:
        query = (
            select(HeartRateReading)
            .where(HeartRateReading.device_id == device_id)
            .order_by(HeartRateReading.created_at.desc())
            .limit(limit)
        )

    result = await db.execute(query)
    readings = result.scalars().all()

    return [
        HeartRateReadingResponse(
            id=reading.id,
            device_id=reading.device_id,
            heart_rate=reading.heart_rate,
            spo2=reading.spo2,
            temperature=reading.temperature,
            created_at=reading.created_at,
        )
        for reading in readings
    ]

    

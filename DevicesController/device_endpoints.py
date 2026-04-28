from fastapi import APIRouter, Depends, HTTPException, status, Query
from requests import delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from AuthController.auth_dependencies import get_current_user
from db import get_db
from DataModels.DeviceLinkModel import DeviceLink
from DataModels.DeviceModel import Device
from DataModels.UserModel import User
from Schemas.DeviceSchema import DeviceResponse, LinkDeviceRequest, UpdateDeviceNameRequest

router = APIRouter(prefix="/devices", tags=["Devices"])

#LINK DEVICE ENDPOINT
@router.post("/link", response_model=DeviceResponse)
async def link_device(
    payload: LinkDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device_result = await db.execute(
        select(Device).where(Device.device_id == payload.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    link_result = await db.execute(
        select(DeviceLink).where(DeviceLink.device_pk == device.id)
    )
    existing_link = link_result.scalar_one_or_none()

    if existing_link:
        if existing_link.user_id == current_user.id:
            return DeviceResponse(
                id=device.id,
                device_id=device.device_id,
                name=device.name,
                device_type=device.device_type,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device is already linked to another user",
        )

    new_link = DeviceLink(
        user_id=current_user.id,
        device_pk=device.id,
    )

    db.add(new_link)
    await db.commit()

    return DeviceResponse(
        id=device.id,
        device_id=device.device_id,
        name=device.name,
        device_type=device.device_type,
    )

#GET MY DEVICES ENDPOINT
@router.get("/mine", response_model=list[DeviceResponse])
async def get_my_devices(
    device_type: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Device)
        .join(DeviceLink, DeviceLink.device_pk == Device.id)
        .where(DeviceLink.user_id == current_user.id)
    )

    if device_type is not None:
        query = query.where(Device.device_type == device_type)

    result = await db.execute(query)
    devices = result.scalars().all()

    return [
        DeviceResponse(
            id=device.id,
            device_id=device.device_id,
            name=device.name,
            device_type=device.device_type,
        )
        for device in devices
    ]

#GET ALL DEVICES ENDPOINT
@router.get("/all", response_model=list[DeviceResponse])
async def get_all_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device)
    )
    devices = result.scalars().all()

    return [
        DeviceResponse(
            id=device.id,
            device_id=device.device_id,
            name=device.name,
            device_type=device.device_type,
        )
        for device in devices
    ]

#UPDATE DEVICE NAME ENDPOINT
@router.patch("/{device_id}/name", response_model=DeviceResponse)
async def update_device_name(
    device_id: str,
    payload: UpdateDeviceNameRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_name = payload.name.strip()

    if not new_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device name cannot be empty",
        )

    result = await db.execute(
        select(Device)
        .join(DeviceLink, DeviceLink.device_pk == Device.id)
        .where(
            Device.device_id == device_id,
            DeviceLink.user_id == current_user.id,
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or not linked to current user",
        )

    device.name = new_name

    await db.commit()
    await db.refresh(device)

    return DeviceResponse(
        id=device.id,
        device_id=device.device_id,
        name=device.name,
        device_type=device.device_type,
    )


#REMOVE DEVICE RELATIONSHIP ENDPOINT
@router.delete("/{device_id}/relationship")
async def remove_device_relationship(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        device_result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = device_result.scalar_one_or_none()

        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        link_result = await db.execute(
            select(DeviceLink).where(
                DeviceLink.device_pk == device.id,
                DeviceLink.user_id == current_user.id,
            )
        )
        link = link_result.scalar_one_or_none()

        if not link:
            raise HTTPException(status_code=404, detail="Device relationship not found")

        await db.delete(link)
        await db.commit()

        return {"ok": True, "message": "Device relationship removed"}

    except HTTPException:
        raise
    except Exception as e:
        print("REMOVE DEVICE RELATIONSHIP ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
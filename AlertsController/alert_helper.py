from sqlalchemy import select

from DataModels.DeviceLinkModel import DeviceLink
from DataModels.DeviceModel import Device


async def get_user_ids_for_device(db, device_id: str) -> list[int]:
    result = await db.execute(
        select(DeviceLink.user_id)
        .join(Device, Device.id == DeviceLink.device_pk)
        .where(Device.device_id == device_id)
    )
    return list(result.scalars().all())

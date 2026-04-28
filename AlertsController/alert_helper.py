from sqlalchemy import select

from DataModels.DeviceLinkModel import DeviceLink
from DataModels.DeviceModel import Device
from DataModels.PushTokenModel import UserPushToken

# Helper function to get user IDs linked to a device
async def get_user_ids_for_device(db, device_id: str) -> list[int]:
    result = await db.execute(
        select(DeviceLink.user_id)
        .join(Device, Device.id == DeviceLink.device_pk)
        .where(Device.device_id == device_id)
    )
    return list(result.scalars().all())


# Helper function to get push tokens for a user
async def get_push_tokens_for_user(db, user_id: int) -> list[str]:
    result = await db.execute(
        select(UserPushToken.push_token).where(UserPushToken.user_id == user_id)
    )
    return list(result.scalars().all())

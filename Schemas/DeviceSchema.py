from pydantic import BaseModel


class LinkDeviceRequest(BaseModel):
    device_id: str

class UpdateDeviceNameRequest(BaseModel):
    name: str

class DeviceResponse(BaseModel):
    id: int
    device_id: str
    name: str | None = None
    device_type: int | None = None

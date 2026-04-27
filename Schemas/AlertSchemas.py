from pydantic import BaseModel
from typing import Optional


class DeviceEventCreate(BaseModel):
    device_id: str
    type: str
    title: Optional[str] = None
    message: Optional[str] = None
    severity: Optional[str] = "warning"
    metadata_json: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    device_id: str
    user_id: int
    type: str
    title: str
    message: str
    severity: str
    status: str
    metadata_json: Optional[str] = None

    class Config:
        from_attributes = True

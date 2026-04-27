from datetime import datetime

from pydantic import BaseModel


class FallReadingCreate(BaseModel):
    device_id: str

    ax: float
    ay: float
    az: float

    gx: float
    gy: float
    gz: float

    total_acc: float
    tilt: float
    tilt_change: float
    possible_fall: bool


class FallReadingResponse(BaseModel):
    id: int
    device_id: str

    ax: float
    ay: float
    az: float

    gx: float
    gy: float
    gz: float

    total_acc: float
    tilt: float
    tilt_change: float
    possible_fall: bool

    created_at: datetime

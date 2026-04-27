from datetime import datetime

from pydantic import BaseModel


class HeartRateReadingCreate(BaseModel):
    device_id: str
    heart_rate: int
    spo2: int
    temperature: float | None = None


class HeartRateReadingResponse(BaseModel):
    id: int
    device_id: str
    heart_rate: int
    spo2: int
    temperature: float | None = None
    created_at: datetime

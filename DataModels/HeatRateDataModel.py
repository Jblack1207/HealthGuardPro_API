from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Float, Integer
from db import Base


class HeartRateReading(Base):
    __tablename__ = "heart_rate_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    heart_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    spo2: Mapped[int] = mapped_column(Integer, nullable=False)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Float, Integer, Boolean

from db import Base


class FallReading(Base):
    __tablename__ = "fall_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    ax: Mapped[float] = mapped_column(Float, nullable=False)
    ay: Mapped[float] = mapped_column(Float, nullable=False)
    az: Mapped[float] = mapped_column(Float, nullable=False)

    gx: Mapped[float] = mapped_column(Float, nullable=False)
    gy: Mapped[float] = mapped_column(Float, nullable=False)
    gz: Mapped[float] = mapped_column(Float, nullable=False)

    total_acc: Mapped[float] = mapped_column(Float, nullable=False)
    tilt: Mapped[float] = mapped_column(Float, nullable=False)
    tilt_change: Mapped[float] = mapped_column(Float, nullable=False)
    possible_fall: Mapped[bool] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    alert_processed = mapped_column(Boolean, nullable=True, default=False, index=True)
    alert_processed_at = mapped_column(DateTime(timezone=True), nullable=True)
    alert_id = mapped_column(Integer, nullable=True)
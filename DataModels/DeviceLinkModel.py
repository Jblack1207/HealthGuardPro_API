from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class DeviceLink(Base):
    __tablename__ = "device_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    device_pk: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False, unique=True, index=True)
    linked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

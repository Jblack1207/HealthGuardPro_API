from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_type: Mapped[int | None] = mapped_column(Integer, nullable=True)

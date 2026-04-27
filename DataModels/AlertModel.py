from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from db import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    type = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, default="critical")
    status = Column(String(50), nullable=False, default="active")

    source_table = Column(String(100), nullable=True)
    source_row_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

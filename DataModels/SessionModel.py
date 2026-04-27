from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Boolean, BigInteger, ForeignKey
from db import Base

class ApiSession(Base):
    __tablename__ = "api_sessions"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger(),ForeignKey("users.id", ondelete="CASCADE"),index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

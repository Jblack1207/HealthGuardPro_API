from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, BigInteger
from db import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[int] = mapped_column(BigInteger(), default=0)
    is_active: Mapped[int] = mapped_column(BigInteger(), default=1)
    firebase_uid: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
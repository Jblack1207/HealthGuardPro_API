import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = (
    f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

class Base(DeclarativeBase):
    pass

#async engine generation - allows connection limiting and overflow - should keep connections fast (Note for Me: Check max conns against SQL DB)
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping= True,
    pool_recycle= 1800,
    pool_size = 10,
    max_overflow= 20
)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

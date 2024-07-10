from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, DateTime, Text, Time, func, UniqueConstraint
)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime
from databases import Database

DATABASE_URL = "postgresql+asyncpg://admin:password@localhost/estate"

database = Database(DATABASE_URL)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger)
    city = Column(String(40))
    district = Column(String(40), default='')
    rooms = Column(Integer, default=-1)
    min_price = Column(Integer)
    max_price = Column(Integer)
    status = Column(Boolean, default=True)
    last_msg_id = Column(Integer, default=0)
    language = Column(String(5), default='en')
    time_start_sent = Column(Time)
    time_finish_sent = Column(Time)
    vip = Column(Boolean, default=True)


class Estate(Base):
    __tablename__ = "estates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource = Column(Integer)
    datetime = Column(DateTime, default=datetime.now)
    city = Column(String(20))
    district = Column(String(20), default='')
    rooms = Column(Integer, default=-1)
    price = Column(Integer)
    url = Column(Text, default='')
    group_id = Column(String(32), default='')
    msg_id = Column(Integer, default=-1)
    msg = Column(Text)
    language = Column(String(4))
    msg_ru = Column(Text)
    msg_en = Column(Text)
    msg_el = Column(Text)


async def create_tables():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    import asyncio

    asyncio.run(create_tables())

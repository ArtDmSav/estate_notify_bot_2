from datetime import datetime

from databases import Database
from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, DateTime, Text, Time, func
)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base

from config.data import DATABASE_URL

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

    # NEW fields
    pet = Column(Boolean, default=False)
    new_building = Column(Boolean, default=False)
    access = Column(Boolean, default=False)
    username = Column(String(32))
    end_of_access = Column(DateTime)
    blocked = Column(Integer)
    advt = Column(Boolean)
    last_advt_time = Column(DateTime, default=func.now())
    last_update_msgs_time = Column(DateTime, default=func.now())
    reg_dt = Column(DateTime, default=func.now())


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

    # NEW fields
    pet = Column(Boolean)
    new_building = Column(Boolean)


async def create_tables():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    import asyncio

    asyncio.run(create_tables())

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config.data import DB_LOGIN, DB_PASSWORD, DB_NAME
from .create import Estate, User

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

DATABASE_URL = f"postgresql+asyncpg://{DB_LOGIN}:{DB_PASSWORD}@localhost/{DB_NAME}"

# Создание асинхронного двигателя и фабрики сессий
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_last_estate_id() -> int:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(func.max(Estate.id))
            )
            last_id = result.scalar_one_or_none()
            return last_id if last_id is not None else 0


async def insert_user_tg(chat_id: int, city: str, min_value: int, max_value: int, language: str, status: bool = True):
    last_estate_id = await get_last_estate_id()
    async with async_session() as session:
        async with session.begin():
            # Поиск пользователя по chat_id
            result = await session.execute(
                select(User).where(User.chat_id == chat_id)
            )
            user = result.scalar_one_or_none()

            if user:
                # Обновление существующего пользователя
                stmt = (
                    update(User).
                    where(User.chat_id == chat_id).
                    values(
                        city=city,
                        min_price=min_value,
                        max_price=max_value,
                        status=status,
                        language=language,
                        last_msg_id=last_estate_id
                    )
                )
                await session.execute(stmt)
            else:
                # Добавление нового пользователя
                new_user = User(
                    chat_id=chat_id,
                    city=city,
                    min_price=min_value,
                    max_price=max_value,
                    status=status,
                    language=language,
                    last_msg_id=last_estate_id
                )
                session.add(new_user)
            await session.commit()


async def deactivate_user(chat_id) -> bool:
    async with async_session() as session:
        async with session.begin():
            # Поиск пользователя по chat_id
            result = await session.execute(
                select(User).where(User.chat_id == chat_id)
            )
            user = result.scalar_one_or_none()

            if user:
                # Обновление статуса пользователя на False
                stmt = (
                    update(User).
                    where(User.chat_id == chat_id).
                    values(status=False)
                )
                await session.execute(stmt)
                await session.commit()
                return True
            else:
                return False


async def get_active_usual_users() -> User:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User).where((User.status == True) & (User.vip != True))
            )
            active_users = result.scalars().all()
            return active_users


async def get_active_vip_users() -> User:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User).where((User.status == True) & (User.vip == True))
            )
            active_users = result.scalars().all()
            return active_users


async def get_user_language(chat_id: str) -> str:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User.language).where(User.chat_id == chat_id)
            )
            language = result.scalar_one_or_none()
            return language if language is not None else ''


async def get_estates(last_estate_id, city, min_price, max_price):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Estate).where(
                    (Estate.id > last_estate_id) &
                    (Estate.city == city) &
                    (Estate.price >= min_price) &
                    (Estate.price <= max_price)
                )
            )
            estates = result.scalars().all()
            return estates


async def update_last_msg_id(chat_id, last_msg_id) -> None:
    async with async_session() as session:
        async with session.begin():
            stmt = (
                update(User).
                where(User.chat_id == chat_id).
                values(last_msg_id=last_msg_id)
            )
            await session.execute(stmt)
            await session.commit()


async def get_user_by_chat_id(chat_id: int):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User).where(User.chat_id == chat_id)
            )
            user = result.scalar_one_or_none()
            return user if user is not None else 0


async def get_estates_in_time_range(city: str, min_price: int, max_price: int, range_time: int, field_msg: str):
    async with async_session() as session:
        async with session.begin():
            threshold_time = datetime.now() - timedelta(hours=range_time)
            msg_lang = getattr(Estate, field_msg)

            result = await session.execute(
                select(msg_lang, Estate.url)
                .where(
                    (Estate.datetime >= threshold_time) &
                    (Estate.city == city) &
                    (Estate.price >= min_price) &
                    (Estate.price <= max_price)
                )
            )
            estates = result.all()
            return estates


async def update_user_language(chat_id: int, language: str) -> None:
    async with async_session() as session:
        async with session.begin():
            # Проверка существования пользователя с заданным chat_id
            result = await session.execute(
                select(User).where(User.chat_id == chat_id)
            )
            user = result.scalar_one_or_none()

            # Обновление языка пользователя
            stmt = (
                update(User).
                where(User.chat_id == chat_id).
                values(language=language)
            )
            await session.execute(stmt)
            await session.commit()


# Admin functions
# ----------------------------------------------

async def get_all_users():
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User))
            users = result.scalars().all()
            return users


async def get_last_10_estate_ids():
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Estate.id).order_by(Estate.id.desc()).limit(10)
            )
            last_10_ids = result.scalars().all()
            return last_10_ids


async def get_estate_by_id(estate_id: int):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Estate).where(Estate.id == estate_id)
            )
            estate = result.scalar_one_or_none()
            return estate


async def get_estate_by_group_id_and_msg_id(group_id: str, msg_id: int):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Estate).where(
                    (Estate.group_id == group_id) &
                    (Estate.msg_id == msg_id)
                )
            )
            estate = result.scalar_one_or_none()
            return estate

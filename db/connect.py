import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .create import Estate, User

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

DATABASE_URL = "postgresql+asyncpg://admin:password@localhost/estate"

# Создание асинхронного двигателя и фабрики сессий
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def insert_user_tg(chat_id: int, city: str, min_value: int, max_value: int, language: str, status: bool = True):
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
                        language=language
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
                    language=language
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


async def get_active_users() -> User:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User).where(User.status == True)
            )
            active_users = result.scalars().all()
            return active_users


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

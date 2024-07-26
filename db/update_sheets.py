import asyncio

import asyncpg

from config.data import DATABASE_URL


async def add_columns():
    conn = await asyncpg.connect(DATABASE_URL)

    # Добавление новых столбцов в таблицу users
    user_columns = [
        "pet BOOLEAN DEFAULT FALSE",
        "new_building BOOLEAN DEFAULT FALSE",
        "access BOOLEAN DEFAULT FALSE",
        "username VARCHAR(32)",
        "end_of_access TIMESTAMP",
        "blocked INTEGER",
        "advt BOOLEAN",
        "last_advt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "last_update_msgs_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "reg_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    ]

    for column in user_columns:
        try:
            await conn.execute(f"ALTER TABLE users ADD COLUMN {column}")
        except asyncpg.exceptions.DuplicateColumnError:
            pass  # Колонка уже существует

    # Добавление новых столбцов в таблицу estates
    estate_columns = [
        "pet BOOLEAN",
        "new_building BOOLEAN",
    ]

    for column in estate_columns:
        try:
            await conn.execute(f"ALTER TABLE estates ADD COLUMN {column}")
        except asyncpg.exceptions.DuplicateColumnError:
            pass  # Колонка уже существует

    await conn.close()


# Пример использования
if __name__ == "__main__":
    asyncio.run(add_columns())

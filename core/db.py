import os
from dotenv import load_dotenv
import asyncpg
from datetime import date
import json

class Database:
    def __init__(self):
        load_dotenv()
        self.pool = None


    async def connect(self):
        """Создаёт пул соединений с PostgreSQL"""
        self.pool = await asyncpg.create_pool(
            host="localhost",
            database="bonch",
            user="postgres",
            password=os.getenv("DB_PASSWORD"),
            min_size=1,
            max_size=10
        )


    async def close(self):
        """Закрывает пул соединений"""
        await self.pool.close()
        

    async def check_scheduler(self, current_date: date):
        """
        Получает расписание на текущий день.
        Если на текущий день ничего нет — возвращает ближайшую дату после текущей.
        Возвращает: (список записей, bool — True если есть на сегодня)
        """
        async with self.pool.acquire() as conn:
            # Сначала проверяем расписание на текущий день
            today_schedule = await conn.fetch("""
                SELECT * FROM schedule 
                WHERE date::date = $1 AND sect = 'IKB-31'
                ORDER BY pair::int ASC
            """, current_date)

            if today_schedule:
                return today_schedule, True

            # Если на сегодня ничего нет — ищем ближайшую будущую дату
            next_schedule = await conn.fetch("""
                SELECT * FROM schedule 
                WHERE date = (
                    SELECT MIN(date) 
                    FROM schedule 
                    WHERE sect = 'IKB-31' AND date > $1
                ) 
                AND sect = 'IKB-31'
                ORDER BY pair::int ASC
            """, current_date)

            return next_schedule, False
        
        
    async def get_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("""
                SELECT * FROM users WHERE id = $1
            """, user_id)
            return user


    async def add_user(self, user_id: int, username: str, full_name: str, group: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (telegram_id, username, full_name, group) VALUES ($1, $2, $3, $4)
            """, user_id, username, full_name, group)
            
            
    async def load_reminders(self):
        async with self.pool.acquire() as conn:
            reminders = await conn.fetch("""
                SELECT * FROM reminders
            """)
            return reminders


    async def get_reminder(self, message: str = None, user_id: int = None):
        async with self.pool.acquire() as conn:
            if message: 
                reminder = await conn.fetch("""
                    SELECT * FROM reminders WHERE message = $1
                """, message)
                return reminder
            if user_id:
                reminder = await conn.fetch("""
                    SELECT * FROM reminders WHERE user_id = $1
                """, user_id)
                return reminder


    async def save_reminders(self, reminder):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO reminders (chat_id, message, deadline, intervals)
                VALUES ($1, $2, $3, $4)
                """,
                (
                    reminder[0],                   # user_id
                    reminder[1],                   # user_data как JSON
                    reminder[2],                   # deadline (datetime)
                    json.dumps(reminder[3])        # intervals как JSON
                )
            )
            await conn.commit() 
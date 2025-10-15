import os
from unittest import result
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
        if self.pool:
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
        
        
    async def get_user(self, chat_id: int):
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("""
                SELECT * FROM users WHERE chat_id = $1
            """, chat_id)
            return user


    async def add_user(self, chat_id: int, username: str, full_name: str, group: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (chat_id, username, full_name, sect) VALUES ($1, $2, $3, $4)
            """, chat_id, username, full_name, group)
            
            
    async def load_reminders(self):
        async with self.pool.acquire() as conn:
            reminders = await conn.fetch("""
                SELECT * FROM reminders
            """)
            return reminders


    async def get_reminder(self, message: str = None, chat_id: int = None):
        async with self.pool.acquire() as conn:
            if message: 
                reminder = await conn.fetch("""
                    SELECT * FROM reminders WHERE message = $1
                """, message)
                return reminder
            if chat_id:
                reminder = await conn.fetch("""
                    SELECT * FROM reminders WHERE chat_id = $1
                """, chat_id)
                return reminder


    async def save_reminders(self, reminder):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO reminders (chat_id, message, deadline, intervals)
                VALUES ($1, $2, $3, $4)
                """,
                (
                    reminder[0],                   # chat_id
                    reminder[1],                   # user_data как JSON
                    reminder[2],                   # deadline (datetime)
                    json.dumps(reminder[3])        # intervals как JSON
                )
            )
            await conn.commit() 


    async def get_deadlines(self):
        async with self.pool.acquire() as conn:
            deadlines = await conn.fetch("""
                SELECT chat_id, message FROM reminders
            """)
            return deadlines


    async def get_queue(self, date: date):
        async with self.pool.acquire() as conn:
            queue = await conn.fetch("""
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY date ASC) AS id,
                    subject,
                    brigade_number
                FROM queue
                WHERE date = $1
            """, date)
            return queue



    async def take_a_place(self, chat_id: int, subject: str, brigade_number: int):
        async with self.pool.acquire() as conn:
            abbriviatures = {
                "ASTRA": "Безопасность Astra-Linux",
                "ББЛС": "Безопасность беспроводных локальных сетей",
                "ЗОССУ": "Защита операционных систем сетевых устройств",
                "ЗПИД": "Защита программ и данных",
                "МИСКЗИ": "Методы и средства криптографической защиты информации",
                "ОМВКС": "Основы маршрутизации в компьютерных сетях",
                "ПАСЗИ": "Программно-аппаратные средства защиты информации",
                "ОИПОИБ": "Организационное и правовое обеспечение информационной безопасности"
            }
            
            if subject in abbriviatures:
                full_subject = abbriviatures[subject]

                result = await conn.execute("""
                    INSERT INTO queue (chat_id, subject, brigade_number, date)
                    SELECT 
                        u.chat_id, 
                        $2 AS subject, 
                        $3 AS brigade_number, 
                        s.date
                    FROM users u
                    JOIN schedule s 
                        ON s.sect = u.sect 
                    AND s.subject = $2
                    AND s.date >= NOW() 
                    AND s.date < NOW() + INTERVAL '2 days'
                    WHERE u.chat_id = $1
                """, chat_id, full_subject, brigade_number)
                
                # result выглядит как "INSERT 0 1"
                if result.endswith("1"):
                    return True
                else:
                    return False

            else:
                return False

    
    async def get_service_topic(self, service):
        async with self.pool.acquire() as conn:
            topic = await conn.fetch("""
                SELECT * FROM service_topics WHERE service = $1
            """, service)
            return topic

    async def set_service_topic(self, service, chat_id, thread_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO service_topics (service, chat_id, thread_id)
                VALUES ($1, $2, $3)
            """, service, chat_id, thread_id)
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
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
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



    async def take_a_place(self, sect: str, subject: str, brigade_number: int):
        async with self.pool.acquire() as conn:
            subject = subject.upper()
            print(subject)
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
                print(sect, full_subject, brigade_number)
                try:
                    result = await conn.execute("""
                        INSERT INTO queue (sect, subject, brigade_number, date)
                        SELECT 
                            $1 AS sect, 
                            $2 AS subject, 
                            $3 AS brigade_number, 
                            s.date
                        FROM schedule s
                        WHERE s.sect = $1
                        AND s.subject = $2
                        AND s.date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 days'
                        AND s.lesson_type IN ('Практические занятия', 'Лабораторная работа')
                    """, sect, full_subject, brigade_number)
                    return result.endswith("1")

                except asyncpg.UniqueViolationError:
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

    async def get_user_info(self, user_id: int):
        async with self.pool.acquire() as conn:
            user_info = await conn.fetchrow("""
                SELECT * FROM users WHERE chat_id = $1
            """, user_id)
            return user_info
        
    async def get_today_schedule(self, sect):
        async with self.pool.acquire() as conn:
            schedule = await conn.fetch("""
                SELECT date, pair, subject, auditorium, teacher, lesson_type FROM schedule WHERE sect = $1 AND date = CURRENT_DATE
            """, sect)
            return schedule
    
    async def save_brigade(self, brigade, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET brigade = $1 WHERE chat_id = $2
            """, brigade, user_id)
            
    async def get_subjects(self):
        """Возвращает уникальные предметы с бригадами от 1 до 15"""
        async with self.pool.acquire() as conn:
            subjects = await conn.fetch("""
                SELECT DISTINCT subject FROM schedule
            """)
            return subjects


    async def get_user_brigade(self, user_id: int):
        query = "SELECT brigade FROM users WHERE chat_id = $1"
        result = await self.pool.fetchval(query, user_id)
        return result

    async def save_issue_report(self, user_id: int, issue_description: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO issue_reports (user_id, description, created_at)
                VALUES ($1, $2, NOW())
            """, user_id, issue_description)
            
    async def get_distinct_teachers(self):
        async with self.pool.acquire() as conn:
            teachers = await conn.fetch("""
                SELECT DISTINCT teacher FROM schedule order by teacher asc
            """)
            return teachers
        
    async def get_teacher_schedule(self, teacher):
        async with self.pool.acquire() as conn:
            schedule = await conn.fetch("""
                SELECT date, pair, subject, auditorium, lesson_type, sect FROM schedule WHERE teacher = $1 and date>=CURRENT_DATE and date<=CURRENT_DATE + INTERVAL '7 days' order by date asc
            """, teacher)
            return schedule
        
    async def get_week_schedule(self, sect):
        async with self.pool.acquire() as conn:
            schedule = await conn.fetch("""
                SELECT date, pair, subject, auditorium, teacher, lesson_type FROM schedule WHERE sect = $1 and date>NOW() and date<NOW() + INTERVAL '7 days'
            """, sect)
            return schedule
        
    async def get_user_subjects(self, user_id: int):
        async with self.pool.acquire() as conn:
            subjects = await conn.fetch("""
                SELECT DISTINCT subject FROM schedule WHERE sect = (SELECT sect FROM users WHERE chat_id = $1) order by subject asc
            """, user_id)
            return subjects
    
    async def add_user_task(self, user_id: int, subject: str, task_type: str, is_brigade: bool):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tasks (user_id, subject, task_type, is_brigade)
                VALUES ($1, $2, $3, $4)
            """, user_id, subject, task_type, is_brigade)
            
    async def get_user_tasks(self, user_id: int):
        async with self.pool.acquire() as conn:
            tasks = await conn.fetch("""
                -- Одиночные задачи пользователя
                SELECT * 
                FROM tasks
                WHERE user_id = $1
                AND is_brigade = false
                AND (deadline >= CURRENT_DATE OR deadline IS NULL)
                
                UNION
                
                -- Бригадные задачи (общие для группы)
                SELECT t.* 
                FROM tasks t
                JOIN users u1 ON t.user_id = u1.chat_id
                JOIN users u2 ON u1.sect = u2.sect AND u1.brigade = u2.brigade
                WHERE u2.chat_id = $1
                AND t.is_brigade = true
                AND u1.brigade IS NOT NULL
                AND (t.deadline >= CURRENT_DATE OR t.deadline IS NULL)
                
                ORDER BY deadline ASC NULLS LAST
            """, user_id)
            return tasks
        
    async def update_task_deadline(self, user_id: int, task_name: str, new_deadline: date):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE tasks
                SET deadline = $1
                WHERE user_id = $2 AND task_type = $3
            """, new_deadline, user_id, task_name)
            
    async def update_task_description(self, user_id: int, task_name: str, new_description: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE tasks
                SET descriptions = $1
                WHERE user_id = $2 AND task_type = $3
            """, new_description, user_id, task_name)
            
    async def update_task_progress(self, user_id: int, task_name: str, new_progress: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE tasks
                SET progress = $1
                WHERE user_id = $2 AND task_type = $3
            """, new_progress, user_id, task_name)
            
    async def update_user_group(self, user_id: int, new_group: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users
                SET sect = $1
                WHERE chat_id = $2
            """, new_group, user_id)
            
    async def update_user_brigade(self, user_id: int, new_brigade: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users
                SET brigade = $1
                WHERE chat_id = $2
            """, new_brigade, user_id)
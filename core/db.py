import os
from unittest import result
from dotenv import load_dotenv
import asyncpg
from datetime import date, datetime
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

    async def get_user_info(self, chat_id: int):
        async with self.pool.acquire() as conn:
            user_info = await conn.fetchrow("""
                SELECT * FROM users WHERE chat_id = $1
            """, chat_id)
            return user_info
        
    async def get_today_schedule(self, sect):
        async with self.pool.acquire() as conn:
            schedule = await conn.fetch("""
                SELECT date, pair, subject, auditorium, teacher, lesson_type FROM schedule WHERE sect = $1 AND date = CURRENT_DATE
            """, sect)
            return schedule
    
    async def save_brigade(self, brigade, chat_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET brigade = $1 WHERE chat_id = $2
            """, brigade, chat_id)
            
    async def get_subjects(self):
        """Возвращает уникальные предметы с бригадами от 1 до 15"""
        async with self.pool.acquire() as conn:
            subjects = await conn.fetch("""
                SELECT DISTINCT subject FROM schedule
            """)
            return subjects


    async def get_user_brigade(self, chat_id: int):
        query = "SELECT brigade FROM users WHERE chat_id = $1"
        result = await self.pool.fetchval(query, chat_id)
        return result

    async def save_issue_report(self, chat_id: int, issue_description: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO issue_reports (chat_id, description, created_at)
                VALUES ($1, $2, NOW())
            """, chat_id, issue_description)
            
    async def get_distinct_teachers(self, user):
        async with self.pool.acquire() as conn:
            teachers = await conn.fetch("""
                SELECT DISTINCT teacher
                FROM schedule 
                WHERE sect=$1 
                order by teacher asc
            """, user[4])
            return teachers
        
    async def get_teacher_schedule(self, teacher):
        async with self.pool.acquire() as conn:
            schedule = await conn.fetch("""
                SELECT date, pair, subject, auditorium, lesson_type, sect 
                FROM schedule 
                WHERE teacher = $1 
                and date>=CURRENT_DATE 
                and date<=CURRENT_DATE + INTERVAL '7 days' 
                ORDER BY date, pair, subject, auditorium, lesson_type, sect
            """, teacher)
            return schedule
        
    async def get_week_schedule(self, sect):
        async with self.pool.acquire() as conn:
            schedule = await conn.fetch("""
                SELECT date, pair, subject, auditorium, teacher, lesson_type FROM schedule WHERE sect = $1 and date>NOW() and date<NOW() + INTERVAL '7 days'
            """, sect)
            return schedule
        
    async def get_user_subjects(self, chat_id: int):
        async with self.pool.acquire() as conn:
            subjects = await conn.fetch("""
                SELECT DISTINCT subject FROM schedule WHERE sect = (SELECT sect FROM users WHERE chat_id = $1) order by subject asc
            """, chat_id)
            return subjects
    
    async def add_user_task(self, chat_id: int, subject: str, task_type: str, is_brigade: bool):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tasks (chat_id, subject, task_type, is_brigade)
                VALUES ($1, $2, $3, $4)
            """, chat_id, subject, task_type, is_brigade)
            
    async def get_user_tasks(self, chat_id: int):
        async with self.pool.acquire() as conn:
            tasks = await conn.fetch("""
                -- Одиночные задачи пользователя
                SELECT * 
                FROM tasks
                WHERE chat_id = $1
                AND is_brigade = false
                AND (deadline >= CURRENT_DATE OR deadline IS NULL)
                
                UNION
                
                -- Бригадные задачи (общие для группы)
                SELECT t.* 
                FROM tasks t
                JOIN users u1 ON t.chat_id = u1.chat_id
                JOIN users u2 ON u1.sect = u2.sect AND u1.brigade = u2.brigade
                WHERE u2.chat_id = $1
                AND t.is_brigade = true
                AND u1.brigade IS NOT NULL
                AND (t.deadline >= CURRENT_DATE OR t.deadline IS NULL)
                
                ORDER BY deadline, subject, task_type ASC NULLS LAST
            """, chat_id)
            return tasks
        
    async def update_task_deadline(self, chat_id: int, task_type: str, deadline: date, subject: str):
        """Обновляет дедлайн задачи по chat_id, task_type И subject"""
        query = """
            UPDATE tasks 
            SET deadline = $1 
            WHERE chat_id = $2 AND task_type = $3 AND subject = $4
        """
        await self.pool.execute(query, deadline, chat_id, task_type, subject)

            
    async def update_task_description(self, chat_id: int, task_type: str, description: str, subject: str):
        """Обновляет описание задачи по chat_id, task_type И subject"""
        query = """
            UPDATE tasks 
            SET descriptions = $1 
            WHERE chat_id = $2 AND task_type = $3 AND subject = $4
        """
        await self.pool.execute(query, description, chat_id, task_type, subject)

            
    async def update_task_progress(self, chat_id: int, task_type: str, progress: int, subject: str):
        """Обновляет прогресс задачи по chat_id, task_type И subject"""
        query = """
            UPDATE tasks 
            SET progress = $1 
            WHERE chat_id = $2 AND task_type = $3 AND subject = $4
        """
        await self.pool.execute(query, progress, chat_id, task_type, subject)

            
    async def update_user_group(self, chat_id: int, new_group: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users
                SET sect = $1
                WHERE chat_id = $2
            """, new_group, chat_id)
            
    async def update_user_brigade(self, chat_id: int, new_brigade: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users
                SET brigade = $1
                WHERE chat_id = $2
            """, new_brigade, chat_id)
            
    async def delete_user_task(self, chat_id: int, task_type: str, subject: str):
        """
        Удаляет задачу:
        - либо свою одиночную,
        - либо любую бригадную из той же группы/бригады
        """
        query = """
            DELETE FROM tasks t
            USING users u_request, users u_task
            WHERE t.task_type = $2
            AND t.subject = $3
            AND (
                -- одиночная задача пользователя
                t.chat_id = $1
                OR
                -- бригадная задача в той же бригаде
                (t.is_brigade = true
                AND t.chat_id = u_task.chat_id
                AND u_request.chat_id = $1
                AND u_request.sect = u_task.sect
                AND u_request.brigade = u_task.brigade
                )
            )
            AND u_task.chat_id = t.chat_id
            AND u_request.chat_id = $1
        """
        await self.pool.execute(query, chat_id, task_type, subject)


    async def remove_user_data(self, chat_id):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM users
                WHERE chat_id = $1
                """,
                chat_id, 
            )
    
    async def create_task_pack(self, tasks: list[tuple]):
        async with self.pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO tasks (chat_id, task_type, subject, is_brigade)
                VALUES ($1, $2, $3, $4)
            """, tasks)

    async def get_schedule(self, sect):
        async with self.pool.acquire() as conn:
            schedule = await conn.fetch("""
                select * from schedule where sect=$1 and date >= $2 and lesson_type in ('Практические занятия', 'Лабораторная работа')
            """, sect, datetime.now().date())
            return schedule
        
    async def get_distinct_sects(self):
        async with self.pool.acquire() as conn:
            schedule = await conn.fetch("""
                SELECT DISTINCT sect FROM schedule order by sect asc
            """)
            return schedule
        
    async def update_tasks(self, updates: list[dict]) -> int:
        """
        Массово обновляет дедлайны задач.
        
        Args:
            updates: Список словарей с ключами:
                - chat_id: ID пользователя
                - task_type: Название задачи
                - subject: Предмет
                - deadline: Новый дедлайн
                
        Returns:
            Количество обновлённых задач
        """
        if not updates:
            return 0
        
        query = """
            UPDATE tasks
            SET deadline = $4
            WHERE chat_id = $1 AND task_type = $2 AND subject = $3
        """
        
        # Подготавливаем данные для executemany
        data = [
            (
                update['chat_id'],
                update['task_type'],
                update['subject'],
                update['deadline']
            )
            for update in updates
        ]
        
        await self.pool.executemany(query, data)
        return len(data)

    async def get_deadlines(self):
        async with self.pool.acquire() as conn:
            # все пользователи
            users = await conn.fetch("""
                SELECT chat_id, sect, brigade
                FROM users
            """)

            # построим dict для быстрого поиска по (sect, brigade)
            group_users = {}
            for u in users:
                key = (u['sect'], u['brigade'])
                group_users.setdefault(key, []).append(u['chat_id'])

            # все задачи с дедлайнами
            tasks = await conn.fetch("""
                SELECT *
                FROM tasks
                WHERE deadline IS NOT NULL
                AND deadline >= CURRENT_DATE
            """)

            result = []

            for task in tasks:
                if not task['is_brigade']:
                    # одиночная задача — отправляем только автору
                    result.append((task['chat_id'], task['subject'], task['deadline']))
                else:
                    # бригадная задача — ищем всех пользователей в одной группе с автором
                    author = next(u for u in users if u['chat_id'] == task['chat_id'])
                    recipients = group_users.get((author['sect'], author['brigade']), [])
                    for chat_id in recipients:
                        result.append((chat_id, task['subject'], task['deadline']))

            return result

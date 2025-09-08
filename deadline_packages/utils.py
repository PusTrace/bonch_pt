import json
from pathlib import Path
import psycopg2
import os
from dotenv import load_dotenv

class Database:
    def __init__(self):
        load_dotenv()
        self.conn = psycopg2.connect(
            host="localhost",
            database="bonch",
            user="postgres",
            password=os.getenv("DB_PASSWORD")
        )
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def check_scheduler(self, current_date):
        self.cur.execute("""
            SELECT * FROM schedule 
            WHERE date = %s AND sect = 'IKB-31'
            ORDER BY pair::int ASC
        """, (current_date,))
        today_schedule = self.cur.fetchall()

        if len(today_schedule) == 0:
            self.cur.execute("""
                SELECT * FROM schedule 
                WHERE date = (
                    SELECT MIN(date) 
                    FROM schedule 
                    WHERE sect = 'IKB-31' AND date > %s
                ) 
                AND sect = 'IKB-31'
                ORDER BY pair::int ASC
            """, (current_date,))
            return self.cur.fetchall(), False
        else:
            return today_schedule, True



def load_reminders():
    db = Database()
    db.cur.execute("SELECT * FROM reminders")
    reminders = db.cur.fetchall()
    db.close()
    return reminders

def save_reminders(reminder):
    db = Database()
    db.cur.execute(
        """
        INSERT INTO reminders (chat_id, message, deadline, intervals)
        VALUES (%s, %s, %s, %s)
        """,
        (
            reminder[0],                   # user_id
            reminder[1],                   # user_data как JSON
            reminder[2],                   # deadline (datetime)
            json.dumps(reminder[3])        # intervals как JSON
        )
    )
    db.commit()
    db.close()


import os
from dotenv import load_dotenv
import psycopg2

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
            WHERE date::date = %s AND sect = 'IKB-31'
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
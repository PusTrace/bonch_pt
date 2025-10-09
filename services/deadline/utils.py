import json

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


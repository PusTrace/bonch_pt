![Status](https://img.shields.io/badge/status-in%20development-yellow)

# University Schedule Bot 🎓

A Telegram bot for managing university schedules, assignments, and academic tasks. Built with aiogram 3.x and PostgreSQL.

## Features

### 📅 Schedule Management
- View today's schedule
- View weekly schedule
- Search schedules by teacher
- Automatic schedule parsing and updates

### 📝 Task Management
- Add assignments (individual or team-based)
- Set deadlines
- Track progress (0-100%)
- Add descriptions
- View all tasks with filtering
- Delete completed tasks

### 👥 Multi-user Support
- Personal tasks
- Team/brigade tasks (shared with classmates)
- Group-based organization

## Tech Stack

- **Python 3.13+**
- **aiogram 3.22** - Telegram Bot framework
- **PostgreSQL** - Database
- **asyncpg** - Async PostgreSQL driver
- **APScheduler** - Task scheduling
- **Docker** - Containerization

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/PusTrace/bonch_pt.git
cd bonch_pt
```
2. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

5. Set up PostgreSQL database:

```sql
CREATE DATABASE your_db_name;
```

6. Run the bot:

```bash
python bonch.py
```

### Docker Deployment

1. Configure `.env` file with your credentials
    
2. Build and run:
    

```bash
docker-compose up -d
```

## Database Schema

### Main Tables

**users**

- `chat_id` (PK) - Telegram user ID
- `username` - Telegram username
- `full_name` - User's full name
- `sect` - Study group
- `brigade` - Team number (for team tasks)

**tasks**

- `task_id` (PK) - Auto-increment ID
- `user_id` (FK) - Owner of the task
- `subject` - Course name
- `task_type` - Task name/type
- `is_brigade` - Individual or team task
- `deadline` - Due date
- `descriptions` - Task description
- `progress` - Completion percentage (0-100)

**schedule**

- `date` - Date
- `pair` - Class number (1-6)
- `subject` - Course name
- `auditorium` - Room number
- `teacher` - Professor name
- `lesson_type` - Lecture/Lab/Practice
- `sect` - Study group

## Configuration

### Adding Your University Schedule

To adapt this bot for your university, you need to start the schedule parser in `services/parse_schedule.py`

## Usage

### First Time Setup

1. Start the bot with `/start`
2. Enter your study group (e.g., `CS-101`)
3. Optionally set your brigade number for team tasks

### Commands

- `/start` - Initialize bot and view today's schedule

### Main Menu

- **Statistics 📊** - View schedules and teachers
- **My Data** - Manage your profile
- **Tasks** - Manage assignments

### Task Management

- **Add Task** - Create new assignment
- **Show Tasks** - View all your tasks
- **Update Deadline** - Change due date
- **Update Description** - Edit task details
- **Update Progress** - Set completion percentage
- **Delete Task** - Remove completed tasks

## Project Structure

```
bonch_pt/
├── bonch.py              # Main entry point
├── core/
│   ├── db.py            # Database layer
│   ├── keyboards.py     # Reply keyboards
│   ├── utils.py         # Formatting utilities
│   ├── states.py        # FSM states
│   └── middlewares.py   # Custom middlewares
├── services/
│   ├── start.py         # Start command & registration
│   ├── schedule.py      # Schedule viewing
│   ├── tasks.py         # Task management
│   ├── user.py          # User profile
│   └── parse_schedule.py # Schedule parser
└── docker-compose.yml   # Docker configuration
```

## Customization for Other Universities

### Step 1: Schedule Parser

Create your own parser in `services/parse_schedule.py`:

- Scrape your university's schedule website
- Parse the data into the standard format
- Store in database

### Step 2: Adjust Time Slots

Update `PAIR_TIMES` in `core/utils.py` to match your class schedule.

### Step 3: Localization (Optional)

Replace all Russian text strings with your preferred language:

- Button labels in `core/keyboards.py`
- Messages in `services/*.py`

### Step 4: Group Format

Modify group name validation in `services/start.py` if your university uses a different naming convention.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request



---
## .env configuration
```env
# Telegram Bot
BOT_TOKEN=BOT_TOKEN

# for log error(optional)
TG_BOT_TOKEN=TG_BOT_TOKEN
TG_CHAT_IDS=TG_CHAT_IDS

# PostgreSQL Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=DB_PASSWORD
DB_NAME=bonch

# for parse schedule
PASSWORD=PASSWORD
LOGIN=LOGIN
```

---
## License

MIT License - feel free to use this project for your own university.

---

**Note:** This bot was originally developed for SPbSUT (Bonch-Bruevich University) but can be adapted for any university with minor modifications.
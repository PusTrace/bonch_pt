from core.start import cmd_start
from services.deadline.router import router as deadlines_router

def register_routers(dp):
    dp.include_router(cmd_start)
    dp.include_router(deadlines_router)


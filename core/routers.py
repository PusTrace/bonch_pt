from services.deadlines.router import router as deadlines_router

def register_routers(dp):
    dp.include_router(deadlines_router)


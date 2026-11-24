import uvicorn
from fastapi import FastAPI

from repository import PostgreSQLDB


class HttpServer:
    def __init__(self, db: PostgreSQLDB, host: str = "0.0.0.0", port: int = 8005):
        self.host = host
        self.port = port
        self.db = db

        self.app = FastAPI(title="sport")

        @self.app.get("/")
        async def read_root():
            return {"status": "live"}

        @self.app.get("/health")
        async def health():
            return {"status": "live"}

        @self.app.get("/exercises")
        async def get_exercises(user_id: int, limit: int | None = None):
            return {"status": "live"}

        self.config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            reload=True,
        )

        self.server = uvicorn.Server(self.config)

    async def start(self):
        print(f"Server started on {self.host}:{self.port}")
        await self.server.serve()

    async def close(self):
        self.server.should_exit = True

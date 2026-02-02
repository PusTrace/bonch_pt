from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db):
        super().__init__()
        self.db = db

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        data["db"] = self.db
        return await handler(event, data)

import logging

log = logging.getLogger("BONCH_BOT")

class ErrorLoggingMiddleware:
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except Exception:
            log.exception("Handler crashed")
            raise

def handle_async_exception(loop, context):
    """
    Ловит все uncaught exceptions в asyncio tasks.
    Отправляет их в логгер, а через TelegramHandler — в Telegram.
    """
    msg = context.get("message", "No message")
    exc = context.get("exception")

    if exc:
        log.exception(f"Unhandled async exception: {msg}", exc_info=exc)
    else:
        log.error(f"Unhandled async exception: {msg}")

import os
import sys
import logging
import requests
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv

class TelegramHandler(logging.Handler):
    MAX_MESSAGE_LENGTH = 4000

    def __init__(self, token: str, chat_ids: list[str], module_name: str, timeout=5):
        super().__init__(level=logging.ERROR)
        self.token = token
        self.chat_ids = chat_ids
        self.module_name = module_name
        self.timeout = timeout
        self.api_url = f"https://api.telegram.org/bot{token}/sendMessage"

    def emit(self, record: logging.LogRecord):
        try:
            # форматируем сообщение
            msg = self.format(record)
            if (
                record.name == "aiogram.dispatcher"
                and "Failed to fetch updates" in msg
                and "ServerDisconnectedError" in msg
            ):
                return  # просто игнорируем

            # добавляем traceback если есть
            if record.exc_info:
                tb_text = "".join(traceback.format_exception(*record.exc_info))
                msg = f"{msg}\n{tb_text}"

            # обрезаем до MAX_MESSAGE_LENGTH
            if len(msg) > self.MAX_MESSAGE_LENGTH:
                msg = msg[-self.MAX_MESSAGE_LENGTH:]  # последние 4000 символов
                msg = "…[truncated]…\n" + msg

            emoji = "🔥" if record.levelno >= logging.CRITICAL else "⚠️"

            # формируем текст без экранирования внутри ```
            text = f"{emoji} *{record.levelname}* | `{self.module_name}`\n\n```\n{msg}\n```"

            for chat_id in self.chat_ids:
                requests.post(
                    self.api_url,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "Markdown"
                    },
                    timeout=self.timeout
                )
        except Exception:
            # не падаем самим логгером
            pass




def setup_logging(module_name: str, log_file: str = None, level: int = logging.INFO,
                  file_level: int = None, console_level: int = None):
    file_level = file_level or level
    console_level = console_level or level
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    
    # console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # telegram
    token = os.getenv("TG_BOT_TOKEN")
    chat_ids_raw = os.getenv("TG_CHAT_IDS")
    if token and chat_ids_raw:
        chat_ids = [cid.strip() for cid in chat_ids_raw.split(",") if cid.strip()]
        telegram_handler = TelegramHandler(token, chat_ids, module_name)
        telegram_handler.setFormatter(formatter)
        root_logger.addHandler(telegram_handler)
        logging.info(f"Telegram notifications enabled for {module_name}: {chat_ids}")
    else:
        logging.warning("Telegram notifications disabled (missing credentials)")
    
    logging.info(f"Logging initialized for module: {module_name}")


def install_global_exception_handler(module_name: str, tail_lines: int = 10):
    """
    Все uncaught exceptions логируются и уходят в телеграм
    """
    def excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        log = logging.getLogger("UNCAUGHT")
        # берем только последние строки traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = "".join(tb_lines).strip().split("\n")[-tail_lines:]
        tb_text = "\n".join(tb_text)

        log.critical(
            f"Uncaught exception in {module_name}\n{tb_text}"
        )
        sys.exit(1)
    
    sys.excepthook = excepthook

import re

def escape_markdown(text: str) -> str:
    # экранируем ` _ * [ ] ( ) ~ > # + - = | { } . !
    return re.sub(r'([_*\[\]()~>#+\-=|{}.!])', r'\\\1', text)


if __name__ == "__main__":
    load_dotenv()
    MODULE_NAME = "LOGGER_TEST"
    setup_logging(module_name=MODULE_NAME, log_file="logs/test.log", level=logging.DEBUG)
    install_global_exception_handler(MODULE_NAME)

    log = logging.getLogger(MODULE_NAME)
    log.info("Info message (no telegram)")
    log.warning("Warning message (no telegram)")
    log.error("Error message (should go to telegram)")
    log.critical("Critical message (should go to telegram)")

    log.info("Raising exception to test global handler...")
    raise RuntimeError("Boom! Uncaught exception test")

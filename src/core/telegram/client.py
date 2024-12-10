from telethon import TelegramClient
from src.utils.logger import get_logger
from typing import Optional

logger = get_logger(__name__)

class TelegramClientManager:
    _instance: Optional[TelegramClient] = None

    @classmethod
    def get_client(cls, api_id: str, api_hash: str) -> TelegramClient:
        if cls._instance is None:
            cls._instance = TelegramClient('MAIN', api_id, api_hash)
        return cls._instance

    @classmethod
    def close(cls):
        if cls._instance:
            cls._instance.disconnect()
            cls._instance = None

def setup_telegram_client(api_id: str, api_hash: str) -> TelegramClient:
    """Initialize and return the Telegram client."""
    try:
        client = TelegramClientManager.get_client(api_id, api_hash)
        logger.info("Telegram client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Telegram client: {e}")
        raise
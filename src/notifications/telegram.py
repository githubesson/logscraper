import asyncio
from typing import Optional
from telegram.ext import ApplicationBuilder
from telegram.constants import ParseMode
from src.utils.logger import get_logger
from src.config.settings import Settings

logger = get_logger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.settings = Settings()
        self.application = ApplicationBuilder().token(self.settings.bot_token).build()
        self.chat_id = self.settings.telegram_chat_id

    async def send_notification(self, filename: str, amount_inserted: int, amount_in_file: int) -> bool:
        """Send notification to Telegram channel."""
        message = self._format_message(filename, amount_inserted, amount_in_file)
        
        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def _format_message(self, filename: str, amount_inserted: int, amount_in_file: int) -> str:
        """Format notification message."""
        return (
            "✨ New data inserted successfully! ✨\n\n"
            f"📂 Filename: {filename}\n"
            f"📊 Amount Inserted: {amount_inserted}\n"
            f"📈 Amount in File: {amount_in_file}"
        )
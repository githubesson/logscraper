from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    # Telegram settings
    api_id: str = os.getenv('API_ID')
    api_hash: str = os.getenv('API_HASH')
    bot_token: str = os.getenv('BOT_TOKEN')

    # MongoDB settings
    mongo_uri: str = os.getenv('MONGO_URI')
    database_name: str = os.getenv('DATABASE_NAME')
    collection_name: str = os.getenv('COLLECTION_NAME')

    # Worker settings
    max_concurrent_downloads: int = int(os.getenv('MAX_CONCURRENT_DOWNLOADS'))
    max_concurrent_processors: int = int(os.getenv('MAX_CONCURRENT_PROCESSORS'))

    # Webhook URLs
    discord_webhook_url: str = os.getenv('DISCORD_WEBHOOK_URL')
    telegram_chat_id: int = int(os.getenv('TELEGRAM_CHAT_ID'))

    def __post_init__(self):
        # Load channels from file
        import json
        with open('channels.json', 'r') as f:
            self.channels = json.load(f)
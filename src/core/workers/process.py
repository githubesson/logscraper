import asyncio
from typing import Optional
from src.utils.logger import get_logger
from src.core.processing.processor import FileProcessor
from src.data.mongodb.repository import MongoRepository
from src.notifications.discord import DiscordNotifier
from src.config.settings import Settings

logger = get_logger(__name__)

class ProcessWorker:
    def __init__(self, max_concurrent: int):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = asyncio.Queue()
        self.tasks = []
        
        # Get settings
        self.settings = Settings()
        
        # Initialize dependencies
        self.mongo_repo = MongoRepository(
            uri=self.settings.mongo_uri,
            database=self.settings.database_name,
            collection=self.settings.collection_name
        )
        
        self.discord_notifier = DiscordNotifier()
        
        # Initialize processor with dependencies
        self.processor = FileProcessor(
            mongo_repo=self.mongo_repo,
            discord_notifier=self.discord_notifier
        )

    async def add_to_queue(self, file_path: str, password: Optional[str], channel_info: dict):
        await self.queue.put((file_path, password, channel_info))

    async def run(self):
        while True:
            file_path, password, channel_info = await self.queue.get()
            try:
                async with self.semaphore:
                    await self.processor.process_file(
                        file_path=file_path,
                        channel_type=channel_info['type'],
                        password=password
                    )
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
            finally:
                self.queue.task_done()

    async def cleanup(self):
        """Cleanup resources when worker is done."""
        try:
            if hasattr(self, 'mongo_repo'):
                self.mongo_repo.close()
        except Exception as e:
            logger.error(f"Error during MongoDB cleanup: {e}")
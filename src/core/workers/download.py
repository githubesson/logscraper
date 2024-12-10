import asyncio
from typing import Optional, Tuple
from telethon import types, events
from src.utils.logger import get_logger
from src.core.workers.process import ProcessWorker

logger = get_logger(__name__)

class DownloadWorker:
    def __init__(self, max_concurrent: int, process_worker: ProcessWorker):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = asyncio.Queue()
        self.tasks = []
        self.process_worker = process_worker

    async def add_to_queue(self, item: Tuple):
        await self.queue.put(item)

    async def run(self):
        while True:
            queue_item = await self.queue.get()
            try:
                async with self.semaphore:
                    if isinstance(queue_item, tuple) and len(queue_item) == 4:
                        message, file_path, password, channel_info = queue_item
                        if isinstance(message, (events.NewMessage.Event, types.Message)):
                            if isinstance(message, events.NewMessage.Event):
                                message = message.message

                            if message.media:
                                downloaded_path = await message.client.download_media(
                                    message=message, 
                                    file=file_path
                                )
                                logger.info(f'New file downloaded to {downloaded_path}')
                                await self.notify_process_worker(downloaded_path, password, channel_info)
                            else:
                                logger.warning(f"Message does not contain media: {message.id}")
                        else:
                            logger.error(f"Unexpected message type in download queue: {type(message)}")
                    else:
                        logger.error(f"Unexpected item in download queue: {queue_item}")
            except Exception as e:
                logger.error(f"Error downloading file: {e}")
            finally:
                self.queue.task_done()

    async def notify_process_worker(self, file_path: str, password: Optional[str], channel_info: dict):
        try:
            await self.process_worker.add_to_queue(file_path, password, channel_info)
            logger.info(f"File {file_path} queued for processing")
        except Exception as e:
            logger.error(f"Error queuing file for processing: {e}")
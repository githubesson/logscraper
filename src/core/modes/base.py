from abc import ABC, abstractmethod
from src.utils.logger import get_logger
import asyncio

logger = get_logger(__name__)

class BaseMode(ABC):
    """Base class for all operation modes."""
    
    def __init__(self, client, download_worker, process_worker):
        self.client = client
        self.download_worker = download_worker
        self.process_worker = process_worker
        self.logger = logger

    @abstractmethod
    async def run(self):
        """Run the mode operation."""
        pass

    async def cleanup(self):
        """Clean up resources."""
        for worker in [self.download_worker, self.process_worker]:
            if hasattr(worker, 'tasks'):
                for task in worker.tasks:
                    task.cancel()
                await asyncio.gather(*worker.tasks, return_exceptions=True)
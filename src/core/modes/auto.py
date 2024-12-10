from src.core.modes.base import BaseMode
from src.core.telegram.handlers import setup_handlers
from src.config.settings import Settings

class AutoMode(BaseMode):
    """Automatic mode for monitoring configured channels."""

    async def run(self):
        try:
            settings = Settings()
            self.logger.info(
                f'Started {settings.max_concurrent_downloads} download workers and '
                f'{settings.max_concurrent_processors} process workers'
            )

            # Setup handlers for all configured channels
            setup_handlers(
                self.client,
                self.download_worker.queue,
                settings.channels
            )

            self.logger.info("Auto mode started. Monitoring channels...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            self.logger.error(f"Error in auto mode: {e}")
        finally:
            await self.cleanup()
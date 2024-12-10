import asyncio
from src.config.settings import Settings
from src.core.telegram.client import setup_telegram_client
from src.core.workers.download import DownloadWorker
from src.core.workers.process import ProcessWorker
from src.utils.logger import setup_logger
from src.core.modes.auto import AutoMode
from src.core.modes.manual import ManualMode
from src.core.modes.channel import ChannelMode

settings = Settings()
logger = setup_logger()

async def menu():
    """Main menu for the application."""

    # Initialize components
    client = setup_telegram_client(settings.api_id, settings.api_hash)
    
    # Initialize process worker first
    process_worker = ProcessWorker(settings.max_concurrent_processors)
    # Pass process worker to download worker
    download_worker = DownloadWorker(settings.max_concurrent_downloads, process_worker)

    # Start worker tasks
    download_worker.tasks = [asyncio.create_task(download_worker.run()) 
                           for _ in range(settings.max_concurrent_downloads)]
    process_worker.tasks = [asyncio.create_task(process_worker.run()) 
                          for _ in range(settings.max_concurrent_processors)]

    await client.start()

    # Initialize modes
    modes = {
        '1': AutoMode(client, download_worker, process_worker),
        '2': ManualMode(client, download_worker, process_worker),
        '3': ChannelMode(client, download_worker, process_worker)
    }

    while True:
        print("\nSelect a mode:")
        print("1. Auto Mode")
        print("2. Manual Mode")
        print("3. Channel Download Mode")
        print("4. Exit")

        choice = input("Enter your choice (1-4): ")

        if choice in modes:
            await modes[choice].run()
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

    # Cleanup
    for mode in modes.values():
        await mode.cleanup()
    await client.disconnect()

async def main():
    """Main entry point of the application."""
    try:
        await menu()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Application stopped")

if __name__ == "__main__":
    asyncio.run(main())
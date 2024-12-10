from src.core.modes.base import BaseMode
import os

class ChannelMode(BaseMode):
    """Channel mode for downloading all files from a specific channel."""

    async def run(self):
        try:
            channel_id = input("Enter the Telegram channel ID: ")
            try:
                channel_id = int(channel_id)
            except ValueError:
                self.logger.error("Invalid channel ID. Please enter a numeric ID.")
                return

            self.logger.info(f"Starting download for channel: {channel_id}")
            
            async for message in self.client.iter_messages(channel_id):
                if message.media:
                    await self._process_message(message)

            self.logger.info("All files have been queued for download.")
            
            # Wait for completion
            await self.download_worker.queue.join()
            await self.process_worker.queue.join()
            
            self.logger.info("All downloads and processing completed.")
            
        except Exception as e:
            self.logger.error(f"Error in channel download mode: {e}")
        finally:
            await self.cleanup()

    async def _process_message(self, message):
        """Process a single message from the channel."""
        chat_id = message.chat_id
        message_id = message.id
        message_link = f'tg://privatepost?channel={chat_id}&post={message_id}'

        # Get file extension and create filename
        extension = '.file'
        if message.document:
            original_filename = getattr(message.document, 'attributes', [{}])[0].file_name
            _, extension = os.path.splitext(original_filename)

        valid_filename = f'{message_id}{extension}'
        file_path = f'./{valid_filename}'
        file_size = message.file.size if message.file else 0

        self.logger.info(f'Queueing file: {valid_filename}')
        self.logger.info(f'Message link: {message_link}')
        self.logger.info(f'File size: {file_size / (1024 * 1024):.2f} MB')

        channel_info = {'type': 'archive'}
        await self.download_worker.add_to_queue(
            (message, file_path, None, channel_info)
        )
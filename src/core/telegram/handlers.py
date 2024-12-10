import re
import unicodedata
from telethon import events, types
from src.utils.logger import get_logger
from src.config.constants import SPECIAL_PASSWORDS
from typing import Dict, Any, Optional

logger = get_logger(__name__)

class MessageHandler:
    def __init__(self, download_queue):
        self.download_queue = download_queue

    async def handle_message(self, event: events.NewMessage.Event, channel_info: Dict[str, Any]):
        """Handle incoming message events."""
        if not event.message.media:
            return

        file_info = self._process_file_info(event)
        if not file_info:
            return

        password = self._extract_password(event, channel_info)
        await self._queue_download(event, file_info, password, channel_info)

    def _process_file_info(self, event: events.NewMessage.Event) -> Optional[Dict[str, Any]]:
        """Process and validate file information from the message."""
        try:
            chat_id = event.chat_id
            message_id = event.message.id

            if event.message.file:
                original_filename = event.message.file.name or f'message{message_id}'
                file_size = event.message.file.size
            else:
                original_filename = f'message{message_id}'
                file_size = 0

            valid_filename = self._sanitize_filename(original_filename, message_id)

            return {
                'chat_id': chat_id,
                'message_id': message_id,
                'filename': valid_filename,
                'file_size': file_size,
                'message_link': f'tg://privatepost?channel={chat_id}&post={message_id}'
            }
        except Exception as e:
            logger.error(f"Error processing file info: {e}")
            return None

    def _sanitize_filename(self, filename: str, message_id: int) -> str:
        """Sanitize filename for safe file system operations."""
        # Remove unsafe characters
        valid_filename = filename.replace('/', '').replace('\\', '_')
        valid_filename = unicodedata.normalize('NFKD', valid_filename)

        try:
            valid_filename.encode('utf-8')
        except UnicodeEncodeError:
            valid_filename = f'message{message_id}'

        if len(valid_filename) > 255:
            valid_filename = valid_filename[:250] + f'{message_id}'

        return valid_filename

    def _extract_password(self, event: events.NewMessage.Event, channel_info: Dict[str, Any]) -> Optional[str]:
        """Extract password from message text using regex pattern."""
        message_text = event.message.message.strip() if event.message.message else ""

        # Check for special passwords first
        for key, password in SPECIAL_PASSWORDS.items():
            if key in event.message.file.name:
                return password

        # Try regex pattern if provided in channel info
        if 'regex' in channel_info:
            regex_pattern = channel_info['regex']
            password_match = re.search(regex_pattern, message_text, re.DOTALL | re.IGNORECASE)
            if password_match:
                password = password_match.group(1).strip()
                return None if password == '?' else password

        return None

    async def _queue_download(self, event: events.NewMessage.Event, file_info: Dict[str, Any],
                              password: Optional[str], channel_info: Dict[str, Any]):
        """Queue file for download."""
        try:
            file_path = f"./{file_info['filename']}"

            # Log file information
            logger.info(f"Message link: {file_info['message_link']}")
            logger.info(f"Filename: {file_info['filename']}")
            logger.info(f"File size: {file_info['file_size'] / (1024 * 1024):.2f} MB")
            if password:
                logger.info(f"Password: {password}")
            else:
                logger.info("No password found")

            await self.download_queue.put((event, file_path, password, channel_info))

        except Exception as e:
            logger.error(f"Error queueing download: {e}")

def setup_handlers(client, download_queue, channels):
    """Setup message handlers for all channels."""
    handler = MessageHandler(download_queue)

    for channel in channels:
        @client.on(events.NewMessage(chats=channel['id']))
        async def message_handler(event, channel_info=channel):
            await handler.handle_message(event, channel_info)

    return handler
import asyncio
import os
import subprocess
from typing import List, Optional
from src.utils.logger import get_logger
from src.core.processing.extractor import ArchiveExtractor
from src.core.processing.parser import LineParser
from src.notifications.discord import DiscordNotifier
from src.data.mongodb.repository import MongoRepository
import telegram
from src.config.settings import Settings
from src.config.constants import SPECIAL_URLS, SPECIAL_LOGINS


logger = get_logger(__name__)

class FileProcessor:
    def __init__(self, mongo_repo: MongoRepository, discord_notifier: DiscordNotifier):
        self.mongo_repo = mongo_repo
        self.discord_notifier = discord_notifier
        self.extractor = ArchiveExtractor()
        self.parser = LineParser()
        self.batch_size = 1000
        self.bot = telegram.Bot(token=Settings.bot_token)  # Replace with your actual bot token

    async def _send_telegram_message(self, filename, amount_inserted, amount_in_file):
        message = (
            "✨ New data inserted successfully! ✨\n\n"
            f"📂 Filename: {filename}\n"
            f"📊 Amount Inserted: {amount_inserted}\n"
            f"📈 Amount in File: {amount_in_file}"
        )
        
        try:
            await self.bot.send_message(chat_id=Settings.telegram_chat_id, text=message)  # Replace with your actual chat ID
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def process_file(self, file_path: str, channel_type: str, password: Optional[str] = None):
        """Process a file based on its type."""
        try:
            if channel_type == 'archive':
                await self._process_archive(file_path, password)
            elif channel_type == 'combo':
                await self._process_combo(file_path)
            else:
                logger.error(f"Unknown channel type: {channel_type}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
        finally:
            self._cleanup(file_path)

    async def _process_archive(self, file_path: str, password: Optional[str]):
        """Process an archive file."""
        extract_path = os.path.splitext(file_path)[0]
        os.makedirs(extract_path, exist_ok=True)

        # Remove await here since extract_file returns a bool
        if self.extractor.extract_file(file_path, extract_path, password):
            errors = []  # Initialize empty errors list
            # Process the extracted files
            success = await self._process_extracted_files(extract_path, errors)

            if success:  # Check if processing was successful
                combined_path = os.path.join(extract_path, 'combined.txt')
                unique_path = os.path.join(extract_path, 'unique.txt')

                if os.path.exists(unique_path):
                    await self._ingest_processed_data(unique_path, "archive")
    async def _process_combo(self, file_path: str):
        """Process a combo file."""
        await self._ingest_processed_data(file_path, "combo")

    @staticmethod
    async def _process_extracted_files(extract_path: str, errors: List[str]) -> bool:
        """Process extracted files using ripgrep patterns."""
        try:
            try:
                cmd1 = r"""rg -oUNI "URL:\s(.*?)[|\r]\nUsername:\s(.*?)[|\r]\nPassword:\s(.*?)[|\r]\n" -r '$1:$2:$3' --glob-case-insensitive -g "Passwords.txt" | uniq >> combined.txt"""
                subprocess.run(cmd1, shell=True, cwd=extract_path, check=True)
                logger.info(f"Executed 1st rg command in {extract_path}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error executing 1st rg command: {e}")
                errors.append(f"1st rg command failed: {e}")

            try:
                cmd2 = r"""rg -oUNI "URL:\s(.*)\nUSER:\s(.*)\nPASS:\s(.*)" -r '$1:$2:$3' --multiline --glob-case-insensitive -g "All Passwords.txt" | tr -d '\r' | uniq >> combined.txt"""
                subprocess.run(cmd2, shell=True, cwd=extract_path, check=True)
                logger.info(f"Executed 2nd rg command in {extract_path}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error executing 2nd rg command: {e}")
                errors.append(f"2nd rg command failed: {e}")

            try:
                cmd3 = r"""rg -oUNI "url:\s*(.*?)\r?\nlogin:\s*(.*?)\r?\npassword:\s*(.*?)(\r?\n|$)" -r '$1:$2:$3' --multiline --glob-case-insensitive -g "passwords.txt" | tr -d '\r' | uniq >> combined.txt"""
                subprocess.run(cmd3, shell=True, cwd=extract_path, check=True)
                logger.info(f"Executed 3rd rg command in {extract_path}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error executing 3rd rg command: {e}")
                errors.append(f"3rd rg command failed: {e}")

            # Remove duplicates
            subprocess.run(
                'sort combined.txt | uniq > unique.txt',
                shell=True,
                cwd=extract_path,
                check=True,
                stdout=subprocess.DEVNULL
            )

            return len(errors) < 3

        except Exception as e:
            logger.error(f"Error processing extracted files: {e}")
            return False
        
    async def _validate_document(self, document):
        """Validate the document before insertion."""
        url = document['url']
        if any(special_url in url for special_url in SPECIAL_URLS) or any(special_login in document['email'] for special_login in SPECIAL_LOGINS):
            await self.discord_notifier.send_special_notification(
                special_url=url,
                url=document['url'],
                login=document['username'],
                password=document['password']
            )

    async def _ingest_processed_data(self, file_path: str, channel_type: str):
        """Ingest processed data into MongoDB using batch processing."""
        line_count = self.parser.count_valid_lines(file_path)
        logger.info(f"Number of valid lines in {file_path}: {line_count}")

        documents = []
        inserted_count = 0
        batch_count = 0

        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    try:
                        document = self.parser.parse_line(line, channel_type)
                        if document:
                            documents.append(document)
                            batch_count += 1

                            await self._validate_document(document)

                            # Insert batch when it reaches batch_size
                            if batch_count >= self.batch_size:
                                success_count = self.mongo_repo.insert_many(documents)
                                inserted_count += success_count
                                documents = []  # Clear the batch
                                batch_count = 0
                        else:
                            logger.warning(f"Skipping invalid line: {line}")
                    except Exception as e:
                        logger.error(f"Error processing line: {line}. Error: {e}")

            # Insert any remaining documents
            if documents:
                success_count = self.mongo_repo.insert_many(documents)
                inserted_count += success_count
   
        await self.discord_notifier.send_notification(filename=file_path, amount_inserted=inserted_count, amount_in_file=line_count)

        await self._send_telegram_message(file_path, inserted_count, line_count)



    def _cleanup(self, file_path: str):
        """Clean up temporary files and directories."""
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            if os.path.isdir(os.path.splitext(file_path)[0]):
                import shutil
                shutil.rmtree(os.path.splitext(file_path)[0])
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

           
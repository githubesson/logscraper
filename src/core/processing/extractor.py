import os
import errno
import shutil
import zipfile
import pyzipper
import py7zr
import subprocess
from typing import Optional, List
from src.utils.logger import get_logger
from src.config.constants import MIN_ARCHIVE_SIZE, FileExtensions
from src.utils.file import FileUtils

logger = get_logger(__name__)

class ArchiveExtractor:
    @staticmethod
    def extract_file(file_path: str, extract_path: str, password: Optional[str] = None) -> bool:
        """Extract an archive file based on its extension."""
        file_extension = os.path.splitext(file_path)[1].lower()
        errors: List[str] = []

        try:
            # Create extraction directory
            if not FileUtils.ensure_directory(extract_path):
                return False

            # Extract based on file type
            if file_extension == FileExtensions.ZIP.value:
                ArchiveExtractor._extract_zip(file_path, extract_path, password)
            elif file_extension == FileExtensions.RAR.value:
                ArchiveExtractor._extract_rar(file_path, extract_path, password)
            elif file_extension == FileExtensions.SEVEN_Z.value:
                ArchiveExtractor._extract_7z(file_path, extract_path, password)
            else:
                logger.error(f"Unsupported file format: {file_extension}")
                return False

            logger.info(f"Successfully extracted {file_path} to {extract_path}")

            # Process extracted files
            ArchiveExtractor._recursive_extract(extract_path, password)
            return ArchiveExtractor._process_extracted_files(extract_path, errors)

        except Exception as e:
            logger.error(f"Error extracting {file_path}: {str(e)}")
            return False

    @staticmethod
    def _extract_zip(file_path: str, extract_path: str, password: Optional[str] = None):
        """Extract ZIP files, handling both standard and encrypted archives."""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                if password:
                    zip_ref.setpassword(password.encode())
                ArchiveExtractor._extract_all(zip_ref, extract_path)
        except (RuntimeError, zipfile.BadZipFile, NotImplementedError):
            try:
                with pyzipper.AESZipFile(file_path, 'r') as zip_ref:
                    if password:
                        zip_ref.pwd = password.encode()
                    ArchiveExtractor._extract_all(zip_ref, extract_path)
            except Exception as e:
                logger.error(f"Failed to extract zip file: {e}")
                raise

    @staticmethod
    def _extract_rar(file_path: str, extract_path: str, password: Optional[str] = None):
        """Extract RAR files using unrar command-line tool."""
        try:
            cmd = ["unrar", "x", "-o+", file_path, extract_path]
            if password:
                cmd.insert(2, f"-p{password}")

            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Successfully extracted RAR file: {file_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting RAR file: {e.stderr.decode()}")
            raise

    @staticmethod
    def _extract_7z(file_path: str, extract_path: str, password: Optional[str] = None):
        """Extract 7z files using py7zr library."""
        try:
            with py7zr.SevenZipFile(file_path, mode='r', password=password) as z:
                z.extractall(path=extract_path)
            logger.info(f"Successfully extracted 7z file: {file_path}")
        except (py7zr.Bad7zFile, py7zr.PasswordRequired) as e:
            logger.error(f"Error extracting 7z file: {str(e)}")
            raise

    @staticmethod
    def _extract_all(zip_ref, extract_path: str):
        """Extract all files from a ZIP archive, handling path length issues."""
        for member in zip_ref.namelist():
            try:
                zip_ref.extract(member, extract_path)
            except OSError as e:
                if e.errno == errno.ENAMETOOLONG:
                    logger.warning(f"Skipping file due to path length: {member}")
                else:
                    raise

    @staticmethod
    def _recursive_extract(path: str, password: Optional[str] = None):
        """Recursively extract nested archives."""
        for root, _, files in os.walk(path):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    file_extension = os.path.splitext(file)[1].lower()

                    # Only process large archives
                    if (file_extension in [ext.value for ext in FileExtensions] and
                            os.path.getsize(file_path) > MIN_ARCHIVE_SIZE):

                        logger.info(f"Found nested archive: {file_path}")
                        new_extract_path = os.path.splitext(file_path)[0]

                        if not FileUtils.is_valid_path_length(new_extract_path):
                            logger.warning(f"Skipping file due to path length: {file_path}")
                            continue

                        FileUtils.ensure_directory(new_extract_path)
                        ArchiveExtractor.extract_file(file_path, new_extract_path, password)
                        FileUtils.safe_remove(file_path)
                        ArchiveExtractor._recursive_extract(new_extract_path, password)

                except OSError as e:
                    if e.errno == errno.ENAMETOOLONG:
                        logger.warning(f"Skipping file due to path length: {os.path.join(root, file)}")
                    else:
                        logger.error(f"Error processing file {os.path.join(root, file)}: {e}")

    @staticmethod
    def _process_extracted_files(extract_path: str, errors: List[str]) -> bool:
        """Process extracted files using ripgrep patterns."""
        try:
            # Execute ripgrep commands
            rg_commands = [
                r"""rg -oUNI "URL:\s(.*?)[|\r]\nUsername:\s(.*?)[|\r]\nPassword:\s(.*?)[|\r]\n" -r '$1:$2:$3' --glob-case-insensitive -g "Passwords.txt" | uniq >> combined.txt""",
                r"""rg -oUNI "URL:\s(.*)\nUSER:\s(.*)\nPASS:\s(.*)" -r '$1:$2:$3' --multiline --glob-case-insensitive -g "All Passwords.txt" | tr -d '\r' | uniq >> combined.txt""",
                r"""rg -oUNI "url:\s*(.*?)\r?\nlogin:\s*(.*?)\r?\npassword:\s*(.*?)(\r?\n|$)" -r '$1:$2:$3' --multiline --glob-case-insensitive -g "passwords.txt" | tr -d '\r' | uniq >> combined.txt"""
            ]

            for cmd in rg_commands:
                try:
                    subprocess.run(cmd, shell=True, cwd=extract_path, check=True)
                except subprocess.CalledProcessError as e:
                    errors.append(f"Command failed: {e}")

            # Remove duplicates
            subprocess.run(
                'sort combined.txt | uniq -u > unique.txt',
                shell=True,
                cwd=extract_path,
                check=True,
                stdout=subprocess.DEVNULL
            )

            return len(errors) < 100

        except Exception as e:
            logger.error(f"Error processing extracted files: {e}")
            return False
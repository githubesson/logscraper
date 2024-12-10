import os
import errno
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

class FileUtils:
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """Create directory if it doesn't exist."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except OSError as e:
            logger.error(f"Error creating directory {path}: {e}")
            return False

    @staticmethod
    def safe_remove(path: str) -> bool:
        """Safely remove a file or directory."""
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
            return True
        except OSError as e:
            logger.error(f"Error removing {path}: {e}")
            return False

    @staticmethod
    def get_file_size(path: str) -> Optional[int]:
        """Get file size in bytes."""
        try:
            return os.path.getsize(path)
        except OSError as e:
            logger.error(f"Error getting file size for {path}: {e}")
            return None

    @staticmethod
    def is_valid_path_length(path: str) -> bool:
        """Check if path length is valid for the operating system."""
        try:
            if os.name == 'nt':  # Windows
                return len(path) < 260
            return len(path) < 4096  # Unix-like systems
        except Exception as e:
            logger.error(f"Error checking path length: {e}")
            return False

    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize path for safe file operations."""
        try:
            # Replace potentially unsafe characters
            safe_path = path.replace('..', '_')
            safe_path = os.path.normpath(safe_path)
            return safe_path
        except Exception as e:
            logger.error(f"Error sanitizing path: {e}")
            return path
from datetime import datetime as dt
from typing import Dict, Optional
from src.config.constants import PROTOCOLS
from src.utils.logger import get_logger

logger = get_logger(__name__)

class LineParser:
    @staticmethod
    def parse_line(line: str, channel_type: str) -> Optional[Dict[str, str]]:
        """Parse a single line based on channel type."""
        try:
            parts = line.strip().split(':')

            if channel_type == 'combo':
                return LineParser._parse_combo_line(parts)
            elif channel_type == 'archive':
                return LineParser._parse_archive_line(parts)

            return None
        except Exception as e:
            logger.error(f"Error parsing line: {e}")
            return None

    @staticmethod
    def _parse_combo_line(parts: list) -> Optional[Dict[str, str]]:
        """Parse combo-type line."""
        if len(parts) == 2:
            return {
                "email": parts[0],
                "password": parts[1],
                "source_db": f"combo_logs_{dt.now().strftime('%d_%m_%Y')}"
            }
        elif len(parts) >= 3:
            return LineParser._parse_extended_line(parts, "combo")
        return None

    @staticmethod
    def _parse_archive_line(parts: list) -> Optional[Dict[str, str]]:
        """Parse archive-type line."""
        if len(parts) < 3:
            return None
        return LineParser._parse_extended_line(parts, "archive")

    @staticmethod
    def _parse_extended_line(parts: list, line_type: str) -> Dict[str, str]:
        """Parse line with URL, email, and password components."""
        if parts[0] in PROTOCOLS:
            url = f"{parts[0]}:{parts[1]}"
            email = parts[2]
            password = ':'.join(parts[3:])
        else:
            url = parts[0]
            email = parts[1]
            password = ':'.join(parts[2:])

        return {
            "email": email,
            "password": password,
            "url": url,
            "source_db": f"stealer_logs_{dt.now().strftime('%d_%m_%Y')}"
        }

    @staticmethod
    def count_valid_lines(file_path: str) -> int:
        """Count valid lines in a file."""
        try:
            with open(file_path, 'r') as file:
                return sum(1 for line in file)
        except Exception as e:
            logger.error(f"Error counting lines in {file_path}: {e}")
            return 0
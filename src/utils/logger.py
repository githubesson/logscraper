import logging
from typing import Optional

_logger: Optional[logging.Logger] = None

def setup_logger(log_file='app.log', log_level=logging.INFO) -> logging.Logger:
    """Configure and return a logger with both file and console handlers."""
    global _logger

    if _logger is not None:
        return _logger

    logger = logging.getLogger('telegram_processor')
    logger.setLevel(log_level)

    # Prevent duplicate handlers
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    _logger = logger
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Get the configured logger or create a new one if not exists."""
    global _logger

    if _logger is None:
        _logger = setup_logger()

    if name:
        return _logger.getChild(name)
    return _logger
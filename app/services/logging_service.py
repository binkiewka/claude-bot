import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

class LoggingService:
    def __init__(self, log_dir='logs'):
        """
        Initialize logging service
        
        :param log_dir: Directory to store log files
        """
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('ClaudeBot')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler with log rotation
        log_file = os.path.join(log_dir, f'claude_bot_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add formatter to handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message):
        """
        Log an info message
        
        :param message: Message to log
        """
        self.logger.info(message)

    def error(self, message, exc_info=None):
        """
        Log an error message
        
        :param message: Error message
        :param exc_info: Exception information
        """
        self.logger.error(message, exc_info=exc_info)

    def warning(self, message):
        """
        Log a warning message
        
        :param message: Warning message
        """
        self.logger.warning(message)

    def debug(self, message):
        """
        Log a debug message
        
        :param message: Debug message
        """
        self.logger.debug(message)

    def critical(self, message):
        """
        Log a critical message
        
        :param message: Critical message
        """
        self.logger.critical(message)

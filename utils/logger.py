import logging
import os
import sys

import config


class Logger:
    """Logger"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger(*args, **kwargs)
        return cls._instance
    
    def _init_logger(self, app_name: str = config.APP_NAME):
        """Initialize the logger"""
        self.app_name = app_name
        
        # Create logs directory
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(app_name)
        
        if not self.logger.handlers:
            # Set log level
            log_level = logging.DEBUG if config.DEBUG else logging.INFO
            self.logger.setLevel(log_level)
            
            # File handler
            log_file = os.path.join(log_dir, f"{app_name}.log")
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter(
                "%(levelname)s: %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def info(self, message: str, **fields):
        """Log info message"""
        self._log_with_fields("INFO", message, **fields)
    
    def debug(self, message: str, **fields):
        """Log debug message"""
        self._log_with_fields("DEBUG", message, **fields)
    
    def warning(self, message: str, **fields):
        """Log warning message"""
        self._log_with_fields("WARNING", message, **fields)
    
    def error(self, message: str, **fields):
        """Log error message"""
        self._log_with_fields("ERROR", message, **fields)
    
    def critical(self, message: str, **fields):
        """Log critical message"""
        self._log_with_fields("CRITICAL", message, **fields)
    
    def _log_with_fields(self, level: str, message: str, **fields):
        """Log message with additional fields"""
        if fields:
            field_str = " ".join([f"{k}={v}" for k, v in fields.items() if v is not None])
            full_message = f"{message} [{field_str}]" if field_str else message
        else:
            full_message = message
        
        log_method = getattr(self.logger, level.lower())
        log_method(full_message)

def get_logger() -> Logger:
    """Get logger instance"""
    return Logger()

# Export logger instance
logger = get_logger()
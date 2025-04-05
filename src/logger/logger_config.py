# logger_config.py
import logging
import sys
import os # Required for the SQLite handler
from logging.handlers import RotatingFileHandler
from logger.sqlite_handler import SQLiteHandler # Import the new handler!

class Logger:
    """
    Class to configure and use a standard Python logger.

    Allows logging messages to a file, console, and/or SQLite database.
    """
    def __init__(self,
                 logger_name='AppLogger',
                 level=logging.INFO,
                 log_to_console=True,
                 # File configuration
                 log_to_file=True,
                 log_file='app.log',
                 max_bytes=10*1024*1024, # 10 MB
                 backup_count=5,
                 # SQLite configuration
                 log_to_sqlite=False, # Disabled by default
                 sqlite_db_file='logs.db'):
        """
        Initializes and configures the logger with the specified handlers.
        """
        self.logger_name = logger_name
        self.level = level

        # Get the logger
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(self.level)

        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            # Create standard formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # --- File Handler (Rotating) ---
            if log_to_file:
                try:
                    # Ensure the log directory exists
                    log_dir = os.path.dirname(os.path.abspath(log_file))
                    if log_dir and not os.path.exists(log_dir):
                        os.makedirs(log_dir, exist_ok=True)

                    file_handler = RotatingFileHandler(
                        log_file,
                        maxBytes=max_bytes,
                        backupCount=backup_count,
                        encoding='utf-8'
                    )
                    file_handler.setLevel(self.level)
                    file_handler.setFormatter(formatter)
                    self.logger.addHandler(file_handler)
                except Exception as e:
                    print(f"Error configuring file logging for '{log_file}': {e}", file=sys.stderr)

            # --- Console Handler ---
            if log_to_console:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(self.level)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)

            # --- SQLite Handler ---
            if log_to_sqlite:
                try:
                    sqlite_handler = SQLiteHandler(db_file=sqlite_db_file)
                    sqlite_handler.setLevel(self.level)
                    # It doesn't need the same text formatter, but we assign it just in case
                    sqlite_handler.setFormatter(formatter)
                    self.logger.addHandler(sqlite_handler)
                    self.logger.info(f"Logging to SQLite DB '{sqlite_db_file}' activated.", extra={'event_type':'LOG_INIT'})
                except Exception as e:
                    # The specific error is already printed within SQLiteHandler
                    print(f"Could not activate SQLite logging: {e}", file=sys.stderr)


            # If no handler was configured
            if not self.logger.handlers:
                 self.logger.addHandler(logging.NullHandler())
                 print(f"Warning: Logger '{self.logger_name}' configured without active handlers.", file=sys.stderr)

    # --- Methods for logging messages ---
    # Modify methods to easily accept 'extra'

    def debug(self, message, extra=None):
        self.logger.debug(message, extra=extra)

    def info(self, message, extra=None):
        self.logger.info(message, extra=extra)

    def warning(self, message, extra=None):
        self.logger.warning(message, extra=extra)

    def error(self, message, exc_info=False, extra=None):
        self.logger.error(message, exc_info=exc_info, extra=extra)

    def critical(self, message, extra=None):
        self.logger.critical(message, extra=extra)

    def exception(self, message, extra=None):
        # Exception already includes exc_info=True by default
        self.logger.exception(message, extra=extra)


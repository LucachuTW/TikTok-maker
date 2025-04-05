import logging
import sys
import os
import getpass
from logging.handlers import RotatingFileHandler
from logger.sqlite_handler import SQLiteHandler
from utils.config_manager import ConfigManager

config = ConfigManager()

class Logger:
    """
    Class to configure and use a standard Python logger.
    Logs to file, console, and optionally SQLite.
    Paths are configurable via config.yaml.
    """
    def __init__(self,
                 logger_name='AppLogger',
                 level=logging.INFO,
                 log_to_console=True,
                 log_to_file=True,
                 max_bytes=10*1024*1024,
                 backup_count=5,
                 log_to_sqlite=False):

        self.logger_name = logger_name
        self.level = level

        # Load config values for paths
        log_config = config.config.get("logs", {})
        user = getpass.getuser()

        log_file = log_config.get("path", f"/home/{user}/logs/app.log").replace("[user]", user)
        sqlite_db_file = log_config.get("sqlite_file", f"/home/{user}/logs/logs.db").replace("[user]", user)

        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(self.level)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # --- File Handler ---
            if log_to_file:
                try:
                    log_dir = os.path.dirname(os.path.abspath(log_file))
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
                    sqlite_handler.setFormatter(formatter)
                    self.logger.addHandler(sqlite_handler)
                    self.logger.info(f"Logging to SQLite DB '{sqlite_db_file}' activated.", extra={'event_type': 'LOG_INIT'})
                except Exception as e:
                    print(f"Could not activate SQLite logging: {e}", file=sys.stderr)

            if not self.logger.handlers:
                self.logger.addHandler(logging.NullHandler())
                print(f"Warning: Logger '{self.logger_name}' configured without active handlers.", file=sys.stderr)

    # --- Wrapper methods ---
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
        self.logger.exception(message, extra=extra)

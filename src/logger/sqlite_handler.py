# sqlite_handler.py
import logging
import sqlite3
import os
import threading
import sys # To print errors if the DB fails

class SQLiteHandler(logging.Handler):
    """
    A logging handler that writes records to a SQLite database,
    saving only: id, timestamp, logger_name, message, event_type.
    """
    _conn_cache = {}
    _lock = threading.Lock()

    def __init__(self, db_file='logs.db'):
        super().__init__()
        self.db_file = db_file
        self._initialize_db()

    def _get_connection(self):
        """Gets a thread-safe SQLite connection for the current thread."""
        thread_id = threading.get_ident()
        if thread_id not in SQLiteHandler._conn_cache:
            db_dir = os.path.dirname(os.path.abspath(self.db_file))
            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except OSError as e:
                    print(f"Error creating directory for DB {db_dir}: {e}", file=sys.stderr)
                    raise

            SQLiteHandler._conn_cache[thread_id] = sqlite3.connect(
                self.db_file,
                timeout=5,
                check_same_thread=False # Necessary for thread safety with cache
            )
        return SQLiteHandler._conn_cache[thread_id]

    def _initialize_db(self):
        """Creates the simplified logs table if it does not exist."""
        with SQLiteHandler._lock: # Use lock for initialization as well
            temp_conn = None
            try:
                # Ensure directory exists before connecting
                db_dir = os.path.dirname(os.path.abspath(self.db_file))
                if db_dir and not os.path.exists(db_dir):
                   os.makedirs(db_dir, exist_ok=True)

                temp_conn = sqlite3.connect(self.db_file, timeout=5)
                cursor = temp_conn.cursor()
                # --- Simplified Schema ---
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        logger_name TEXT,
                        message TEXT,
                        event_type TEXT
                    )
                ''')
                # --- End Simplified Schema ---
                temp_conn.commit()
            except Exception as e:
                 print(f"Error initializing/creating simplified table in SQLite DB '{self.db_file}': {e}", file=sys.stderr)
                 # Optionally re-raise or handle more gracefully
            finally:
                if temp_conn:
                    temp_conn.close()

    def emit(self, record):
        """
        Writes a log record to the simplified database.
        Extracts 'event_type' from the record's 'extra' dictionary.
        """
        # Formatting is necessary to get the formatted timestamp
        self.format(record)

        # Extract the required information from the record
        timestamp = self.formatter.formatTime(record, self.formatter.datefmt) if self.formatter else record.asctime
        logger_name = record.name
        message = record.getMessage() # Use getMessage() for proper handling
        # Extract event_type from the 'extra' dictionary, with a default value
        event_type = getattr(record, 'event_type', 'GENERAL') # Use getattr for safety

        # Prepare SQL for simplified insertion
        sql = '''
            INSERT INTO logs (timestamp, logger_name, message, event_type)
            VALUES (?, ?, ?, ?)
        '''
        values = (
            timestamp,
            logger_name,
            message,
            event_type
        )

        # Insert into the database
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
        except Exception as e:
            # Print error to stderr and let the logging system handle the error
            print(f"Error writing simplified log to SQLite DB '{self.db_file}': {e}", file=sys.stderr)
            self.handleError(record) # Standard way to signal an error during emit

    def close(self):
        """Closes the SQLite connections upon finalization."""
        with SQLiteHandler._lock: # Ensure thread safety during close
             for conn in SQLiteHandler._conn_cache.values():
                 try:
                     conn.close()
                 except Exception as e:
                     print(f"Error closing SQLite connection: {e}", file=sys.stderr)
        SQLiteHandler._conn_cache.clear()
        super().close()
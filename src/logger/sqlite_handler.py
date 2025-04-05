# sqlite_handler.py
import logging
import sqlite3
import os
import threading
import sys # Para imprimir errores si falla la DB

class SQLiteHandler(logging.Handler):
    """
    Un manejador de logging que escribe los registros en una base de datos SQLite,
    guardando únicamente: id, timestamp, logger_name, message, event_type.
    """
    _conn_cache = {}
    _lock = threading.Lock()

    def __init__(self, db_file='logs.db'):
        super().__init__()
        self.db_file = db_file
        self._initialize_db()

    def _get_connection(self):
        """Obtiene una conexión SQLite segura para el hilo actual."""
        thread_id = threading.get_ident()
        if thread_id not in SQLiteHandler._conn_cache:
            db_dir = os.path.dirname(os.path.abspath(self.db_file))
            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except OSError as e:
                    print(f"Error creando directorio para DB {db_dir}: {e}", file=sys.stderr)
                    raise

            SQLiteHandler._conn_cache[thread_id] = sqlite3.connect(
                self.db_file,
                timeout=5,
                check_same_thread=False
            )
        return SQLiteHandler._conn_cache[thread_id]

    def _initialize_db(self):
        """Crea la tabla de logs simplificada si no existe."""
        with SQLiteHandler._lock:
            temp_conn = None
            try:
                db_dir = os.path.dirname(os.path.abspath(self.db_file))
                if db_dir and not os.path.exists(db_dir):
                   os.makedirs(db_dir, exist_ok=True)

                temp_conn = sqlite3.connect(self.db_file, timeout=5)
                cursor = temp_conn.cursor()
                # --- Esquema Simplificado ---
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        logger_name TEXT,
                        message TEXT,
                        event_type TEXT
                    )
                ''')
                # --- Fin Esquema Simplificado ---
                temp_conn.commit()
            except Exception as e:
                 print(f"Error al inicializar/crear tabla simplificada en DB SQLite '{self.db_file}': {e}", file=sys.stderr)
            finally:
                if temp_conn:
                    temp_conn.close()

    def emit(self, record):
        """
        Escribe un registro de log en la base de datos simplificada.
        Extrae 'event_type' del diccionario 'extra' del registro.
        """
        # Aplicar formato es necesario para obtener el timestamp formateado
        self.format(record)

        # Extraer la información requerida del registro
        timestamp = self.formatter.formatTime(record, self.formatter.datefmt) if self.formatter else record.asctime
        logger_name = record.name
        message = record.getMessage()
        # Extraer event_type del diccionario 'extra', con valor por defecto
        event_type = getattr(record, 'event_type', 'GENERAL')

        # Preparar SQL para inserción simplificada
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

        # Insertar en la base de datos
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
        except Exception as e:
            print(f"Error al escribir log simplificado en SQLite DB '{self.db_file}': {e}", file=sys.stderr)
            self.handleError(record)

    def close(self):
        """Cierra las conexiones SQLite al finalizar."""
        with SQLiteHandler._lock:
             for conn in SQLiteHandler._conn_cache.values():
                 conn.close()
        SQLiteHandler._conn_cache.clear()
        super().close()
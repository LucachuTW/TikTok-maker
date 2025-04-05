# logger_config.py
import logging
import sys
import os # Necesario para el handler de SQLite
from logging.handlers import RotatingFileHandler
from sqlite_handler import SQLiteHandler # ¡Importa el nuevo handler!

class Logger:
    """
    Clase para configurar y usar un logger estándar de Python.

    Permite registrar mensajes en archivo, consola y/o base de datos SQLite.
    """
    def __init__(self,
                 logger_name='AppLogger',
                 level=logging.INFO,
                 log_to_console=True,
                 # Configuración de archivo
                 log_to_file=True,
                 log_file='app.log',
                 max_bytes=10*1024*1024, # 10 MB
                 backup_count=5,
                 # Configuración de SQLite
                 log_to_sqlite=False, # Desactivado por defecto
                 sqlite_db_file='logs.db'):
        """
        Inicializa y configura el logger con los handlers especificados.
        """
        self.logger_name = logger_name
        self.level = level

        # Obtener el logger
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(self.level)

        # Evitar añadir handlers duplicados
        if not self.logger.handlers:
            # Crear formateador estándar
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # --- Handler para Archivo (Rotatorio) ---
            if log_to_file:
                try:
                    # Asegurar que el directorio del log existe
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
                    print(f"Error configurando el log de archivo '{log_file}': {e}", file=sys.stderr)

            # --- Handler para Consola ---
            if log_to_console:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(self.level)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)

            # --- Handler para SQLite ---
            if log_to_sqlite:
                try:
                    sqlite_handler = SQLiteHandler(db_file=sqlite_db_file)
                    sqlite_handler.setLevel(self.level)
                    # No necesita el mismo formateador de texto, pero lo asignamos por si acaso
                    sqlite_handler.setFormatter(formatter)
                    self.logger.addHandler(sqlite_handler)
                    self.logger.info(f"Logging a SQLite DB '{sqlite_db_file}' activado.", extra={'event_type':'LOG_INIT'})
                except Exception as e:
                    # El error específico ya se imprime dentro de SQLiteHandler
                    print(f"No se pudo activar el logging a SQLite: {e}", file=sys.stderr)


            # Si no se configuró ningún handler
            if not self.logger.handlers:
                 self.logger.addHandler(logging.NullHandler())
                 print(f"Advertencia: Logger '{self.logger_name}' configurado sin handlers activos.", file=sys.stderr)

    # --- Métodos para registrar mensajes ---
    # Modificamos los métodos para aceptar 'extra' fácilmente

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
        # Exception ya incluye exc_info=True por defecto
        self.logger.exception(message, extra=extra)
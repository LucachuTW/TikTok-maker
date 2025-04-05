import logging
import sys
from logging.handlers import RotatingFileHandler

class Logger:
    """
    Clase para configurar y usar un logger estándar de Python.

    Permite registrar mensajes en un archivo y/o en la consola
    con niveles y formatos configurables.
    """
    def __init__(self,
                 logger_name='AppLogger',
                 log_file='app.log',
                 level=logging.INFO,
                 log_to_console=True,
                 log_to_file=True,
                 max_bytes=10*1024*1024, # 10 MB
                 backup_count=5):
        """
        Inicializa y configura el logger.

        Args:
            logger_name (str): Nombre del logger. Útil si tienes múltiples loggers.
            log_file (str): Nombre del archivo donde se guardarán los logs.
            level (int): Nivel mínimo de log a registrar (e.g., logging.DEBUG, logging.INFO).
            log_to_console (bool): Si es True, los logs también se mostrarán en la consola.
            log_to_file (bool): Si es True, los logs se guardarán en el archivo especificado.
            max_bytes (int): Tamaño máximo del archivo de log antes de rotar.
            backup_count (int): Número de archivos de log de respaldo a mantener.
        """
        self.logger_name = logger_name
        self.log_file = log_file
        self.level = level
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # Obtener el logger (si ya existe con ese nombre, devuelve el mismo)
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(self.level)

        # Evitar añadir handlers duplicados si se instancia varias veces con el mismo nombre
        if not self.logger.handlers:
            # Crear formateador
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # Configurar handler para archivo (con rotación)
            if self.log_to_file:
                try:
                    file_handler = RotatingFileHandler(
                        self.log_file,
                        maxBytes=self.max_bytes,
                        backupCount=self.backup_count,
                        encoding='utf-8' # Asegurar codificación correcta
                    )
                    file_handler.setLevel(self.level)
                    file_handler.setFormatter(formatter)
                    self.logger.addHandler(file_handler)
                except Exception as e:
                    # Si falla la creación del archivo, al menos loguear en consola
                    print(f"Error configurando el log de archivo '{self.log_file}': {e}", file=sys.stderr)
                    self.log_to_file = False # Desactivar para evitar más errores
                    if not self.log_to_console: # Si no estaba activa, forzar consola
                       self.log_to_console = True


            # Configurar handler para consola
            if self.log_to_console:
                console_handler = logging.StreamHandler(sys.stdout) # Usar stdout por defecto
                console_handler.setLevel(self.level)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)

            # Si no se configuró ningún handler (ej: archivo falló y consola desactivada)
            if not self.logger.handlers:
                 self.logger.addHandler(logging.NullHandler()) # Evita mensaje "No handlers could be found"
                 print(f"Advertencia: Logger '{self.logger_name}' configurado sin handlers activos.", file=sys.stderr)


    # --- Métodos para registrar mensajes ---

    def debug(self, message):
        """Registra un mensaje con nivel DEBUG."""
        self.logger.debug(message)

    def info(self, message):
        """Registra un mensaje con nivel INFO."""
        self.logger.info(message)

    def warning(self, message):
        """Registra un mensaje con nivel WARNING."""
        self.logger.warning(message)

    def error(self, message, exc_info=False):
        """
        Registra un mensaje con nivel ERROR.

        Args:
            message (str): El mensaje de error.
            exc_info (bool): Si es True, añade información de la excepción actual al log.
                             Útil dentro de un bloque `except`.
        """
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message):
        """Registra un mensaje con nivel CRITICAL."""
        self.logger.critical(message)

    def exception(self, message):
        """
        Registra un mensaje con nivel ERROR incluyendo automáticamente
        la información de la excepción actual. Es como llamar a error()
        con exc_info=True. Ideal para bloques `except`.
        """
        self.logger.exception(message)

# --- Ejemplo de cómo obtener el logger (opcional, para testing aquí) ---
# if __name__ == "__main__":
#     # Crear una instancia del logger
#     mi_logger = Logger(logger_name='TestLogger', log_file='test.log', level=logging.DEBUG)
#
#     # Usar los métodos
#     mi_logger.debug("Este es un mensaje de debug.")
#     mi_logger.info("Información relevante aquí.")
#     mi_logger.warning("Una advertencia sobre algo.")
#     try:
#         x = 1 / 0
#     except ZeroDivisionError:
#         mi_logger.error("Ocurrió un error al dividir.", exc_info=True)
#         mi_logger.exception("Otra forma de loguear la excepción de división.")
#
#     mi_logger.critical("¡Error crítico! La aplicación podría fallar.")

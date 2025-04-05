"""Utils focused on detecting and connecting to the camera"""
import pyudev
import os
import subprocess
from utils.config_manager import ConfigManager
from logger.logger_config import Logger
import shutil
import time

config = ConfigManager()
logger = Logger(logger_name='CameraLogger')
class Camera:
    def __init__(self):
        self.vendor = None
        self.model = None
        self.device_node = None
        self.serial = None
        self._wait_for_camera()

    def _wait_for_camera(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by('block')

        known_models = config.config.get("cameras", [])

        logger.info(f"Waiting for USB camera. Known models: {known_models}")

        for device in iter(monitor.poll, None):
            if device.action == 'add' and device.get('ID_USB_DRIVER') == 'usb-storage':
                model = device.get('ID_MODEL', '')
                if model.lower() in [m.lower() for m in known_models]:
                    self.vendor = device.get('ID_VENDOR', 'Unknown')
                    self.model = model
                    self.device_node = device.device_node
                    self.serial = device.get('ID_SERIAL_SHORT') or device.get('ID_SERIAL', 'Unknown')

                    logger.info(f"Camera detected:")
                    logger.info(f"  Vendor: {self.vendor}")
                    logger.info(f"  Model: {self.model}")
                    logger.info(f"  Device node: {self.device_node}")
                    logger.info(f"  Serial: {self.serial}")
                    break

    def mount(self, mount_path=None):
        if mount_path is None:
            mount_path = os.path.expanduser("~/camera_mount")
        
        partition = self.device_node + "1"
        self.mount_point = mount_path

        os.makedirs(mount_path, exist_ok=True)

        try:
            subprocess.run(
                ["sudo", "mount", partition, mount_path],
                check=True
            )
            logger.info(f"Camera mounted at {mount_path}")
        except subprocess.CalledProcessError:
            logger.error(f"Failed to mount {partition} at {mount_path}")

    def unmount(self):
        if not hasattr(self, 'mount_point'):
            logger.warning("No mount point to unmount.")
            return

        try:
            # Intenta desmontar con la opción -l (lazy unmount)
            subprocess.run(
                ["sudo", "umount", "-l", self.mount_point],
                check=True
            )
            logger.info(f"Camera unmounted from {self.mount_point}")

            # Espera activa hasta que el sistema libere el punto de montaje
            timeout = 5  # segundos
            start = time.time()
            while time.time() - start < timeout:
                if not os.path.ismount(self.mount_point):
                    logger.info(f"Mount point {self.mount_point} is no longer a mount point.")
                    break
                time.sleep(0.5)

            # Verifica si el directorio aún existe y está accesible
            if os.path.exists(self.mount_point):
                try:
                    os.listdir(self.mount_point)  # Forzar acceso
                    shutil.rmtree(self.mount_point)
                    logger.info(f"Mount point {self.mount_point} removed")
                except Exception as e:
                    logger.error(f"Error removing mount point {self.mount_point}: {e}")
            else:
                logger.warning(f"Mount point {self.mount_point} no longer exists.")
        except subprocess.CalledProcessError:
            logger.error(f"Failed to unmount {self.mount_point}")
        except Exception as e:
            logger.error(f"Unexpected error during unmount: {e}")

    def download(self, base_path):
        """
        Download the content of the camera to the given path.
        If there are already files in the path, we can use rsync to only download the new files.
        """
        if not hasattr(self, 'mount_point'):
            logger.warning("Camera is not mounted.")
            return

        camara_path = os.path.join(self.mount_point, "DCIM")
        if not os.path.exists(camara_path):
            logger.warning(f"Camera path {camara_path} does not exist.")
            return
        video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.mts')
        gcsv_exts = ('.gcsv',)

        video_dest = os.path.join(base_path, "videos")
        gcsv_dest = os.path.join(base_path, "gcsv")

        os.makedirs(video_dest, exist_ok=True)
        os.makedirs(gcsv_dest, exist_ok=True)

        logger.info(f"Copying files from {camara_path} to:")
        logger.info(f"  - Videos: {video_dest}")
        logger.info(f"  - GCSV : {gcsv_dest}")

        for root, _, files in os.walk(camara_path):
            for file in files:
                src_file = os.path.join(root, file)
                lower_file = file.lower()

                if lower_file.endswith(video_exts):
                    dst_file = os.path.join(video_dest, file)
                elif lower_file.endswith(gcsv_exts):
                    dst_file = os.path.join(gcsv_dest, file)
                else:
                    continue  # ignore other files

                if not os.path.exists(dst_file):
                    try:
                        shutil.copy2(src_file, dst_file)
                        logger.info(f"  Copy: {file}")
                    except Exception as e:
                        logger.error(f"  Error copying {file}: {e}")
                else:
                    logger.info(f"  Already exists: {file}")

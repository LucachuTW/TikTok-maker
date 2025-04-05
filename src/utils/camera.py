"""Utils focused on detecting and connecting to the camera"""
import pyudev
import os
import subprocess
from utils.config_manager import ConfigManager
from logger.logger_manager import Logger
import shutil
import time

config = ConfigManager()
logger = Logger(logger_name='CameraLogger', log_to_file=True, log_to_sqlite=True)
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

        known_serials = config.config.get("cameras", [])

        logger.info(f"Waiting for USB camera. Known serials: {known_serials}")

        for device in iter(monitor.poll, None):
            if device.action == 'add' and device.get('ID_USB_DRIVER') == 'usb-storage':
                serial = device.get('ID_SERIAL_SHORT') or device.get('ID_SERIAL', '')
                if serial in known_serials:
                    self.vendor = device.get('ID_VENDOR', 'Unknown')
                    self.model = device.get('ID_MODEL', 'Unknown')
                    self.device_node = device.device_node
                    self.serial = serial

                    logger.info(f"Camera detected:")
                    logger.info(f"  Vendor: {self.vendor}")
                    logger.info(f"  Model: {self.model}")
                    logger.info(f"  Device node: {self.device_node}")
                    logger.info(f"  Serial: {self.serial}")
                    break


    def mount(self, mount_path=None):
        if mount_path is None:
            mount_path = os.path.expanduser("~/camera_mount")
        
        self.mount_point = mount_path
        os.makedirs(mount_path, exist_ok=True)

        # Encuentra particiones hijas de este dispositivo
        context = pyudev.Context()
        device = pyudev.Device.from_device_file(context, self.device_node)
        partitions = [
            dev.device_node
            for dev in device.children
            if dev.subsystem == 'block' and dev.device_type == 'partition'
        ]

        if not partitions:
            logger.error(f"No partitions found for device {self.device_node}")
            return

        for partition in partitions:
            try:
                subprocess.run(
                    ["sudo", "mount", partition, mount_path],
                    check=True
                )
                logger.info(f"Camera mounted at {mount_path} using partition {partition}")
                return  # exit after first successful mount
            except subprocess.CalledProcessError:
                logger.warning(f"Failed to mount {partition}, trying next...")

        logger.error(f"All mount attempts failed for {self.device_node}")

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
        Each video (and its associated .gcsv) is saved in its own subfolder.
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

        logger.info(f"Copying files from {camara_path} to individual folders under {base_path}")

        files_by_base = {}

        # First pass: group files by base name (without extension)
        for root, _, files in os.walk(camara_path):
            for file in files:
                name, ext = os.path.splitext(file)
                ext = ext.lower()
                if ext in video_exts or ext in gcsv_exts:
                    files_by_base.setdefault(name, []).append(os.path.join(root, file))

        # Now for each base, create a subfolder and copy files in
        for base_name, file_paths in files_by_base.items():
            dest_dir = os.path.join(base_path, base_name)
            os.makedirs(dest_dir, exist_ok=True)

            for src in file_paths:
                filename = os.path.basename(src)
                dst_file = os.path.join(dest_dir, filename)

                if not os.path.exists(dst_file):
                    try:
                        shutil.copy2(src, dst_file)
                        logger.info(f"  Copied {filename} to {dest_dir}")
                    except Exception as e:
                        logger.error(f"  Error copying {filename} to {dest_dir}: {e}")
                else:
                    logger.info(f"  Skipped (already exists): {filename} in {dest_dir}")

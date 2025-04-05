"""Utils focused on detecting and connecting to the camera"""
import pyudev
import os
import subprocess
from utils.config_manager import ConfigManager
import shutil

config = ConfigManager()

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

        print(f"Waiting for USB camera. Known models: {known_models}")

        for device in iter(monitor.poll, None):
            if device.action == 'add' and device.get('ID_USB_DRIVER') == 'usb-storage':
                model = device.get('ID_MODEL', '')
                if model.lower() in [m.lower() for m in known_models]:
                    self.vendor = device.get('ID_VENDOR', 'Unknown')
                    self.model = model
                    self.device_node = device.device_node
                    self.serial = device.get('ID_SERIAL_SHORT') or device.get('ID_SERIAL', 'Unknown')

                    print(f"Camera detected:")
                    print(f"  Vendor: {self.vendor}")
                    print(f"  Model: {self.model}")
                    print(f"  Device node: {self.device_node}")
                    print(f"  Serial: {self.serial}")
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
            print(f"Camera mounted at {mount_path}")
        except subprocess.CalledProcessError:
            print(f"Failed to mount {partition} at {mount_path}")

    def unmount(self):
        if hasattr(self, 'mount_point'):
            try:
                subprocess.run(
                    ["umount", self.mount_point],
                    check=True
                )
                print(f"Camera unmounted from {self.mount_point}")
                # Clean up the mount point
                os.rmdir(self.mount_point)
            except subprocess.CalledProcessError:
                print(f"Failed to unmount {self.mount_point}")
        else:
            print("No mount point to unmount.")

    def download(self, base_path):
        """
        Download the content of the camera to the given path.
        If there are already files in the path, we can use rsync to only download the new files.
        """
        if not hasattr(self, 'mount_point'):
            print("Camera is not mounted.")
            return

        camara_path = os.path.join(self.mount_point, "DCIM")
        if not os.path.exists(camara_path):
            print(f"Camera path {camara_path} does not exist.")
            return
        video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.mts')
        gcsv_exts = ('.gcsv',)

        video_dest = os.path.join(base_path, "videos")
        gcsv_dest = os.path.join(base_path, "gcsv")

        os.makedirs(video_dest, exist_ok=True)
        os.makedirs(gcsv_dest, exist_ok=True)

        print(f"Copying files from {camara_path} to:")
        print(f"  - Videos: {video_dest}")
        print(f"  - GCSV : {gcsv_dest}")

        for root, _, files in os.walk(camara_path):
            for file in files:
                src_file = os.path.join(root, file)
                lower_file = file.lower()

                if lower_file.endswith(video_exts):
                    dst_file = os.path.join(video_dest, file)
                elif lower_file.endswith(gcsv_exts):
                    dst_file = os.path.join(gcsv_dest, file)
                else:
                    continue  # ignorar otros archivos

                if not os.path.exists(dst_file):
                    shutil.copy2(src_file, dst_file)
                    print(f"  Copy: {file}")
                else:
                    print(f"  Already exists: {file}")
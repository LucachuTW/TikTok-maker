"""Utils focused on detecting and connecting to the camera"""
import pyudev
from utils.config_manager import ConfigManager

config = ConfigManager()

class Camera:
    def __init__(self):
        self.vendor = None
        self.model = None
        self.device_node = None
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
                    print(f"Camera detected: {self.vendor} {self.model}")
                    break

"""Executable module for connecting"""
from utils.config_manager import ConfigManager
from utils.camera import Camera

config = ConfigManager()

if __name__ == "__main__":
    while True:
        camera = Camera()
        camera.mount()
        print(camera.model)
        camera.download(config.config.get("camera_path", None))
        camera.unmount()
        print("Unmounted")

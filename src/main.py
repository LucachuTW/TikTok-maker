"""Executable module for connecting"""
from utils.config_manager import ConfigManager
from utils.camera import Camera

config = ConfigManager()

if __name__ == "__main__":
    while True:
        camera = Camera()
        camera.mount()
        print(camera.model)
        camera.download(config.config.get("path", None)[0])
        camera.unmount()
        print("Unmounted")

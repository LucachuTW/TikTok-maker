"""Executable module for connecting"""
from utils.config_manager import ConfigManager
from utils.camera import Camera

config = ConfigManager()
camera = Camera()
camera.mount()
print(camera.model)
print(config.config)

if __name__ == "__main__":
    pass

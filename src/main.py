"""Executable module for connecting"""
from utils.camera import detect_cam
from utils.config_manager import ConfigManager

config = ConfigManager()

print(config.config)

if __name__ == "__main__":
    pass

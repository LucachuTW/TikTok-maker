import os
import yaml

class ConfigManager:
    def __init__(self, path="config/config.yaml"):
        self.path = path
        self.config = None
        self.load_config()

    def load_config(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        absolute_path = os.path.join(base_dir, self.path)
        with open(absolute_path, 'r') as file:
            self.config = yaml.safe_load(file)

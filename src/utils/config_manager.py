import os
import yaml
import getpass

class ConfigManager:
    def __init__(self, path="config/config.yaml"):
        self.path = path
        self.config = None
        self._ensure_config_exists()
        self._load_config()
        self._fix_placeholders()

    def _ensure_config_exists(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        absolute_path = os.path.join(base_dir, self.path)

        config_dir = os.path.dirname(absolute_path)
        os.makedirs(config_dir, exist_ok=True)

        if not os.path.isfile(absolute_path):
            default_config = {
                "camera_path": "/home/[user]/camera_mount",
                "logs": {
                    "path": "/home/[user]/logs/app.log",
                    "sqlite_file": "/home/[user]/logs/logs.db"
                },
                "cameras": ["Wasintek_camera"]
            }
            with open(absolute_path, 'w') as file:
                yaml.dump(default_config, file, default_flow_style=False)

    def _load_config(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        absolute_path = os.path.join(base_dir, self.path)
        with open(absolute_path, 'r') as file:
            self.config = yaml.safe_load(file)

    def _fix_placeholders(self):
        user = getpass.getuser()

        def replace_placeholders(value):
            if isinstance(value, str):
                return value.replace("[user]", user)
            elif isinstance(value, list):
                return [replace_placeholders(v) for v in value]
            elif isinstance(value, dict):
                return {k: replace_placeholders(v) for k, v in value.items()}
            return value

        self.config = replace_placeholders(self.config)

import os
import yaml
import getpass

class ConfigManager:
    def __init__(self, path="config/config.yaml"):
        self.path = path
        self.config = None
        self._ensure_config_exists()
        self._load_config()
        self._fix_paths()

    def _ensure_config_exists(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        absolute_path = os.path.join(base_dir, self.path)

        config_dir = os.path.dirname(absolute_path)
        os.makedirs(config_dir, exist_ok=True)

        if not os.path.isfile(absolute_path):
            default_config = {
                "path": ["/home/[user]/camera_mount"],
                "cameras": ["Wasintek_camera"]
            }
            with open(absolute_path, 'w') as file:
                yaml.dump(default_config, file)

    def _load_config(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        absolute_path = os.path.join(base_dir, self.path)
        with open(absolute_path, 'r') as file:
            self.config = yaml.safe_load(file)

    def _fix_paths(self):
        original_path = self.config.get('path', [None])[0]
        if not original_path:
            return

        if "[user]" in original_path:
            user = getpass.getuser()
            replaced_path = original_path.replace("[user]", user)
            self.config["path"][0] = replaced_path

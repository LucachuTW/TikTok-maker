import getpass
from pathlib import Path
from utils.config_manager import ConfigManager

config = ConfigManager()

def extract_path_current_file():
    """
    Extract the path of the dir of the current file.
    """
    # Get the absolute path of the current file
    current_file_path = Path(__file__).resolve()
    
    # Get the parent directory of the current file
    parent_directory = current_file_path.parent
    
    return parent_directory

def extract_path():
    path = config.config.get('path', None)[0]
    if "[user]" in path:
        user = getpass.getuser()
        path = path.replace("[user]", user)

    return path
    


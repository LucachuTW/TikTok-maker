import subprocess
from pathlib import Path
from utils.config_manager import ConfigManager

config = ConfigManager()

def run_gyroflow(video_path: str):
    video_path = Path(video_path)
    video_name = video_path.stem

    camera_path = Path(config.config["camera_path"])
    
    gyroflow_executable = Path(__file__).parent / "gyroflow"
    settings_path = Path(__file__).parent / "settings2.gyroflow"
    gyro_data_path = camera_path / f"{video_name}_synchronized.gcsv"

    command = [
        str(gyroflow_executable),
        str(video_path),
        str(settings_path),
        "-g",
        str(gyro_data_path)
    ]
    print(command)

    try:
        subprocess.run(command, check=True)
        print(f"✅ Estabilizado: {video_path.name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al estabilizar {video_path.name}: {e}")

import subprocess
from pathlib import Path
from utils.config_manager import ConfigManager

config = ConfigManager()

def run_gyroflow(video_path: str):
    video_path = Path(video_path)
    video_name = video_path.stem
    video_dir = video_path.parent  # ✅ Carpeta donde está el vídeo

    gyroflow_executable = Path(__file__).parent / "gyroflow"
    settings_path = Path(__file__).parent / "settings.gyroflow"
    gyro_data_path = video_dir / f"{video_name}_synchronized.gcsv"  # ✅ en la misma carpeta del vídeo

    command = [
        str(gyroflow_executable),
        str(video_path),
        str(settings_path),
        "-g",
        str(gyro_data_path)
    ]
    print("Running:", " ".join(command))

    try:
        subprocess.run(command, check=True)
        print(f"✅ Estabilizado: {video_path.name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al estabilizar {video_path.name}: {e}")

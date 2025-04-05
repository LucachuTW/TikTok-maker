"""Executable module for connecting all modules"""
from utils.config_manager import ConfigManager
from utils.camera import Camera
from utils.extract_audio_wav import extract_audio_ffmpeg
import os

config = ConfigManager()

def list_videos(base_path):
    """Recursively find all video files inside subfolders."""
    found = []
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.lower().endswith(('.mp4', '.mov', '.avi')):
                found.append(os.path.join(root, f))
    return found

def choose_files(files, prompt="Select files (comma-separated indices):"):
    if not files:
        print("No files found.")
        return []

    for i, f in enumerate(files):
        print(f"{i}: {f}")
    
    selected = input(prompt + " ")
    indices = [int(i.strip()) for i in selected.split(",") if i.strip().isdigit()]
    return [files[i] for i in indices if 0 <= i < len(files)]

def stabilish(files):
    print("⚙️ Stabilizing the following files:")
    for f in files:
        print(f" - {f}")
        # TODO: Implement stabilization logic
    return []  # Replace with list of stabilized video paths if applicable

def extract_audio(files):
    print("🔉 Extracting audio from the following files:")
    for full_path in files:
        print(f" - {full_path}")

        video_name = os.path.splitext(os.path.basename(full_path))[0]
        video_dir = os.path.dirname(full_path)

        audio_dir = os.path.join(video_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        output_path = os.path.join(audio_dir, f"{video_name}.wav")
        extract_audio_ffmpeg(full_path, output_path)


def clip(files):
    print("✂️ Clipping the following files:")
    for full_path in files:
        print(f" - {full_path}")

        video_name = os.path.splitext(os.path.basename(full_path))[0]
        video_dir = os.path.dirname(full_path)

        clips_dir = os.path.join(video_dir, "clips")
        os.makedirs(clips_dir, exist_ok=True)

        print(f"  → Would save clips into: {clips_dir}")


if __name__ == "__main__":
    while True:
        camera = Camera()
        camera.mount()
        print(camera.model)
        camera.download(config.config.get("camera_path", None))
        camera.unmount()
        print("📤 Camera unmounted.")

        base_path = config.config.get("camera_path", "")
        downloaded_videos = list_videos(base_path)

        # 1. Extraer audio automáticamente
        print("\n🔉 Automatically extracting audio from downloaded videos...")
        extract_audio(downloaded_videos)

        # 2. Estabilización
        print("\n🎥 Available videos:")
        videos_to_stabilize = choose_files(downloaded_videos, "Select videos to stabilize:")
        stabilized_videos = stabilish(videos_to_stabilize)

        # 3. Clipping
        all_videos_after_stab = list_videos(base_path)
        print("\n📼 Videos available for clipping:")
        videos_to_clip = choose_files(all_videos_after_stab, "Select videos to clip:")
        clip(videos_to_clip)

        print("\n🔁 Restarting loop...\n")

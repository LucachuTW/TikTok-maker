"""Executable module for connecting all modules"""
from utils.config_manager import ConfigManager
from utils.camera import Camera
from utils.extract_audio_wav import extract_audio_ffmpeg
import os

config = ConfigManager()

def list_videos(path):
    return [f for f in os.listdir(path) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

def choose_files(files, prompt="Select files (comma-separated indices):"):
    if not files:
        print("No files found.")
        return []

    for i, f in enumerate(files):
        print(f"{i}: {f}")
    
    selected = input(prompt + " ")
    indices = [int(i.strip()) for i in selected.split(",") if i.strip().isdigit()]
    return [files[i] for i in indices if 0 <= i < len(files)]

def stabilish(files, input_dir):
    print("⚙️ Stabilizing the following files:")
    for f in files:
        pass

def clip(files, input_dir):
    print("✂️ Clipping the following files:")
    for f in files:
        pass


def extract_audio(files, input_dir):
    print("🔉 Extracting audio from the following files:")
    for f in files:
        full_path = os.path.join(input_dir, f)

        parent_dir = os.path.dirname(full_path)
        grandparent_dir = os.path.dirname(parent_dir)

        audio_dir = os.path.join(grandparent_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        # Ruta de salida
        output_path = os.path.join(audio_dir, os.path.splitext(f)[0] + ".wav")

        extract_audio_ffmpeg(full_path, output_path)

if __name__ == "__main__":
    while True:
        camera = Camera()
        camera.mount()
        print(camera.model)
        camera.download(config.config.get("camera_path", None))
        camera.unmount()
        print("📤 Camera unmounted.")

        video_dir = os.path.join(config.config.get("camera_path", ""), "videos")
        all_videos = list_videos(video_dir)

        print("\n🎥 Available videos:")
        videos_to_stabilize = choose_files(all_videos, "Select videos to stabilize:")

        # 2. Stabilize selected videos
        stabilized_videos = stabilish(videos_to_stabilize, video_dir)

        # 3. List videos again for clipping
        all_videos_after_stab = list_videos(video_dir)

        print("\n📼 Videos available for clipping:")
        videos_to_clip = choose_files(all_videos_after_stab, "Select videos to clip:")

        # 4. Clip selected
        clip(videos_to_clip, video_dir)

        # 5. List videos again for audio extraction
        all_videos_after_clip = list_videos(video_dir)

        print("\n🔊 Videos available for audio extraction:")
        videos_for_audio = choose_files(all_videos_after_clip, "Select videos to extract audio from:")

        # 6. Extract audio
        extract_audio(videos_for_audio, video_dir)


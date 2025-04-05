from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, ImageClip
from utils.manage_csv import CSVManager
from utils.config_manager import ConfigManager
import os
import subprocess
from gyroflow.interpolate_gcsv import interpolate_data_for_frames_from_video_path


def get_interval_clip(peak_times, clip_duration=(0.5, 1.5)):
    clips_duration = []
    for peak_time in peak_times:
        start_time = max(peak_time - clip_duration[0], 0)
        end_time = peak_time + clip_duration[1]
        clips_duration.append((start_time, end_time))

    clips_duration.sort(key=lambda x: x[0])

    merged_clips = []
    for clip in clips_duration:
        if not merged_clips:
            merged_clips.append(clip)
        else:
            last_start, last_end = merged_clips[-1]
            current_start, current_end = clip

            if current_start <= last_end:
                merged_clips[-1] = (last_start, max(last_end, current_end))
            else:
                merged_clips.append(clip)

    return merged_clips

def overlay_data_on_video(video_path, frame_data):
    video = VideoFileClip(video_path)
    fps = video.fps

    def make_frame_with_overlay(get_frame, t):
        frame = get_frame(t)
        frame_idx = int(t * fps)
        if frame_idx >= len(frame_data):
            return frame

        data = frame_data[frame_idx]
        text = (
            f"Time: {data['timestamp_sec']:.2f}s\n"
            f"Gyro: [{data['gyro_x']:.2f}, {data['gyro_y']:.2f}, {data['gyro_z']:.2f}]\n"
            f"Accel: [{data['accel_x']:.2f}, {data['accel_y']:.2f}, {data['accel_z']:.2f}]"
        )

        txt_clip = TextClip(
            text,
            fontsize=20,
            color='white',
            font='DejaVu-Sans',
            bg_color='black'
        ).set_position(("left", "bottom")).set_duration(1.0 / fps)

        composite = CompositeVideoClip([ImageClip(frame).set_duration(1.0 / fps), txt_clip])
        return composite.get_frame(0)

    print("Rendering video with overlay...")

    base, ext = os.path.splitext(video_path)
    temp_output_path = f"{base}_with_overlay{ext}"

    new_video = video.fl(make_frame_with_overlay)
    new_video.write_videofile(temp_output_path, codec="libx264", audio_codec="aac")

    print("Replacing original video...")
    os.remove(video_path)
    os.rename(temp_output_path, video_path)

    return video_path


def create_highlight_clips(video_path, clips_duration, output_folder, join=False):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    clip_paths = []

    video = VideoFileClip(video_path)
    total_duration = video.duration
    clips = []

    for i, (start, end) in enumerate(clips_duration):
        start = max(start, 0)
        end = min(end, total_duration)
        if end - start <= 0.1:
            print(f"Clip {i+1} skipped: duration too short ({end - start}s)")
            continue

        try:
            subclip = video.subclip(start, end)
            has_audio = subclip.audio is not None

            clip_file = os.path.join(output_folder, f"{base_name}_clip_{i+1}.mp4")
            print(f"Exporting clip {i+1}: {start:.2f}s to {end:.2f}s | Audio: {has_audio}")
            
            subclip.write_videofile(
                clip_file,
                codec="libx264",
                audio_codec="aac" if has_audio else None,
                audio=has_audio,
                verbose=False,
                logger=None
            )
            
            clip_paths.append(clip_file)
            clips.append(subclip)
        except Exception as e:
            print(f"Error creating clip {i+1}: {e}")

    if join and clips:
        try:
            final = concatenate_videoclips(clips)
            joined_path = os.path.join(output_folder, f"{base_name}_highlights.mp4")
            print("Concatenating all clips into one...")
            final.write_videofile(joined_path, codec="libx264", audio=True)
            return [joined_path]
        except Exception as e:
            print(f"Error concatenating clips: {e}")

    return clip_paths

def clip(files):
    print("✂️ Clipping the following files:")
    for full_path in files:
        print(f" - {full_path}")

        video_dir = os.path.dirname(full_path)
        video_name = os.path.basename(full_path)

        # Buscar el archivo .gcsv con el mismo nombre base
        base_name = os.path.splitext(video_name)[0]
        gcsv_path = os.path.join(video_dir, f"{base_name}.gcsv")

        """
        # add overlay info:
        frame_data = interpolate_data_for_frames_from_video_path(full_path, gcsv_path)
        overlay_data_on_video(full_path, frame_data)
        """

        if not os.path.exists(gcsv_path):
            print(f"  ⚠️  GCSV file not found: {gcsv_path}, skipping.")
            continue

        try:
            csv_manager = CSVManager(gcsv_path)
            peaks = csv_manager.detect_peaks(kind='acceleration', top_n=5, plot=False)
            peak_times = [p[0] for p in peaks]

            if not peak_times:
                print(f"  ⚠️  No peaks found in {gcsv_path}, skipping.")
                continue

            clips_duration = get_interval_clip(peak_times, clip_duration=(0.5, 1.5))
            clips_dir = os.path.join(video_dir, "clips")

            print(f"  ✨ Creating highlight clips for {base_name}...")
            create_highlight_clips(full_path, clips_duration, clips_dir, join=True)

        except Exception as e:
            print(f"  ❌ Error while clipping {full_path}: {e}")

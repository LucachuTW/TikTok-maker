from moviepy.editor import VideoFileClip, concatenate_videoclips
from manage_csv import CSVManager
from config_manager import ConfigManager
import os
import subprocess

def compress_video(input_path, output_path, crf=28, scale_width=640):
    """
    Compress the video using ffmpeg.
    :param input_path: Path to original video.
    :param output_path: Path to save compressed video.
    :param crf: Constant Rate Factor (lower = better quality, default 28).
    :param scale_width: Resize width (height is auto).
    """
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-vf", f"scale={scale_width}:-2",  # Resize width, preserve aspect ratio
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(crf),
        "-an",  # remove audio to save more resources
        output_path,
        "-y"  # overwrite
    ]
    print("Compressing video with ffmpeg...")
    print("Running command:", ' '.join(cmd))

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def get_interval_clip(peak_times, clip_duration=(0.5, 1.5)):
    """
    Get the start and end time for the clip based on peak time.
    :param peak_time: List of times of the peak moments.
    :param clip_duration: Tuple of (start_offset, end_offset).
    :return: List of tuples of (start_time, end_time).
    """
    clips_duration = []
    for peak_time in peak_times:
        start_time = max(peak_time - clip_duration[0], 0)
        end_time = peak_time + clip_duration[1]
        clips_duration.append((start_time, end_time))

    #Clips with share time, we join it:
    # Sort the intervals by start time
    clips_duration.sort(key=lambda x: x[0])

    # Merge overlapping intervals
    merged_clips = []
    for clip in clips_duration:
        if not merged_clips:
            merged_clips.append(clip)
        else:
            last_start, last_end = merged_clips[-1]
            current_start, current_end = clip

            # If intervals overlap or touch, merge them
            if current_start <= last_end:
                merged_clips[-1] = (last_start, max(last_end, current_end))
            else:
                merged_clips.append(clip)

    # `merged_clips` now contains clean, non-overlapping intervals

    return merged_clips

def create_highlight_clips(video_path, clips_duration, output_folder, join=False):
    """
    Create video highlight clips from specified time intervals.

    :param video_path: Path to the video file.
    :param clips_duration: List of (start_time, end_time) tuples.
    :param output_folder: Folder to save the generated clips.
    :param join: If True, concatenate all clips into one final video.
    :return: List of paths to generated clips or final joined video.
    """
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
if __name__ == "__main__":
    config = ConfigManager()
    path = config.config.get("camera_path", None)
    path_csv = os.path.join(path, "gcsv", "Runcam6_0002.gcsv")
    csv_manager = CSVManager(path_csv)
    video_path = os.path.join(path, "videos", csv_manager.video_name)
    output_folder = os.path.join(path, "highlights")

    # Compress video first
    compressed_video_path = os.path.join(path, "videos", f"compressed_{csv_manager.video_name}")
    compress_video(video_path, compressed_video_path)
    video_path = compressed_video_path

    # Get peaks
    peaks = csv_manager.detect_peaks(kind='acceleration', top_n=5, plot=True)
    peak_times = [p[0] for p in peaks]

    print(f"Peak times: {peak_times}")

    # Get intervals for clips
    clips_duration = get_interval_clip(peak_times, clip_duration=(0.5, 1.5))

    print(f"Clips duration: {clips_duration}")

    # Create highlight clips
    create_highlight_clips(video_path, clips_duration, output_folder, join=True)

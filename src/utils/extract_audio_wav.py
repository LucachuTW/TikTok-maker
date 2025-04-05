#!/usr/bin/env python3
import ffmpeg  # Import the ffmpeg-python library
import sys
import os

def extract_audio_ffmpeg(input_video_path, output_audio_path):
    """
    Extracts the audio stream from a video file to WAV format using ffmpeg-python.

    Args:
        input_video_path (str): Path to the input video file.
        output_audio_path (str): Path for the output WAV audio file.

    Returns:
        bool: True if extraction was successful, False otherwise.
    """
    print(f"Attempting to extract audio from '{input_video_path}' to '{output_audio_path}' using ffmpeg-python...")

    # Check if input file exists
    if not os.path.isfile(input_video_path):
        print(f"Error: Input file not found: {input_video_path}", file=sys.stderr)
        return False

    try:
        # Set up the FFmpeg stream using ffmpeg-python
        stream = ffmpeg.input(input_video_path)

        # Select only the audio stream and specify output parameters.
        # The '.wav' extension usually implies pcm_s16le, but we specify it for certainty.
        # 'vn=True' (no video) is implied when only outputting audio.
        stream = ffmpeg.output(stream, output_audio_path, acodec='pcm_s16le')

        # Execute the FFmpeg command.
        # overwrite_output=True allows overwriting the output file if it already exists.
        # capture_stdout/stderr=True allows capturing FFmpeg's messages if needed.
        print("Running FFmpeg command...")
        ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)

        print("Audio extraction completed successfully!")
        return True

    except ffmpeg.Error as e:
        # Catch errors specific to ffmpeg execution
        print("Error during FFmpeg execution:", file=sys.stderr)
        # FFmpeg often prints useful information to stderr
        print("FFmpeg stderr:", file=sys.stderr)
        print(e.stderr.decode('utf8'), file=sys.stderr)
        return False
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return False

# --- Main execution block ---
if __name__ == "__main__":
    # Check if the correct number of command-line arguments is provided
    if len(sys.argv) != 3:
        print(f"Usage: python3 {sys.argv[0]} <input_video.mp4> <output_audio.wav>", file=sys.stderr)
        sys.exit(1) # Exit with an error code

    # Get input and output paths from arguments
    video_input = sys.argv[1]
    audio_output = sys.argv[2]

    # Call the extraction function
    if not extract_audio_ffmpeg_python(video_input, audio_output):
        print("Audio extraction failed.", file=sys.stderr)
        sys.exit(1) # Exit with an error code
    else:
        print("Process finished.")
        sys.exit(0) # Exit successfully

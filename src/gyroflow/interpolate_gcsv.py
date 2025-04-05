#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import csv
import cv2  # OpenCV for video processing
import numpy as np

def get_video_properties(video_path):
    """Gets FPS and frame count from a video file."""
    if not os.path.isfile(video_path):
        print(f"Error: Video file not found: {video_path}", file=sys.stderr)
        return None, None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}", file=sys.stderr)
        return None, None

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if fps is None or frame_count is None or fps <= 0 or frame_count <= 0:
         print(f"Error: Could not read valid FPS or frame count from: {video_path}", file=sys.stderr)
         return None, None

    print(f"Video properties: FPS={fps:.3f}, Frame Count={frame_count}")
    return fps, frame_count

def read_and_prepare_gcsv_data(gcsv_path):
    """Reads GCSV, applies tscale, and returns data as numpy arrays."""
    if not os.path.isfile(gcsv_path):
        print(f"Error: GCSV file not found: {gcsv_path}", file=sys.stderr)
        return None

    timestamps_sec = []
    gyro_data = []  # To store [rx, ry, rz]
    accel_data = [] # To store [ax, ay, az]

    tscale = None
    header_found = False
    expected_cols = 7 # t, rx, ry, rz, ax, ay, az

    print(f"Reading GCSV file: {gcsv_path}")
    try:
        with open(gcsv_path, 'r', encoding='utf-8') as infile:
            for line_num, line in enumerate(infile):
                line = line.strip()
                if not line:
                    continue

                if not header_found:
                    # --- Process Metadata and Header ---
                    if line.lower().startswith('tscale,'):
                        try:
                            tscale = float(line.split(',')[1])
                            print(f"  Found tscale: {tscale}")
                        except (IndexError, ValueError):
                            print(f"Error: Invalid tscale format in line: {line}", file=sys.stderr)
                            return None
                    elif line.lower().startswith('t,rx,ry,rz,ax,ay,az'):
                        header_found = True
                        print("  GCSV data header found.")
                    # Copy other metadata somewhere if needed, otherwise ignore for this script
                else:
                    # --- Process Data Lines ---
                    if tscale is None:
                        print("Error: 'tscale' not found in GCSV metadata before data lines.", file=sys.stderr)
                        return None

                    parts = line.split(',')
                    if len(parts) != expected_cols:
                        print(f"Warning: Skipping line {line_num+1}, expected {expected_cols} columns, got {len(parts)}: {line}", file=sys.stderr)
                        continue

                    try:
                        # Convert to float, apply tscale to timestamp
                        raw_t = float(parts[0])
                        timestamp_sec = raw_t * tscale
                        rx, ry, rz = float(parts[1]), float(parts[2]), float(parts[3])
                        ax, ay, az = float(parts[4]), float(parts[5]), float(parts[6])

                        timestamps_sec.append(timestamp_sec)
                        gyro_data.append([rx, ry, rz])
                        accel_data.append([ax, ay, az])

                    except ValueError as e:
                        print(f"Warning: Skipping line {line_num+1} due to value error ({e}): {line}", file=sys.stderr)
                        continue

        if not header_found:
             print("Error: Data header 't,rx,ry,rz,ax,ay,az' not found in GCSV file.", file=sys.stderr)
             return None
        if not timestamps_sec:
            print("Error: No valid data lines found after header in GCSV file.", file=sys.stderr)
            return None

        print(f"  Read {len(timestamps_sec)} GCSV data points.")
        # Convert lists to numpy arrays for efficient processing
        gcsv_data = {
            "timestamps_sec": np.array(timestamps_sec),
            "gyro": np.array(gyro_data),
            "accel": np.array(accel_data)
        }
        return gcsv_data

    except IOError as e:
        print(f"Error reading GCSV file: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading GCSV: {e}", file=sys.stderr)
        return None


def interpolate_data_for_frames(gcsv_data, fps, frame_count):
    """Interpolates GCSV data at each video frame timestamp."""
    if frame_count <= 0 or fps <= 0:
        return None

    # Calculate timestamps for the center of each video frame
    # Alternatively, use start of frame: np.arange(frame_count) / fps
    frame_timestamps_sec = (np.arange(frame_count) + 0.5) / fps
    print(f"Calculating target timestamps for {frame_count} frames (center-frame)...")

    original_gcsv_times = gcsv_data["timestamps_sec"]
    output_data = []

    # Check if frame timestamps are within the range of GCSV timestamps
    min_gcsv_time = original_gcsv_times[0]
    max_gcsv_time = original_gcsv_times[-1]
    min_frame_time = frame_timestamps_sec[0]
    max_frame_time = frame_timestamps_sec[-1]

    if min_frame_time < min_gcsv_time or max_frame_time > max_gcsv_time:
        print("Warning: Video frame times extend beyond the range of GCSV timestamps.", file=sys.stderr)
        print(f"  Video time range: [{min_frame_time:.3f}s, {max_frame_time:.3f}s]", file=sys.stderr)
        print(f"  GCSV time range:  [{min_gcsv_time:.3f}s, {max_gcsv_time:.3f}s]", file=sys.stderr)
        print("  Interpolation at the edges will use boundary values.", file=sys.stderr)
        # Optional: Add stricter handling here if needed (e.g., error out)

    print("Interpolating Gyro data...")
    interp_gyro_x = np.interp(frame_timestamps_sec, original_gcsv_times, gcsv_data["gyro"][:, 0])
    interp_gyro_y = np.interp(frame_timestamps_sec, original_gcsv_times, gcsv_data["gyro"][:, 1])
    interp_gyro_z = np.interp(frame_timestamps_sec, original_gcsv_times, gcsv_data["gyro"][:, 2])

    print("Interpolating Accelerometer data...")
    interp_accel_x = np.interp(frame_timestamps_sec, original_gcsv_times, gcsv_data["accel"][:, 0])
    interp_accel_y = np.interp(frame_timestamps_sec, original_gcsv_times, gcsv_data["accel"][:, 1])
    interp_accel_z = np.interp(frame_timestamps_sec, original_gcsv_times, gcsv_data["accel"][:, 2])

    print("Formatting output data...")
    for i in range(frame_count):
        output_data.append({
            "frame": i,
            "timestamp_sec": frame_timestamps_sec[i],
            "gyro_x": interp_gyro_x[i],
            "gyro_y": interp_gyro_y[i],
            "gyro_z": interp_gyro_z[i],
            "accel_x": interp_accel_x[i],
            "accel_y": interp_accel_y[i],
            "accel_z": interp_accel_z[i],
        })

    return output_data

def interpolate_data_for_frames_from_video_path(video_path, gcsv_path):
    """Wrapper to read video properties and GCSV data, then interpolate."""
    fps, frame_count = get_video_properties(video_path)
    if fps is None or frame_count is None:
        return None

    gcsv_data = read_and_prepare_gcsv_data(gcsv_path)
    if gcsv_data is None:
        return None

    return interpolate_data_for_frames(gcsv_data, fps, frame_count)

# --- Main execution block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Interpolate GCSV gyro/accel data for each frame of a video.",
        epilog="Note: This script provides interpolated data per frame. Gyroflow typically does NOT require this pre-processing as it handles synchronization internally."
    )
    parser.add_argument("gcsv_file", help="Path to the input GCSV file.")
    parser.add_argument("video_file", help="Path to the corresponding video file.")
    parser.add_argument("output_csv", help="Path to save the output CSV file with interpolated data per frame.")

    args = parser.parse_args()

    # 1. Get Video Properties
    print("-" * 10, "Step 1: Reading Video Properties", "-" * 10)
    fps, frame_count = get_video_properties(args.video_file)
    if fps is None:
        sys.exit(1)

    # 2. Read and Prepare GCSV Data
    print("-" * 10, "Step 2: Reading GCSV Data", "-" * 10)
    gcsv_data = read_and_prepare_gcsv_data(args.gcsv_file)
    if gcsv_data is None:
        sys.exit(1)

    # 3. Interpolate Data
    print("-" * 10, "Step 3: Interpolating Data", "-" * 10)
    interpolated_results = interpolate_data_for_frames(gcsv_data, fps, frame_count)
    if interpolated_results is None:
        print("Error during interpolation step.", file=sys.stderr)
        sys.exit(1)

    # 4. Write Output CSV
    print("-" * 10, "Step 4: Writing Output CSV", "-" * 10)
    try:
        print(f"Writing interpolated data to: {args.output_csv}")
        # Define CSV header based on keys in the dictionary
        fieldnames = interpolated_results[0].keys() if interpolated_results else []

        with open(args.output_csv, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(interpolated_results)
        print(f"Successfully wrote {len(interpolated_results)} lines to output file.")

    except IOError as e:
        print(f"Error writing output CSV file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while writing output: {e}", file=sys.stderr)
        sys.exit(1)

    print("-" * 10, "Script finished successfully.", "-" * 10)
    print("\nReminder: Gyroflow usually performs synchronization internally and does not need this pre-interpolated data.")
    sys.exit(0)
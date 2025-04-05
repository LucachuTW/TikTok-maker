

**Version:** 1.0 (ESEI Hackathon Version)
**Authors:** [Javier Pérez Robles, Sergio González Rodríguez, Lucas González Fiz] - Students at ESEI, University of Vigo.

## 1. Introduction

This document provides detailed documentation for the Automated Action Cam Video Processor, a Python project developed during the ESEI Hackathon. The primary goal of this project is to create an automated, end-to-end pipeline for processing footage from action cameras (like Runcam).

The workflow encompasses several stages: automatically detecting camera connections, downloading video and associated sensor (gyro/accelerometer) data, extracting audio, preparing for and facilitating video stabilization using the external Gyroflow tool, analyzing sensor data to identify key moments (e.g., hard braking), and generating compressed highlight clips based on these moments.

This documentation details the project's architecture, the core workflow executed by the main script, the functionality of individual modules, configuration steps, dependencies, and usage instructions.

## 2. Architecture Overview

The system is built around a central orchestrator script (`main.py`) that utilizes various utility modules located in the `src/utils/` directory. Configuration is managed centrally via `src/config/config.yaml`, and logging is handled by modules in `src/logger/`. Integration with external tools like `ffmpeg` (for audio/video processing) and `gyroflow` (for stabilization) is achieved through Python's `subprocess` module and specific helper scripts.

**Data Flow:**

1.  **Camera Connection:** `pyudev` detects a known camera connected via USB.
2.  **Mounting:** `sudo mount` is called to access the camera filesystem.
3.  **File Download:** `.MP4` and `.gcsv` files are copied to a local, structured directory defined in `config.yaml`.
4.  **Unmounting:** `sudo umount` releases the camera.
5.  **Audio Extraction:** `ffmpeg` extracts audio from downloaded videos into `.wav` files.
6.  **Stabilization (Semi-automated):** User selects video; helper scripts (`gyroflow/run_gyroflow.py`) prepare and execute the external `gyroflow` command using the video and corresponding GCSV data.
7.  **Sensor Analysis (for Clipping):** `pandas` and `scipy` analyze GCSV data to find peaks (e.g., acceleration).
8.  **Clipping (Semi-automated):** `moviepy` cuts video segments around detected peaks; `ffmpeg` can be used for pre-compression.

## 3. Core Workflow (`main.py`)

The main script (`src/main.py`) drives the automated process in a continuous loop:

1.  **Initialization:** Instantiates configuration (`ConfigManager`) and camera handling (`Camera`).
2.  **Wait for Camera:** The `Camera` class initialization blocks execution (`_wait_for_camera`) until a USB device matching a serial number listed in `config.yaml` is connected.
3.  **Mount Device:** Once detected, `camera.mount()` attempts to mount the camera's storage partition(s) to a local directory (`~/camera_mount` by default) using `sudo mount`.
4.  **Download Files:** `camera.download()` scans the mounted camera (typically the `DCIM` folder), identifies `.MP4` and `.gcsv` files, groups them by base name, creates a subdirectory for each recording under the path specified in `config.yaml`, and copies the files (`shutil.copy2`).
5.  **Unmount Device:** `camera.unmount()` unmounts the camera filesystem using `sudo umount -l` and attempts to clean up the mount point directory.
6.  **List Downloaded Videos:** `list_videos()` scans the download directory structure to find all processed `.mp4` files.
7.  **Automatic Audio Extraction:** `extract_audio()` is called for all downloaded videos. It uses `utils/extract_audio_wav.py` to create a `.wav` file containing the audio track for each video, saved within an `audio` subfolder next to the video file.
8.  **Interactive Stabilization Prompt:** The script lists available videos and uses `choose_files()` to ask the user (via console input) which videos they wish to stabilize. The selected files are passed to the `stabilish()` function, which is currently a **placeholder** and only prints the selected files. *Actual stabilization requires running `gyroflow` externally, potentially using `src/gyroflow/run_gyroflow.py`.*
9.  **Interactive Clipping Prompt:** The script lists available videos again and asks the user which ones to process for highlight clips. The selected files are passed to the `clip()` function, which is also currently a **placeholder**. *Actual clipping involves analyzing the corresponding GCSV with `utils/manage_csv.py` and cutting the video with `utils/edit_video.py`.*
10. **Loop Restart:** The script prints "Restarting loop..." and returns to step 2 (Wait for Camera). The loop can be interrupted with `Ctrl+C`.

## 4. Modules and Components

This section details the purpose and key functionalities of the individual Python scripts and modules.

### 4.1. `main.py`
* **Purpose:** Main entry point and orchestrator of the entire workflow.
* **Key Functions:** Implements the core loop (wait, mount, download, unmount, process), lists available videos, handles user interaction for selecting files for stabilization/clipping (currently via placeholder functions `stabilish`, `clip`), and calls utility functions for audio extraction.
* **Dependencies:** `utils.config_manager`, `utils.camera`, `utils.extract_audio_wav`, `os`.

### 4.2. `utils/config_manager.py`
* **Purpose:** Manages loading and accessing configuration settings from `config/config.yaml`.
* **Key Class:** `ConfigManager`.
* **Functionality:** Ensures the config file exists (creates a default if not), loads YAML data, automatically replaces the `[user]` placeholder in paths with the current username. Provides access to config values via its `config` attribute.
* **Dependencies:** `os`, `yaml`, `getpass`.

### 4.3. `utils/camera.py`
* **Purpose:** Handles all interactions with the connected action camera.
* **Key Class:** `Camera`.
* **Functionality:**
    * `__init__` / `_wait_for_camera`: Uses `pyudev` to monitor USB connections and blocks until a camera with a matching serial from `config.yaml` is found. Stores device details.
    * `mount`: Finds the correct partition for the detected device and uses `sudo mount` to mount it.
    * `download`: Scans the camera's `DCIM` directory, copies `.MP4` and `.gcsv` files to the configured local path, creating subdirectories for each recording.
    * `unmount`: Uses `sudo umount -l` to unmount the device and cleans up the mount point.
* **Dependencies:** `pyudev`, `os`, `subprocess`, `shutil`, `time`, `utils.config_manager`, `logger.logger_manager`. Requires `sudo` privileges for mount/unmount.

### 4.4. `utils/extract_audio_wav.py`
* **Purpose:** Extracts audio tracks from video files into WAV format.
* **Key Function:** `extract_audio_ffmpeg`.
* **Functionality:** Takes input video and output audio paths. Uses the `ffmpeg-python` library to construct and run an `ffmpeg` command (`ffmpeg -i video.mp4 -vn -acodec pcm_s16le audio.wav`) to perform the extraction. Includes error handling for `ffmpeg` execution. Can also be run as a standalone script.
* **Dependencies:** `ffmpeg-python`, `sys`, `os`. Requires `ffmpeg` CLI tool.

### 4.5. `utils/manage_csv.py`
* **Purpose:** Reads, processes, analyzes, and plots data from Gyroflow GCSV files.
* **Key Class:** `CSVManager`.
* **Functionality:**
    * `__init__` / `create_dataframe`: Reads GCSV metadata (like `tscale`, `gscale`, `ascale`, `videofilename`) and data into a `pandas` DataFrame. Applies scaling factors to create columns with physical units (seconds, degrees, g's).
    * `plot_csv`: Uses `matplotlib` to generate plots of gyroscope and accelerometer data over time.
    * `detect_peaks`: Calculates acceleration or rotation magnitude. Uses `scipy.signal.find_peaks` to identify significant peaks (custom logic for braking detection by looking at negative acceleration). Returns timestamps and values of top peaks. Optionally plots the magnitude and detected peaks.
* **Dependencies:** `pandas`, `matplotlib`, `numpy`, `scipy`, `os`, `utils.config_manager`.

### 4.6. `utils/edit_video.py`
* **Purpose:** Provides functions for video editing tasks like compression and clipping.
* **Key Functions:**
    * `compress_video`: Compresses a video using `ffmpeg` via `subprocess`. Allows setting CRF (quality) and resizing. Removes audio during compression.
    * `get_interval_clip`: Takes a list of peak timestamps (from `manage_csv.py`) and generates start/end time tuples for video clips around these peaks, merging overlapping intervals.
    * `create_highlight_clips`: Takes a video path and a list of time intervals. Uses `moviepy` (`VideoFileClip.subclip`) to extract these segments. Optionally uses `moviepy.concatenate_videoclips` to join them into a single highlight reel. Saves output clips to a specified folder.
* **Dependencies:** `moviepy`, `manage_csv`, `config_manager`, `os`, `subprocess`. Requires `ffmpeg` CLI tool for compression.

### 4.7. `logger/logger_manager.py`
* **Purpose:** Configures the standard Python `logging` system for the application.
* **Key Class:** `Logger`.
* **Functionality:** Sets up logging handlers based on configuration and instantiation parameters:
    * Console Handler (`StreamHandler`): Logs messages to `stdout`.
    * File Handler (`RotatingFileHandler`): Logs messages to a file specified in `config.yaml`, with rotation based on size.
    * SQLite Handler (`logger.sqlite_handler.SQLiteHandler`): Optionally logs structured data to an SQLite database (path from `config.yaml`).
    * Provides wrapper methods (`info`, `error`, etc.) for easy use.
* **Dependencies:** `logging`, `sys`, `os`, `getpass`, `logger.sqlite_handler`, `utils.config_manager`.

### 4.8. `logger/sqlite_handler.py`
* **Purpose:** A custom logging handler to write selected log information to an SQLite database.
* **Key Class:** `SQLiteHandler`.
* **Functionality:** Inherits from `logging.Handler`. Creates/connects to an SQLite DB file. Defines a simplified table (`logs`) to store timestamp, logger name, message, and a custom `event_type` (extracted from the log record's `extra` dict if provided). Handles database connection and insertion in a thread-safe manner.
* **Dependencies:** `logging`, `sqlite3`, `os`, `threading`, `sys`.

### 4.9. `gyroflow/run_gyroflow.py`
* **Purpose:** A command-line script to execute the external Gyroflow stabilization tool with specific parameters.
* **Key Function:** `run_gyroflow`.
* **Functionality:** Uses `argparse` to accept paths for the video file, Gyroflow project file (`.gyroflow`), GCSV data file, and optionally the path to the `gyroflow` executable and an overwrite flag. Constructs the correct `gyroflow` command-line arguments based on Gyroflow v1.6.0 syntax (`gyroflow video.mp4 project.gyroflow -g data.gcsv [-f]`). Executes the command using `subprocess.run`, capturing output and handling errors.
* **Dependencies:** `argparse`, `subprocess`, `sys`, `os`, `shlex`. Requires `gyroflow` CLI tool.

### 4.10. `gyroflow/interpolate_gcsv.py`
* **Purpose:** A utility script to interpolate high-frequency GCSV sensor data to match the timestamps of each frame in a lower-frequency video file. **Note: This is generally NOT needed for Gyroflow itself.**
* **Key Functions:** `get_video_properties`, `read_and_prepare_gcsv_data`, `interpolate_data_for_frames`.
* **Functionality:** Reads video FPS and frame count using OpenCV. Reads GCSV data, applying `tscale`. Calculates the timestamp for each video frame (e.g., frame center time). Uses `numpy.interp` to perform linear interpolation of each gyro and accelerometer axis at the precise frame timestamps. Writes the results (frame number, timestamp, interpolated sensor values) to a new CSV file.
* **Dependencies:** `argparse`, `os`, `sys`, `csv`, `cv2` (opencv-python), `numpy`.

*(Note: `gyroflow/gyroflow.sh` has been omitted from this documentation as requested).*

## 5. Configuration (`config/config.yaml`)

The `config.yaml` file centralizes key settings:

* **`cameras`**: (List of strings) Contains the USB serial numbers of the action cameras that the script should recognize and process upon connection. Example: `["SERIAL123", "SERIAL456"]`.
* **`camera_path`**: (String) The base directory path on your local machine where downloaded files (videos, GCSV) will be stored. Subdirectories named after the recording (e.g., `Runcam6_0001`) will be created here. The placeholder `[user]` is automatically replaced with your username (e.g., `/home/[user]/camera` becomes `/home/your_user/camera`).
* **`logs`**: (Dictionary) Contains settings for logging:
    * `path`: (String) Full path for the rotating log file (e.g., `/home/[user]/logs/app.log`). `[user]` is replaced.
    * `sqlite_file`: (String) Full path for the SQLite database file if SQLite logging is enabled (e.g., `/home/[user]/logs/logs.db`). `[user]` is replaced.

## 6. Dependencies

### 6.1. System Dependencies
* **Linux OS:** Required for `pyudev`, `mount`, `umount`.
* **Python:** Version 3.x.
* **FFmpeg:** Command-line tool (accessible via PATH).
* **Gyroflow:** Command-line tool (accessible via PATH or located correctly).
* **sudo:** Required for mount/unmount operations.
* **libc++1** Required to use gyroflow

### 6.2. Python Libraries
These can be installed using pip:
```bash
pip install -r requirements.txt
```
7. Setup and Installation

    Clone Repository: Obtain the project source code.
    Install System Tools: Install ffmpeg and gyroflow using your distribution's package manager or download them from their official websites. Ensure they are executable and in your system's PATH.
    Install Python Libraries: Navigate to the project directory (or virtual environment) and run:
    Bash

    pip install -r requirements.txt

    (Assuming a requirements.txt file is created with the libraries listed above. If not, install them individually using the pip command from section 6.2).
    Configure sudo (Optional): If you require fully unattended operation, configure sudoers to allow passwordless execution of mount and umount for the specific device/mount point used by the script. This requires careful setup to maintain system security.
    Configure config.yaml: Edit src/config/config.yaml to add your camera's serial number(s) and verify/adjust the file paths. Ensure the specified directories exist or the script has permission to create them.

8. Running the Application

Execute the main workflow script from the project's root directory:
Bash

python3 src/main.py

The script will then:

    Log initialization messages.
    Wait for a recognized camera to be connected via USB.
    Proceed through the automated download and audio extraction steps upon detection.
    Present interactive prompts in the console asking the user to select videos for stabilization and clipping (these steps currently require manual follow-up or further integration).
    Loop back to wait for the next camera connection after completing the interactive steps. Press Ctrl+C to exit the script.

9. Manual Script Execution

Besides the main workflow, individual utility scripts can be run manually:

    Stabilizing a Video (using run_gyroflow.py):
    Bash

python3 src/gyroflow/run_gyroflow.py \
  --video /path/to/Runcam6_0001/Runcam6_0001.MP4 \
  --project /path/to/your_settings.gyroflow \
  --gcsv /path/to/Runcam6_0001/Runcam6_0001_synced.gcsv \
  --gyroflow-path /path/to/your/gyroflow # Optional

Interpolating GCSV Data (using interpolate_gcsv.py):
Bash

    python3 src/gyroflow/interpolate_gcsv.py \
      /path/to/Runcam6_0001/Runcam6_0001.gcsv \
      /path/to/Runcam6_0001/Runcam6_0001.MP4 \
      /path/to/Runcam6_0001/interpolated_data.csv

    Generating Highlights Example (adapting edit_video.py): You can run python3 src/utils/edit_video.py. The if __name__ == "__main__": block in that script demonstrates compressing a specific video, finding acceleration peaks in its GCSV, and creating a joined highlight clip. Modify the paths within that block to test on other files.

10. Future Work / TODOs

    
Full Stabilization Integration: Implement the logic within main.py's stabilish function to properly call run_gyroflow.py (or use subprocess directly) based on user selection, managing input/output paths and potentially Gyroflow project files.
Full Clipping Integration: Implement the logic within main.py's clip function to utilize manage_csv.py for peak detection on the selected video's GCSV and edit_video.py to perform the actual video cutting and joining.
GCSV Synchronization: Add an optional, automatic step (perhaps using logic similar to sync_gcsv_100hz.py if needed based on camera) after download to ensure GCSV timestamps are correct before stabilization or analysis.
Configuration Expansion: Add more options to config.yaml (e.g., Gyroflow executable path, stabilization parameters, peak detection thresholds, clip padding times, compression settings).
Robustness: Add more comprehensive error handling for external tool failures, file system issues, and unexpected data formats.
User Interface: Develop a Graphical User Interface (GUI) (e.g., using PyQt, Kivy, Tkinter) to replace the console-based interaction for a more user-friendly experience.
Packaging: Structure the project for easier distribution and installation (e.g., using setup.py or pyproject.toml).
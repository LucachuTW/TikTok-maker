import argparse
import subprocess
import sys
import os
import shlex # Used for safer printing of the command

def run_gyroflow(gyroflow_path, video_path, project_path, gcsv_path, overwrite=False):
    """
    Constructs and runs the Gyroflow command based on the determined syntax
    for Gyroflow v1.6.0 (gh2204).
    """

    # --- 1. Validate Paths ---
    # Ensure the Gyroflow executable path exists and is executable (basic check)
    if not os.path.isfile(gyroflow_path) or not os.access(gyroflow_path, os.X_OK):
         # Try adding './' if just a name was given, assuming it's in the current dir
         if os.path.isfile("./" + gyroflow_path) and os.access("./" + gyroflow_path, os.X_OK):
             gyroflow_path = "./" + gyroflow_path
         else:
            print(f"Error: Gyroflow executable not found or not executable at '{gyroflow_path}'", file=sys.stderr)
            sys.exit(1)

    # Ensure input files exist
    if not os.path.isfile(video_path):
        print(f"Error: Video file not found at '{video_path}'", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(project_path):
        print(f"Error: Gyroflow project file not found at '{project_path}'", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(gcsv_path):
        print(f"Error: GCSV gyro data file not found at '{gcsv_path}'", file=sys.stderr)
        sys.exit(1)

    # --- 2. Construct Command ---
    # Use absolute paths for robustness when calling subprocess
    abs_gyroflow_path = os.path.abspath(gyroflow_path)
    abs_video_path = os.path.abspath(video_path)
    abs_project_path = os.path.abspath(project_path)
    abs_gcsv_path = os.path.abspath(gcsv_path)

    # Command structure based on gyroflow --help for v1.6.0
    command = [
        abs_gyroflow_path,
        abs_video_path,      # Positional argument 1: video file
        abs_project_path,    # Positional argument 2: project file
        "-g", abs_gcsv_path  # Option -g for gyro file
    ]

    # Add overwrite flag if requested by the user
    if overwrite:
        command.append("-f") # Append the -f option

    # --- 3. Execute Command ---
    # shlex.join is good for printing the command in a copy-paste friendly way
    print(f"Executing Gyroflow command:\n{shlex.join(command)}\n")

    try:
        # Run the command. check=True raises CalledProcessError on non-zero exit code.
        # capture_output=True captures stdout/stderr. text=True decodes them as text.
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')

        print("--- Gyroflow execution successful! ---")
        # Print stdout/stderr from Gyroflow for information (might contain warnings)
        if result.stdout:
            print("\nGyroflow stdout:")
            print(result.stdout.strip())
        if result.stderr:
            print("\nGyroflow stderr:")
            print(result.stderr.strip())
        print("--------------------------------------")

    except subprocess.CalledProcessError as e:
        # Handle errors reported by Gyroflow (non-zero exit code)
        print(f"\n--- Error: Gyroflow execution failed! (Exit Code: {e.returncode}) ---", file=sys.stderr)
        if e.stdout:
            print("\nGyroflow stdout:", file=sys.stderr)
            print(e.stdout.strip(), file=sys.stderr)
        if e.stderr:
            print("\nGyroflow stderr:", file=sys.stderr)
            print(e.stderr.strip(), file=sys.stderr)
        print("------------------------------------------------------------", file=sys.stderr)
        sys.exit(e.returncode) # Exit script with the same code Gyroflow used
    except Exception as e:
        # Handle other potential errors during subprocess execution
        print(f"\nAn unexpected error occurred while trying to run Gyroflow: {e}", file=sys.stderr)
        sys.exit(1)


# --- 4. Script Argument Parsing ---
if __name__ == "__main__":
    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Automate Gyroflow CLI execution using video, project, and gcsv files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Show default values in help
    )

    # Define required arguments
    parser.add_argument("-v", "--video", required=True,
                        help="Path to the input video file (.MP4)")
    parser.add_argument("-p", "--project", required=True,
                        help="Path to the Gyroflow project settings file (.gyroflow)")
    parser.add_argument("-gcsv", "--gcsv", required=True,
                        help="Path to the GCSV gyro data file (.gcsv)")

    # Define optional arguments
    parser.add_argument("--gyroflow-path", default="./gyroflow",
                        help="Path to the Gyroflow executable")
    parser.add_argument("-f", "--overwrite", action="store_true", # 'store_true' means it's a flag
                        help="Allow overwriting existing output file (adds -f flag to Gyroflow)")

    # Parse the arguments provided when the script is run
    args = parser.parse_args()

    # Call the main function with the parsed arguments
    run_gyroflow(
        gyroflow_path=args.gyroflow_path,
        video_path=args.video,
        project_path=args.project,
        gcsv_path=args.gcsv,
        overwrite=args.overwrite
    )

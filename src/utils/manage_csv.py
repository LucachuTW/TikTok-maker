from utils.config_manager import ConfigManager
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from scipy.signal import find_peaks

config = ConfigManager()

class CSVManager:
    """
    Class to manage CSV files.
    """
    def __init__(self, path):
        """
        Initializes the CSVManager with a given path.
        Path of the GCSV file
        """
        self.path_file = path 
        self.data = None
        self.video_name = None
        self.create_dataframe()

    def create_dataframe(self):
        with open(self.path_file) as f:
            lines = f.readlines()

        tscale = gscale = ascale = None
        header_lines = []
        data_start_index = 0
        for i, line in enumerate(lines):
            if line.startswith("videofilename"):
                self.video_name = line.strip().split(",")[1]
            elif line.startswith("tscale"):
                tscale = float(line.split(",")[1])
            elif line.startswith("gscale"):
                gscale = float(line.split(",")[1])
            elif line.startswith("ascale"):
                ascale = float(line.split(",")[1])
            elif line.startswith("t,rx,ry,rz,ax,ay,az"):
                data_start_index = i
                break
            header_lines.append(line.strip())

        self.data = pd.read_csv(self.path_file, skiprows=data_start_index)

        self.data["time_s"] = self.data["t"] * tscale
        self.data["rx_deg"] = self.data["rx"] * gscale
        self.data["ry_deg"] = self.data["ry"] * gscale
        self.data["rz_deg"] = self.data["rz"] * gscale
        self.data["ax_g"] = self.data["ax"] * ascale
        self.data["ay_g"] = self.data["ay"] * ascale
        self.data["az_g"] = self.data["az"] * ascale

    def plot_csv(self):
        """
        Plot gyro and accelerometer data.
        """
        data = self.data

        # Plot gyroscope
        plt.figure(figsize=(12, 6))
        plt.plot(data["time_s"], data["rx_deg"], label="rx (deg)")
        plt.plot(data["time_s"], data["ry_deg"], label="ry (deg)")
        plt.plot(data["time_s"], data["rz_deg"], label="rz (deg)")
        plt.title("Rotation (gyroscope)")
        plt.xlabel("Time (s)")
        plt.ylabel("Rotation (degrees)")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.show()

        # Plot accelerometer
        plt.figure(figsize=(12, 6))
        plt.plot(data["time_s"], data["ax_g"], label="ax (g)")
        plt.plot(data["time_s"], data["ay_g"], label="ay (g)")
        plt.plot(data["time_s"], data["az_g"], label="az (g)")
        plt.title("Acceleration (accelerometer)")
        plt.xlabel("Time (s)")
        plt.ylabel("Acceleration (g)")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.show()

    def detect_peaks(self, kind='acceleration', top_n=3, plot=True):
        """
        Detect the top peaks distributed across video segments.

        :param kind: 'acceleration' or 'rotation'
        :param top_n: Final number of top peaks to return (after segment selection)
        :param plot: Whether to show a plot
        :return: List of (time, value) of the top peaks
        """
        if self.data is None:
            print("No data loaded.")
            return []

        # Select magnitude based on kind
        if kind == 'acceleration':
            ax = self.data["ax_g"]
            magnitude = -ax  # invert for braking
            ylabel = "Braking Force (-ax in g)"
            threshold = -np.percentile(ax, 5)
        elif kind == 'rotation':
            magnitude = np.sqrt(
                self.data["rx_deg"]**2 + self.data["ry_deg"]**2 + self.data["rz_deg"]**2
            )
            ylabel = "Total Rotation (°/s)"
            threshold = np.percentile(magnitude, 95)
        else:
            raise ValueError("Kind must be 'acceleration' or 'rotation'.")

        # Detect peaks
        indices, properties = find_peaks(magnitude, height=threshold)
        peak_times = self.data["time_s"].iloc[indices].values
        peak_values = properties["peak_heights"]
        all_peaks = list(zip(peak_times, peak_values))

        # Segment the time axis into 10 parts
        total_time = self.data["time_s"].iloc[-1]
        segment_duration = total_time / 10
        segment_best_peaks = []

        for i in range(10):
            start = i * segment_duration
            end = (i + 1) * segment_duration
            segment_peaks = [
                (t, v) for t, v in all_peaks if start <= t < end
            ]
            if segment_peaks:
                # Select the max peak in the segment
                best = max(segment_peaks, key=lambda x: x[1])
                segment_best_peaks.append(best)

        # From segment-best peaks, select the top N globally
        segment_best_peaks.sort(key=lambda x: x[1], reverse=True)
        selected_peaks = segment_best_peaks[:top_n]

        # Plot if needed
        if plot:
            plt.figure(figsize=(12, 6))
            plt.plot(self.data["time_s"], magnitude, label="Magnitude")
            times = [p[0] for p in selected_peaks]
            vals = [p[1] for p in selected_peaks]
            plt.plot(times, vals, "rx", label=f"Top {len(selected_peaks)} Peaks")
            plt.title(f"Top {len(selected_peaks)} {kind.capitalize()} Peaks (Segmented)")
            plt.xlabel("Time (s)")
            plt.ylabel(ylabel)
            plt.legend()
            plt.grid()
            plt.tight_layout()
            plt.show()

        return selected_peaks



if __name__ == "__main__":
    # Example usage
    path = config.config.get("camera_path", None)
    path_file = os.path.join(path, "gcsv", "Runcam6_0002.gcsv")
    csv_manager = CSVManager(path_file)
    csv_manager.plot_csv()
    print(f"Nombre del video: {csv_manager.video_name}")
    peaks = csv_manager.detect_peaks(kind='acceleration', top_n = 4, plot=True)
    print(f"Peak times: {peaks}")

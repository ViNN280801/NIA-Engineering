import speedtest
import csv
from datetime import datetime
import logging
import os

NETWORK_SPEED_ANALYZER = "SPEED ANALYZER"

# Setup a default logging configuration
default_logger = logging.getLogger("default_logger")
default_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
default_logger.addHandler(handler)


class NetworkSpeedAnalyzer:
    def __init__(self, filename, logger=None):
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        self.filename = filename
        self.logger = logger if logger is not None else default_logger

    def measure_speed(self):
        """
        Measures the download and upload speed using the speedtest library.
        Returns:
            tuple: download speed and upload speed in bits per second.
        """
        try:
            st = speedtest.Speedtest()
            st.download()
            st.upload()
            st.results.share()

            results_dict = st.results.dict()
            return results_dict["download"], results_dict["upload"]
        except Exception as e:
            self.logger.error(f"Error measuring speed: {e}")
            return None, None

    def write_to_csv(self, download_speed, upload_speed):
        """
        Writes the measured download and upload speeds to a CSV file.
        Args:
            download_speed (float): The download speed in bits per second.
            upload_speed (float): The upload speed in bits per second.
        """
        try:
            with open(self.filename, "a", newline="") as csvfile:
                fieldnames = ["timestamp", "download_speed", "upload_speed"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if csvfile.tell() == 0:
                    writer.writeheader()

                writer.writerow(
                    {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "download_speed": download_speed,
                        "upload_speed": upload_speed,
                    }
                )
            self.logger.info(
                f"Data written to {self.filename}: Download {download_speed / 1_000_000:.2f} Mbps, Upload {upload_speed / 1_000_000:.2f} Mbps"
            )
        except Exception as e:
            self.logger.error(f"Error writing to CSV: {e}")

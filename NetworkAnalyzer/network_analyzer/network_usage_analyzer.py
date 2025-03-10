import psutil
import csv
from datetime import datetime
import logging
import os

NETWORK_USAGE_ANALYZER = "DATA USAGE ANALYZER"

# Setup a default logging configuration
default_logger = logging.getLogger("default_logger")
default_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
default_logger.addHandler(handler)


class NetworkUsageAnalyzer:
    def __init__(self, filename, logger=None):
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        self.filename = filename
        self.logger = logger if logger is not None else default_logger

    def get_network_usage(self):
        """
        Gets the network usage statistics.
        Returns:
            tuple: Bytes sent and bytes received.
        """
        try:
            net_io = psutil.net_io_counters()
            return net_io.bytes_sent, net_io.bytes_recv
        except Exception as e:
            self.logger.error(f"Error getting network usage: {e}")
            return None, None

    def write_to_csv(self, sent_bytes, recv_bytes):
        """
        Writes the network usage statistics to a CSV file.
        Args:
            sent_bytes (int): The number of bytes sent.
            recv_bytes (int): The number of bytes received.
        """
        try:
            with open(self.filename, "a", newline="") as csvfile:
                fieldnames = ["timestamp", "sent_bytes", "recv_bytes"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if csvfile.tell() == 0:
                    writer.writeheader()

                writer.writerow(
                    {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "sent_bytes": sent_bytes,
                        "recv_bytes": recv_bytes,
                    }
                )
            self.logger.info(
                f"Data written to {self.filename}: Sent {sent_bytes / (1024 * 1024):.2f} MB, Received {recv_bytes / (1024 * 1024):.2f} MB"
            )
        except Exception as e:
            self.logger.error(f"Error writing to CSV: {e}")

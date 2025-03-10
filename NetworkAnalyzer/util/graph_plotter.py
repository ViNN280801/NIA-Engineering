import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import logging
import os


class GraphPlotter:
    def __init__(self, network_usage_file, network_speed_file):
        self.network_usage_file = network_usage_file
        self.network_speed_file = network_speed_file

    def plot_speed_graph(self, file, ax, xticks):
        """
        Plot speed graph from the given file.

        Args:
            file (str): The file path to plot data from.
            ax (matplotlib.axes.Axes): The axes to plot the graph on.
            xticks (int): Interval for X-ticks in graphs.
        """
        data = pd.read_csv(file)
        ax.plot(
            data["timestamp"],
            data["download_speed"] / 1_000_000,
            label="Download Speed (Mbps)",
        )
        ax.plot(
            data["timestamp"],
            data["upload_speed"] / 1_000_000,
            label="Upload Speed (Mbps)",
        )
        ax.set_xlabel("Time (HH:MM)")
        ax.set_ylabel("Speed (Mbps)")
        ax.set_title("Network Speed Over Time")
        ax.legend()
        ax.grid(True)
        ax.set_xticks(ax.get_xticks()[::xticks])
        plt.xticks(rotation=45)

    def plot_usage_graph(self, file, ax, xticks):
        """
        Plot usage graph from the given file.

        Args:
            file (str): The file path to plot data from.
            ax (matplotlib.axes.Axes): The axes to plot the graph on.
            xticks (int): Interval for X-ticks in graphs.
        """
        data = pd.read_csv(file)
        ax.plot(
            data["timestamp"],
            data["sent_bytes"] / (1024 * 1024),
            label="Sent Data (MB)",
        )
        ax.plot(
            data["timestamp"],
            data["recv_bytes"] / (1024 * 1024),
            label="Received Data (MB)",
        )
        ax.set_xlabel("Time (HH:MM)")
        ax.set_ylabel("Data (MB)")
        ax.set_title("Network Data Usage Over Time")
        ax.legend()
        ax.grid(True)
        ax.set_xticks(ax.get_xticks()[::xticks])
        plt.xticks(rotation=45)

    def plot_graphs(self, xticks: int, save_path: str = "network_graphs.png"):
        """
        Plots the network usage and speed graphs from the given CSV files and saves them as a PNG file.

        Parameters:
        xticks (int): Interval of x-axis ticks
        save_path (str): Path to save the PNG file
        """
        try:
            # Check if the files exist before attempting to read them
            if not os.path.exists(self.network_usage_file) or not os.path.exists(
                self.network_speed_file
            ):
                logging.error("One or both CSV files do not exist.")
                return

            # Load data from CSV files
            df_usage = pd.read_csv(self.network_usage_file)
            df_speed = pd.read_csv(self.network_speed_file)

            # Convert timestamp to HH:MM format
            df_usage["time"] = pd.to_datetime(df_usage["timestamp"]).dt.strftime(
                "%H:%M"
            )
            df_speed["time"] = pd.to_datetime(df_speed["timestamp"]).dt.strftime(
                "%H:%M"
            )

            # Convert bytes to megabytes for data usage
            df_usage["sent_MB"] = df_usage["sent_bytes"] / (1024 * 1024)
            df_usage["recv_MB"] = df_usage["recv_bytes"] / (1024 * 1024)

            # Convert speed to Mbps
            df_speed["download_Mbps"] = df_speed["download_speed"] / 1_000_000
            df_speed["upload_Mbps"] = df_speed["upload_speed"] / 1_000_000

            # Calculate average speeds
            avg_download_speed = df_speed["download_Mbps"].mean()
            avg_upload_speed = df_speed["upload_Mbps"].mean()

            plt.figure(figsize=(14, 7))

            # Data usage plot
            plt.subplot(2, 1, 1)
            plt.plot(
                df_usage["time"], df_usage["sent_MB"], "r-", label="Sent Data (MB)"
            )
            plt.plot(
                df_usage["time"], df_usage["recv_MB"], "b-", label="Received Data (MB)"
            )
            plt.xlabel("Time (HH:MM)")
            plt.ylabel("Data (MB)")
            plt.title("Data Usage Over Time")
            plt.xticks(np.arange(0, len(df_usage["time"]), step=xticks), rotation=45)
            plt.legend()
            plt.grid(True)

            # Speed plot
            plt.subplot(2, 1, 2)
            plt.plot(
                df_speed["time"],
                df_speed["download_Mbps"],
                "r-",
                label=f"Download Speed (Mbps), Avg: {avg_download_speed:.2f} Mbps",
            )
            plt.plot(
                df_speed["time"],
                df_speed["upload_Mbps"],
                "b-",
                label=f"Upload Speed (Mbps), Avg: {avg_upload_speed:.2f} Mbps",
            )
            plt.xlabel("Time (HH:MM)")
            plt.ylabel("Speed (Mbps)")
            plt.title("Speed Over Time")
            plt.xticks(np.arange(0, len(df_speed["time"]), step=xticks), rotation=45)
            plt.legend()
            plt.grid(True)

            plt.tight_layout()
            plt.savefig(save_path)
            logging.info(f"Plots saved to the file: {save_path}")
            plt.show()
        except Exception as e:
            logging.error(f"Error plotting graphs: {e}")

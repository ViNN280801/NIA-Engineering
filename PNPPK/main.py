#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import signal
import datetime
import traceback
from PyQt5 import QtWidgets
from gui.window import GFRControlWindow


def sigint_handler(signum, frame):
    """
    @brief Signal handler for SIGINT (Ctrl+C).
    @details
    This handler is invoked when the user presses Ctrl+C. It performs a graceful shutdown.
    """
    print("\nCtrl+C detected. Quitting...")
    sys.exit(0)


def _check_qt_plugin_path():
    """
    @brief Check if the QT_PLUGIN_PATH environment variable is set for Windows.
    @details
    This function checks if the QT_PLUGIN_PATH environment variable is set.
    If it is not set, it will print an error message and exit the program.
    """
    if os.name == "nt":
        qt_plugin_path = os.getenv("QT_PLUGIN_PATH")
        if not qt_plugin_path:
            print(
                "QT_PLUGIN_PATH is not set. Please set it to the path of the Qt plugins. "
                "Example: \\venv\\Lib\\site-packages\\PyQt5\\Qt5\\plugins"
            )
            sys.exit(1)


def is_admin():
    """
    @brief Check if the script is running with administrative privileges.
    @return True if running as admin, False otherwise.
    """
    if os.name == "nt":  # Windows
        try:
            # Only administrators can access the C:\Windows\System32\config directory
            os.listdir(os.path.join(os.environ["SystemRoot"], "System32", "config"))
            return True
        except PermissionError:
            return False
    else:  # Linux/macOS
        return os.geteuid() == 0


def elevate_privileges():
    """
    @brief Restart the script with administrative privileges.
    @details
    This function will relaunch the script with elevated privileges.
    """
    if os.name == "nt":  # Windows
        import ctypes

        # Relaunch the script with the 'runas' verb to request admin privileges
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)
    else:  # Linux/macOS
        # Relaunch the script with sudo and preserve environment variables
        print("Restarting with administrative privileges...")
        args = ["sudo", "-E", sys.executable] + sys.argv
        try:
            os.execvp("sudo", args)
        except Exception as e:
            print(f"Failed to restart with sudo: {e}")
            sys.exit(1)


def main():
    """
    @brief Main function to run the RRG control interface.
    @details
    This function initializes the Qt application and displays the RRGControlWindow.
    """
    # Install the SIGINT handler for Ctrl+C.
    signal.signal(signal.SIGINT, sigint_handler)
    app = QtWidgets.QApplication(sys.argv)
    global window
    window = GFRControlWindow()
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    _check_qt_plugin_path()

    try:
        main()
    except Exception:
        # Generate a log filename with the current date and time.
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"crash-log-{now}.log"
        with open(log_filename, "w") as log_file:
            traceback.print_exc(file=log_file)

        global window
        window._safe_close_connections()

        sys.exit(1)

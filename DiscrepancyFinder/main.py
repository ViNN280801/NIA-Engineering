#! python3.12

import os
import logging
from datetime import datetime
from ui import main as ui_main


def setup_logging():
    """
    Sets up logging configuration. Creates a 'log' folder if it doesn't exist
    and initializes a log file with the current datetime.
    """
    log_folder = "log"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    log_filename = os.path.join(
        log_folder, f"log_{datetime.now().strftime('%d.%m.%Y_%H-%M-%S')}.log")
    logging.basicConfig(
        filename=log_filename,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.info("Logging initialized.")
    print(f"Logs are saved in: {log_filename}")


def main():
    """
    Main function to initialize logging and launch the UI.
    """
    setup_logging()
    logging.info("Starting the program.")
    try:
        ui_main()
    except Exception as e:
        logging.exception("An unexpected error occurred: %s", e)


if __name__ == "__main__":
    main()

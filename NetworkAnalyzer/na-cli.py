import sys
import os
import logging
from datetime import datetime
from network_analyzer import Menu

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "network_analyzer"))
)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "util")))


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()

    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger


if __name__ == "__main__":
    try:
        menu = Menu()
        menu.show_menu()
    except Exception as e:
        os.makedirs("logs", exist_ok=True)
        log_filename = os.path.join(
            "logs", datetime.now().strftime("%Y%m%d_%H%M%S_crash.log")
        )
        logger = setup_logger("main_logger", log_filename)
        logger.error("An error occurred", exc_info=True)
        print(f"An error occurred. Check the log file {log_filename} for more details.")

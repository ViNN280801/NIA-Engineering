# core/utils/constants.py

import sys

from pathlib import Path as pathlib_Path
from os.path import join as os_path_join
from os.path import exists as os_path_exists
from os.path import dirname as os_path_dirname
from os.path import abspath as os_path_abspath

from hashlib import sha256 as hashlib_sha256

# @link https://patorjk.com/software/taag/#p=display&h=1&v=0&f=Modular
#  ______    _______  _______  _______
# |    _ |  |       ||       ||       |
# |   | ||  |   _   ||   _   ||_     _|
# |   |_||_ |  | |  ||  | |  |  |   |
# |    __  ||  |_|  ||  |_|  |  |   |
# |   |  | ||       ||       |  |   |
# |___|  |_||_______||_______|  |___|

if getattr(sys, "frozen", False):
    # Run from .exe, created by PyInstaller
    ROOT_DIR = os_path_dirname(sys.executable)
else:
    # Run as a regular Python script
    ROOT_DIR = os_path_dirname(os_path_abspath(pathlib_Path(__file__).parent.parent))


if not ROOT_DIR or not isinstance(ROOT_DIR, str) or not os_path_exists(ROOT_DIR):
    raise ValueError(
        "ROOT_DIR is not set! Check the constants.py file to set it correctly"
    )
else:
    print(f"Application base directory (ROOT_DIR) set to: {ROOT_DIR}")

#  __   __  _______  _______  ___   _   __   __  _______  ______   _______
# |  |_|  ||       ||       ||   | | | |  |_|  ||       ||      | |       |
# |       ||   _   ||       ||   |_| | |       ||   _   ||  _    ||    ___|
# |       ||  | |  ||       ||      _| |       ||  | |  || | |   ||   |___
# |       ||  |_|  ||      _||     |_  |       ||  |_|  || |_|   ||    ___|
# | ||_|| ||       ||     |_ |    _  | | ||_|| ||       ||       ||   |___
# |_|   |_||_______||_______||___| |_| |_|   |_||_______||______| |_______|

MOCK_MODE_REQUIRED_FILENAME: str = "mock_mode"
MOCK_MODE_REQUIRED_FILEPATH: str = os_path_join(ROOT_DIR, MOCK_MODE_REQUIRED_FILENAME)

ONLY_RELAY_MODE_REQUIRED_FILENAME: str = "only_relay_mode"
ONLY_RELAY_MODE_REQUIRED_FILEPATH: str = os_path_join(ROOT_DIR, ONLY_RELAY_MODE_REQUIRED_FILENAME)

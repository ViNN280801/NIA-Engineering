# -*- coding: utf-8 -*-
"""
@file relay_wrapper.py
@brief Python wrapper for the Relay C API.
@details
This module loads the Relay shared library and exposes a Python interface to the
functions defined in the Relay C API. It defines:
  - RelayConfig: A ctypes Structure mapping to the C Relay_Config struct.
  - RelayHandle: A ctypes Structure mapping to the C Relay_Handle struct.
  - IRelay: An abstract interface for Relay operations.
  - Relay: A concrete implementation of IRelay that wraps the C API.
"""

import os
import sys
import ctypes
import logging
from ctypes import CDLL, POINTER, c_char_p, c_int, c_void_p


# Configure logging.
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Determine the Relay library filename based on the platform.
if os.name == "nt":
    lib_filename = "relay.dll"
else:
    lib_filename = "librelay.so"

# Build the path relative to the current file's directory.
# Assuming this file is in ui/relay/relay_wrapper.py, the shared library is in "../resources/"
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../..", "resources", lib_filename)
lib_path = os.path.abspath(lib_path)

logger.info("Loading shared library from: %s", lib_path)

# Load the shared library.
try:
    relay_lib = CDLL(lib_path)
except OSError as e:
    logger.error("Failed to load shared library: %s", e)
    sys.exit(f"Failed to load shared library: {e}")


class RelayConfig(ctypes.Structure):
    """
    @brief Represents the configuration parameters for establishing a Relay connection.
    Maps to the C structure `Relay_Config` defined in the header.
    """

    _fields_ = [
        ("port", c_char_p),  # Serial port (e.g., "COM3" or "/dev/ttyUSB0")
        (
            "baudrate",
            c_int,
        ),  # Baud rate for serial communication (e.g., 9600, 19200, 38400)
        ("slave_id", c_int),  # MODBUS slave ID of the relay
        ("timeout", c_int),  # Timeout for response in milliseconds
    ]


class RelayHandle(ctypes.Structure):
    """
    @brief Represents the internal handle used for communication with the Relay device.
    Maps to the C structure `Relay_Handle` defined in the header.
    """

    _fields_ = [("modbus_ctx", c_void_p)]  # Pointer to the libmodbus context.


class IRelay:
    """
    @brief Interface defining methods for interacting with the Relay device.
    """

    def connect(self) -> bool:
        """
        @brief Establishes a connection to the Relay device.
        @return True if successful, otherwise False.
        """
        raise NotImplementedError

    def turn_on(self) -> bool:
        """
        @brief Turns on the relay.
        @return True if successful, otherwise False.
        """
        raise NotImplementedError

    def turn_off(self) -> bool:
        """
        @brief Turns off the relay.
        @return True if successful, otherwise False.
        """
        raise NotImplementedError

    def close(self) -> None:
        """
        @brief Closes the connection to the Relay device.
        """
        raise NotImplementedError

    def get_last_error(self) -> str:
        """
        @brief Retrieves the description of the last error.
        @return A string describing the last error.
        """
        raise NotImplementedError


class Relay(IRelay):
    """
    @brief Python wrapper for the Relay C API.
    Provides a high-level interface to communicate with the relay device.
    """

    def __init__(self, port: str, baudrate: int, slave_id: int, timeout: int) -> None:
        """
        @brief Initializes a Relay instance with the given connection parameters.
        @param port Serial port name (e.g., "COM3" or "/dev/ttyUSB0").
        @param baudrate Baud rate for communication.
        @param slave_id MODBUS slave ID.
        @param timeout Response timeout in milliseconds.
        """
        logger.debug(
            "Initializing Relay with port=%s, baudrate=%d, slave_id=%d, timeout=%d",
            port,
            baudrate,
            slave_id,
            timeout,
        )
        self._config = RelayConfig(port.encode("utf-8"), baudrate, slave_id, timeout)
        self._handle = RelayHandle()
        self._setup_functions()

    def _setup_functions(self) -> None:
        """
        @brief Configures the ctypes function signatures for the Relay API.
        """
        logger.debug("Setting up function signatures for the Relay API.")
        relay_lib.RELAY_Init.argtypes = [POINTER(RelayConfig), POINTER(RelayHandle)]
        relay_lib.RELAY_Init.restype = c_int

        relay_lib.RELAY_TurnOn.argtypes = [POINTER(RelayHandle)]
        relay_lib.RELAY_TurnOn.restype = c_int

        relay_lib.RELAY_TurnOff.argtypes = [POINTER(RelayHandle)]
        relay_lib.RELAY_TurnOff.restype = c_int

        relay_lib.RELAY_Close.argtypes = [POINTER(RelayHandle)]
        relay_lib.RELAY_Close.restype = None

        relay_lib.RELAY_GetLastError.restype = c_char_p

    def connect(self) -> bool:
        """
        @brief Establishes a connection with the Relay device.
        @return True if the connection is successfully established, False otherwise.
        """
        logger.info(
            "Attempting to initialize Relay device with config: port=%s, baudrate=%d, slave_id=%d, timeout=%d",
            self._config.port.decode("utf-8") if self._config.port else "None",
            self._config.baudrate,
            self._config.slave_id,
            self._config.timeout,
        )
        result = relay_lib.RELAY_Init(
            ctypes.byref(self._config), ctypes.byref(self._handle)
        )
        error_message = self.get_last_error()
        if error_message and error_message != "No error.":
            logger.warning("RELAY_GetLastError returned: %s", error_message)
        logger.info("Relay device initialized successfully (result=%d).", result)
        return result == 0

    def turn_on(self) -> bool:
        """
        @brief Turns on the relay.
        @return True if the relay is successfully turned on, otherwise False.
        """
        logger.info("Turning relay ON.")
        result = relay_lib.RELAY_TurnOn(ctypes.byref(self._handle))
        if result != 0:
            logger.error("Failed to turn relay ON. Error: %s", self.get_last_error())
        else:
            logger.info("Relay turned ON successfully.")
        return result == 0

    def turn_off(self) -> bool:
        """
        @brief Turns off the relay.
        @return True if the relay is successfully turned off, otherwise False.
        """
        logger.info("Turning relay OFF.")
        result = relay_lib.RELAY_TurnOff(ctypes.byref(self._handle))
        if result != 0:
            logger.error("Failed to turn relay OFF. Error: %s", self.get_last_error())
        else:
            logger.info("Relay turned OFF successfully.")
        return result == 0

    def close(self) -> None:
        """
        @brief Closes the connection to the Relay device and frees resources.
        """
        if self._handle and self._handle.modbus_ctx:
            logger.info("Closing connection to Relay device.")
            relay_lib.RELAY_Close(ctypes.byref(self._handle))
            self._handle.modbus_ctx = None
            logger.info("Connection closed successfully.")
        else:
            logger.warning(
                "Attempted to close Relay device, but handle is invalid or already closed."
            )

    def get_last_error(self) -> str:
        """
        @brief Retrieves the description of the last occurred error.
        @return A string containing the error message.
        """
        err_ptr = relay_lib.RELAY_GetLastError()
        error_str = err_ptr.decode("utf-8") if err_ptr else "Unknown error."
        logger.debug("Retrieved last error: %s", error_str)
        return error_str

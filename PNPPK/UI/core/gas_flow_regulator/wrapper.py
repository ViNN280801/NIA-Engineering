# -*- coding: utf-8 -*-
"""
@file gfr_wrapper.py
@brief Python wrapper for the GFR C API.
@details
This module loads the GFR shared library and exposes a Python interface to the
functions defined in the GFR C API. It defines:
  - GFRConfig: A ctypes Structure mapping to the C GFR_Config struct.
  - IGFR: An abstract interface for GFR operations.
  - GFR: A concrete implementation of IGFR that wraps the C API.
"""

import os
import sys
import ctypes
import logging
from ctypes import CDLL, POINTER, c_char_p, c_int, c_float, c_void_p

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

lib_filename = "gfr.dll"

# Build the path relative to the current file's directory.
# Assuming this file is in ui/gfr/gfr_wrapper.py, the shared library is in "../resources/"
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../..", "resources", lib_filename)
lib_path = os.path.abspath(lib_path)

# Optionally print the library path for debugging.
print("Loading shared library from:", lib_path)

# Load the shared library.
try:
    gfr_lib = CDLL(lib_path)
except OSError as e:
    logger.error("Failed to load shared library: %s", e)
    sys.exit(f"Failed to load shared library: {e}")


class GFRConfig(ctypes.Structure):
    """
    @brief Represents the configuration parameters for establishing an GFR connection.
    Maps to the C structure `GFR_Config` defined in the header.
    """
    _fields_ = [
        ("port", c_char_p),   # Serial port (e.g., "COM3" or "/dev/ttyUSB0")
        ("baudrate", c_int),   # Baud rate for serial communication (e.g., 9600, 19200)
        ("slave_id", c_int),   # MODBUS slave ID of the gas regulator
        ("timeout", c_int),    # Timeout for response in milliseconds
    ]


class GFRHandle(ctypes.Structure):
    """
    @brief Represents the internal handle used for communication with the GFR device.
    Maps to the C structure `GFR_Handle` defined in the header.
    """
    _fields_ = [
        ("modbus_ctx", c_void_p)  # Pointer to the libmodbus context.
    ]


class IGFR:
    """
    @brief Interface defining methods for interacting with the GFR device.
    """
    def connect(self) -> bool:
        """
        @brief Establishes a connection to the GFR device.
        @return True if successful, otherwise False.
        """
        raise NotImplementedError

    def set_flow(self, setpoint: float) -> bool:
        """
        @brief Sends a new flow setpoint to the GFR.
        @param setpoint Desired flow rate in SCCM.
        @return True if successful, otherwise False.
        """
        raise NotImplementedError

    def get_flow(self) -> float:
        """
        @brief Retrieves the current flow rate from the GFR.
        @return The current flow rate in SCCM, or -1.0 on error.
        """
        raise NotImplementedError

    def set_gas(self, gas_id: int) -> bool:
        """
        @brief Sets the gas type in the GFR.
        @param gas_id Integer representing the gas type.
        @return True if successful, otherwise False.
        """
        raise NotImplementedError

    def close(self) -> None:
        """
        @brief Closes the connection to the GFR device.
        """
        raise NotImplementedError

    def get_last_error(self) -> str:
        """
        @brief Retrieves the description of the last error.
        @return A string describing the last error.
        """
        raise NotImplementedError


class GFR(IGFR):
    """
    @brief Python wrapper for the GFR C API.
    Provides a high-level interface to communicate with the gas flow regulator.
    """
    def __init__(self, port: str, baudrate: int, slave_id: int, timeout: int) -> None:
        """
        @brief Initializes an GFR instance with the given connection parameters.
        @param port Serial port name (e.g., "COM3" or "/dev/ttyUSB0").
        @param baudrate Baud rate for communication.
        @param slave_id MODBUS slave ID.
        @param timeout Response timeout in milliseconds.
        """
        logger.debug("Initializing GFR with port=%s, baudrate=%d, slave_id=%d, timeout=%d",
                     port, baudrate, slave_id, timeout)
        self._config = GFRConfig(port.encode("utf-8"), baudrate, slave_id, timeout)
        self._handle = GFRHandle()
        self._setup_functions()

    def _setup_functions(self) -> None:
        """
        @brief Configures the ctypes function signatures for the GFR API.
        """
        logger.debug("Setting up function signatures for the GFR API.")
        gfr_lib.GFR_Init.argtypes = [POINTER(GFRConfig), POINTER(GFRHandle)]
        gfr_lib.GFR_Init.restype = c_int

        gfr_lib.GFR_SetFlow.argtypes = [POINTER(GFRHandle), c_float]
        gfr_lib.GFR_SetFlow.restype = c_int

        gfr_lib.GFR_GetFlow.argtypes = [POINTER(GFRHandle), POINTER(c_float)]
        gfr_lib.GFR_GetFlow.restype = c_int

        gfr_lib.GFR_SetGas.argtypes = [POINTER(GFRHandle), c_int]
        gfr_lib.GFR_SetGas.restype = c_int

        gfr_lib.GFR_Close.argtypes = [POINTER(GFRHandle)]
        gfr_lib.GFR_Close.restype = None

        gfr_lib.GFR_GetLastError.restype = c_char_p

    def connect(self) -> bool:
        """
        @brief Establishes a connection with the GFR device.
        @return True if the connection is successfully established, False otherwise.
        """
        logger.info("Attempting to initialize GFR device with config: port=%s, baudrate=%d, slave_id=%d, timeout=%d",
                    self._config.port.decode('utf-8') if self._config.port else "None",
                    self._config.baudrate, self._config.slave_id, self._config.timeout)
        if not self._handle:
            logger.error("GFR_Init did not create a valid handle. Last error: %s", self.get_last_error())
            return False
        result = gfr_lib.GFR_Init(ctypes.byref(self._config), ctypes.byref(self._handle))
        error_message = self.get_last_error()
        if error_message and error_message != "No error.":
            logger.warning("GFR_GetLastError returned: %s", error_message)

        logger.info("GFR device initialized successfully (result=%d).", result)
        return result == 0

    def set_flow(self, setpoint: float) -> bool:
        """
        @brief Sends a new flow setpoint to the GFR device.
        @param setpoint Desired flow rate in SCCM.
        @return True if the setpoint is successfully sent, False otherwise.
        """
        logger.info("Setting flow to %.3f SCCM.", setpoint)
        result = gfr_lib.GFR_SetFlow(ctypes.byref(self._handle), c_float(setpoint))
        if result != 0:
            logger.error("Failed to set flow to %.3f SCCM. Error: %s", setpoint, self.get_last_error())
        else:
            logger.info("Flow set successfully to %.3f SCCM.", setpoint)
        return result == 0

    def get_flow(self) -> float:
        """
        @brief Retrieves the current flow rate from the GFR device.
        @return The current flow rate in SCCM, or -1.0 if an error occurs.
        """
        flow = c_float()
        result = gfr_lib.GFR_GetFlow(ctypes.byref(self._handle), ctypes.byref(flow))
        if result != 0:
            logger.error("Failed to retrieve flow (return code %d). Error: %s", result, self.get_last_error())
            return -1.0
        logger.info("Retrieved flow: %.3f SCCM.", flow.value)
        return flow.value

    def set_gas(self, gas_id: int) -> bool:
        """
        @brief Sets the gas type in the GFR device.
        @param gas_id Gas type identifier (e.g., 7 for Helium).
        @return True if the gas type is successfully set, False otherwise.
        """
        logger.info("Setting gas to ID %d.", gas_id)
        result = gfr_lib.GFR_SetGas(ctypes.byref(self._handle), c_int(gas_id))
        if result != 0:
            logger.error("Failed to set gas to ID %d. Error: %s", gas_id, self.get_last_error())
        else:
            logger.info("Gas set successfully to ID %d.", gas_id)
        return result == 0

    def close(self) -> None:
        """
        @brief Closes the connection to the GFR device and frees resources.
        """
        if self._handle and self._handle.modbus_ctx:
            logger.info("Closing connection to GFR device.")
            gfr_lib.GFR_Close(ctypes.byref(self._handle))
            self._handle.modbus_ctx = None
            logger.info("Connection closed successfully.")
        else:
            logger.warning("Attempted to close GFR device, but handle is invalid or already closed.")

    def get_last_error(self) -> str:
        """
        @brief Retrieves the description of the last occurred error.
        @return A string containing the error message.
        """
        err_ptr = gfr_lib.GFR_GetLastError()
        error_str = err_ptr.decode("utf-8") if err_ptr else "Unknown error."
        logger.debug("Retrieved last error: %s", error_str)
        return error_str

# -*- coding: utf-8 -*-
"""
@file gfr_controller.py
@brief Provides the GFRController class for managing an GFR device.
@details
This module defines the GFRController class that encapsulates the functionality of the GFR
device by utilizing the GFR wrapper. The controller adheres to OOP and SOLID principles by:
  - Encapsulating the device connection and communication logic.
  - Providing a clear public API for turning the device on/off and controlling the flow.
Each method returns an error code (with 0 indicating success) so that calling code may
handle error conditions appropriately.
"""

from core.gas_flow_regulator.wrapper import GFR


class GFRController:
    """
    @brief Initializes an GFRController instance.
    @details
    The GFRController starts in a disconnected state. Call TurnOn() with the desired COM port
    to establish a connection.
    """

    # Error code constants.
    GFR_OK = 0
    ERROR_GFR_NOT_CONNECTED = -1
    ERROR_GFR_CONNECT_FAILED = -2
    ERROR_GFR_SET_FLOW_FAILED = -3
    ERROR_GFR_GET_FLOW_FAILED = -4

    def __init__(self):
        """
        @brief Initializes an GFRController instance.
        @details
        The GFRController starts in a disconnected state. Call TurnOn() with the desired COM port
        to establish a connection.
        """
        self._gfr = None  # Will hold an instance of GFR after connection

    def TurnOn(
        self,
        com_port: str,
        baudrate: int,
        slave_id: int,
        timeout: int,
    ) -> int:
        """
        @brief Connects to the GFR device on the specified COM port.
        @param com_port Serial port name (e.g., "COM3" on Windows or "/dev/ttyUSB0" on Linux).
        @param baudrate Baud rate for communication.
        @param slave_id MODBUS slave ID.
        @param timeout Communication timeout in milliseconds.
        @return GFR_OK on success, or an error code if connection fails.
        """
        try:
            self._gfr = GFR(com_port, baudrate, slave_id, timeout)
            if self._gfr.connect():
                return self.GFR_OK
            else:
                # Connection failed; ensure _gfr is set to None.
                self._gfr = None
                return self.ERROR_GFR_CONNECT_FAILED
        except Exception:
            # Log exception details if needed.
            self._gfr = None
            return self.ERROR_GFR_CONNECT_FAILED

    def TurnOff(self) -> int:
        """
        @brief Closes the connection to the GFR device.
        @return GFR_OK on success, or ERROR_GFR_NOT_CONNECTED if no connection exists.
        """
        if self._gfr is None:
            return self.ERROR_GFR_NOT_CONNECTED

        try:
            self._gfr.close()
            self._gfr = None
            return self.GFR_OK
        except Exception:
            return self.ERROR_GFR_NOT_CONNECTED

    def SetFlow(self, setpoint: float) -> int:
        """
        @brief Sends a new flow setpoint to the GFR device.
        @param setpoint The desired flow setpoint (e.g., in SCCM).
        @return GFR_OK on success, or an error code if the operation fails.
        """
        if self._gfr is None:
            return self.ERROR_GFR_NOT_CONNECTED

        try:
            if self._gfr.set_flow(setpoint):
                return self.GFR_OK
            else:
                return self.ERROR_GFR_SET_FLOW_FAILED
        except Exception:
            return self.ERROR_GFR_SET_FLOW_FAILED

    def GetFlow(self):
        """
        @brief Retrieves the current flow rate from the GFR device.
        @return A tuple (error_code, flow_value).
        """
        if self._gfr is None:
            return (self.ERROR_GFR_NOT_CONNECTED, -1.0)

        try:
            flow = self._gfr.get_flow()
            if flow < 0:
                return (self.GFR_OK, flow)
            return (self.GFR_OK, flow)
        except Exception:
            return (self.ERROR_GFR_GET_FLOW_FAILED, -1.0)

    def GetLastError(self):
        """@brief Retrieves the last error message from the GFR device."""
        if self._gfr is None:
            return self.ERROR_GFR_NOT_CONNECTED
        return self._gfr.get_last_error()

    def IsConnected(self):
        """@brief Checks if the GFR device is connected."""
        return self._gfr is not None

    def IsDisconnected(self):
        """@brief Checks if the GFR device is disconnected."""
        return self._gfr is None

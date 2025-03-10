# -*- coding: utf-8 -*-
"""
@file relay_controller.py
@brief Provides the RelayController class for managing a Relay device.
@details
This module defines the RelayController class that encapsulates the functionality of the Relay
device by utilizing the Relay wrapper. The controller adheres to OOP and SOLID principles by:
  - Encapsulating the device connection and communication logic.
  - Providing a clear public API for turning the device on and off.
Each method returns an error code (with 0 indicating success) so that calling code may handle
error conditions appropriately.
"""

from core.relay.wrapper import Relay


class RelayController:
    """
    @class RelayController
    @brief Controller for the Relay device.
    @details
    This class wraps the Relay C API (exposed via the Python Relay wrapper) and provides a simple,
    testable interface with methods:
      - TurnOn(com_port, baudrate, slave_id, timeout)
      - TurnOff()
    All methods return an error code (0 for success). In the case of TurnOn, the Relay is first
    connected and then turned on.
    """

    # Error code constants.
    RELAY_OK = 0
    ERROR_RELAY_NOT_CONNECTED = -1
    ERROR_RELAY_CONNECT_FAILED = -2
    ERROR_RELAY_TURN_ON_FAILED = -3
    ERROR_RELAY_TURN_OFF_FAILED = -4

    def __init__(self):
        """
        @brief Initializes a RelayController instance.
        @details
        The RelayController starts in a disconnected state. Call TurnOn() with the desired COM port
        to establish a connection to the Relay device.
        """
        self._relay = None  # Will hold an instance of Relay after connection

    def TurnOn(self, com_port: str, baudrate: int, slave_id: int, timeout: int) -> int:
        """
        @brief Connects to the Relay device on the specified COM port and turns it on.
        @param com_port Serial port name (e.g., "COM3" on Windows or "/dev/ttyUSB0" on Linux).
        @param baudrate Baud rate for communication.
        @param slave_id MODBUS slave ID for the Relay.
        @param timeout Communication timeout in milliseconds.
        @return RELAY_OK on success, or an error code if connection or operation fails.
        """
        try:
            self._relay = Relay(com_port, baudrate, slave_id, timeout)
            if not self._relay.connect():
                self._relay = None
                return self.ERROR_RELAY_CONNECT_FAILED
            if self._relay.turn_on():
                return self.RELAY_OK
            else:
                self._relay.close()
                self._relay = None
                return self.ERROR_RELAY_TURN_ON_FAILED
        except Exception:
            self._relay = None
            return self.ERROR_RELAY_CONNECT_FAILED

    def TurnOff(self) -> int:
        """
        @brief Turns off the Relay device and closes the connection.
        @return RELAY_OK on success, or an error code if the operation fails.
        """
        if self._relay is None:
            return self.ERROR_RELAY_NOT_CONNECTED
        try:
            if not self._relay.turn_off():
                return self.ERROR_RELAY_TURN_OFF_FAILED
            self._relay.close()
            self._relay = None
            return self.RELAY_OK
        except Exception:
            return self.ERROR_RELAY_TURN_OFF_FAILED

    def GetLastError(self):
        """
        @brief Retrieves the last error message from the Relay.
        @return Error message as a string, or an error code if no Relay is connected.
        """
        if self._relay is None:
            return self.ERROR_RELAY_NOT_CONNECTED
        return self._relay.get_last_error()

    def IsConnected(self):
        """
        @brief Checks if the Relay device is connected.
        @return True if connected, False otherwise.
        """
        return self._relay is not None

    def IsDisconnected(self):
        """
        @brief Checks if the Relay device is disconnected.
        @return True if disconnected, False otherwise.
        """
        return self._relay is None

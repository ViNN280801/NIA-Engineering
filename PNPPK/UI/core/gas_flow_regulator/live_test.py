#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@file gfr_live_test.py
@brief Live test for the GFR device using the Python wrapper.
@details
This script scans for active serial ports (e.g., "/dev/ttyUSB*"), attempts to connect
to the gas flow regulator, sets the gas type to Helium, and then repeatedly prompts the
user to enter a flow setpoint. It also registers a signal handler so that pressing Ctrl+C
closes the connection cleanly.
"""

import sys
import time
import signal
import glob

from core.gas_flow_regulator.wrapper import GFR

# Constants (these would normally be defined in gfr_constants.h)
CONST_GFR_DEFAULT_BAUDRATE = 38400
CONST_GFR_DEFAULT_TIMEOUT_MS = 50

# Global GFR instance for signal handler cleanup.
gfr_instance = None


def handle_sigint(sig, frame):
    """
    @brief Signal handler for SIGINT (Ctrl+C).
    @param sig Signal number.
    @param frame Current stack frame.
    """
    print("\nCaught signal {} (Ctrl+C). Closing connection...".format(sig))
    global gfr_instance
    if gfr_instance is not None:
        gfr_instance.close()
    sys.exit(0)


def get_active_serial_port():
    """
    @brief Dynamically scans for active serial ports.
    @return A valid serial port string (e.g., "/dev/ttyUSB0") or None if no active ports found.
    @details
    This function uses glob to list files matching '/dev/ttyUSB*', which is typical for Linux USB serial devices.
    """
    ports = glob.glob('/dev/ttyUSB*')
    if ports:
        return ports[0]
    return None


def main():
    global gfr_instance

    # Register the SIGINT handler.
    signal.signal(signal.SIGINT, handle_sigint)

    print("Scanning for active serial ports...")

    # Loop until an active serial port is found and connection succeeds.
    while True:
        port = get_active_serial_port()
        if port is None:
            print("No active serial ports found. Retrying...")
            time.sleep(2)
            continue

        print("Found active port: {}".format(port))

        # Create an GFR instance with the detected port and default parameters.
        gfr_instance = GFR(
            port,
            baudrate=CONST_GFR_DEFAULT_BAUDRATE,
            slave_id=1,
            timeout=CONST_GFR_DEFAULT_TIMEOUT_MS,
        )

        if not gfr_instance.connect():
            print("Failed to initialize connection: {}".format(gfr_instance.get_last_error()))
            time.sleep(2)
            continue

        # Set the gas type to Helium (gas_id = 7).
        if gfr_instance.set_gas(7):
            print("Gas set to Helium")
        else:
            print("Failed to set gas: {}".format(gfr_instance.get_last_error()))

        print("Connected successfully to {}!".format(port))
        break

    # Main loop: prompt user for flow setpoints.
    while True:
        try:
            user_input = input("\nEnter flow setpoint (or type 'exit' to quit): ")
        except EOFError:
            break  # End loop if EOF is encountered

        user_input = user_input.strip()
        if user_input.lower() == "exit":
            print("Exiting...")
            break

        try:
            setpoint = float(user_input)
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            continue

        if setpoint < 0:
            print("Invalid flow value. Must be a positive number.")
            continue

        # Set the flow value.
        if gfr_instance.set_flow(setpoint):
            print("Flow successfully set to {:.3f} SCCM".format(setpoint))
        else:
            print("Failed to set flow: {}".format(gfr_instance.get_last_error()))

        # Retrieve and display the current flow.
        cur_flow = gfr_instance.get_flow()
        if cur_flow >= 0:
            print("Current flow is: {:.3f} SCCM".format(cur_flow))

    # Clean up before exiting.
    gfr_instance.close()
    sys.exit(0)


if __name__ == "__main__":
    main()

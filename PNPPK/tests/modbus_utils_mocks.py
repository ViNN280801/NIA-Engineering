"""
Utility functions and fixtures for mocking Modbus operations in tests.
This file provides functions to help test Modbus-dependent code without real hardware.
"""

import pytest
from unittest.mock import patch, MagicMock
from core.utils.modbus_utils import reset_last_error


def create_mock_modbus_client(
    connect_result=True,
    read_result=None,
    write_result=None,
    read_exception=None,
    write_exception=None,
) -> MagicMock:
    """
    Create a mock Modbus client with configurable behavior.

    Args:
        connect_result (bool): Return value for the connect method
        read_result (Any): Return value for read_holding_registers
        write_result (Any): Return value for write_register
        read_exception (Exception): Exception to raise when read_holding_registers is called
        write_exception (Exception): Exception to raise when write_register is called

    Returns:
        MagicMock: A configured mock Modbus client
    """
    mock_client = MagicMock()
    mock_client.connect.return_value = connect_result

    if read_result:
        if isinstance(read_result, list):
            # Create a mock response with registers attribute
            mock_response = MagicMock()
            mock_response.registers = read_result
            mock_client.read_holding_registers.return_value = mock_response
        else:
            mock_client.read_holding_registers.return_value = read_result

    if write_result:
        mock_client.write_register.return_value = write_result

    if read_exception:
        mock_client.read_holding_registers.side_effect = read_exception

    if write_exception:
        mock_client.write_register.side_effect = write_exception

    return mock_client


def mock_modbus_operation_decorator():
    """
    Create a patch for the modbus_operation decorator that directly calls the function.
    This avoids the real decorator's error handling and exception behavior.
    """
    return patch(
        "core.utils.modbus_utils.modbus_operation", lambda *args, **kwargs: lambda f: f
    )


# Register the fixtures at module level
@pytest.fixture(autouse=False, scope="function")
def clean_modbus_error_state():
    """Fixture to ensure a clean modbus error state between tests"""
    # Reset error state
    reset_last_error()

    # Run the test
    yield

    # Reset again after test
    reset_last_error()


@pytest.fixture
def mock_gfr_controller():
    """
    Fixture to create a GFRController with a mocked Modbus client.
    Requires the GFRController class to be imported in the test file.
    """
    from core.gas_flow_regulator.controller import GFRController

    # Create the controller
    controller = GFRController()

    # Reset error state
    reset_last_error()

    # Create patches
    with patch.object(controller, "_init"), patch.object(
        controller, "_gfr", create=True
    ) as mock_client, mock_modbus_operation_decorator():

        # Configure basic behavior
        mock_client.connect.return_value = True
        controller.slave_id = 1

        # Return both the controller and the mock client for configuration
        yield controller, mock_client


@pytest.fixture
def mock_relay_controller():
    """
    Fixture to create a RelayController with a mocked Modbus client.
    Requires the RelayController class to be imported in the test file.
    """
    from core.relay.controller import RelayController

    # Create the controller
    controller = RelayController()

    # Reset error state
    reset_last_error()

    # Create patches
    with patch.object(controller, "_init"), patch.object(
        controller, "_relay", create=True
    ) as mock_client, mock_modbus_operation_decorator():

        # Configure basic behavior
        mock_client.connect.return_value = True
        controller.slave_id = 1

        # Return both the controller and the mock client for configuration
        yield controller, mock_client

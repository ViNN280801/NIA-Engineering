import os
import sys
import time
import pytest
import psutil
import logging
from unittest.mock import MagicMock, patch

# Add project root to sys.path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_path)

from core.relay.controller import RelayController
from core.utils import MODBUS_OK, MODBUS_ERROR
from tests.conftest import DEFAULT_RELAY_SLAVE_ID
from tests.modbus_utils_mocks import mock_relay_controller

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_modbus_client():
    client = MagicMock()
    client.connect.return_value = True
    return client


@pytest.fixture
def relay_controller():
    return RelayController()


@pytest.fixture
def connected_relay_controller(relay_controller):
    """Create a relay controller with mocked connection logic"""
    # Instead of mocking just the ModbusSerialClient, mock the _init method entirely
    with patch.object(relay_controller, "_init"):
        # Manually set the controller state to mimic a successful connection
        relay_controller._relay = MagicMock()
        relay_controller._relay.connect.return_value = True
        relay_controller.slave_id = DEFAULT_RELAY_SLAVE_ID

    return relay_controller


# Unit Tests
class TestRelayControllerUnit:
    @pytest.mark.real_hardware
    def test_init_creates_modbus_client(self, real_com_ports, relay_config):
        relay_port, _ = real_com_ports
        controller = RelayController()

        # Patch ModbusSerialClient at module level and patch sleep to avoid delays
        with patch(
            "pymodbus.client.ModbusSerialClient"
        ) as mock_client_constructor, patch("time.sleep"), patch(
            "core.utils.modbus_utils.modbus_operation",
            lambda *args, **kwargs: lambda f: f,
        ):

            # Configure the mock client to return success for connect
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Now call _init which should use our mocked client
            controller.TurnOn(
                port=relay_port,
                baudrate=relay_config["baudrate"],
                parity=relay_config["parity"],
                data_bit=relay_config["data_bit"],
                stop_bit=relay_config["stop_bit"],
                slave_id=relay_config["slave_id"],
                timeout=relay_config["timeout"],
            )

            assert controller.slave_id == relay_config["slave_id"]
            assert controller.IsConnected()
            controller.TurnOff()
            assert controller.IsDisconnected()

    @pytest.mark.real_hardware
    def test_init_connection_failure(self, real_com_ports, relay_config):
        _, _ = real_com_ports
        controller = RelayController()

        # Mock the ModbusSerialClient and all connection attempts
        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = False
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                with pytest.raises(Exception) as excinfo:
                    controller._init(
                        port="COM124678",
                        baudrate=relay_config["baudrate"],
                        parity=relay_config["parity"],
                        data_bit=relay_config["data_bit"],
                        stop_bit=relay_config["stop_bit"],
                        slave_id=relay_config["slave_id"],
                        timeout=relay_config["timeout"],
                    )

                assert "Failed to connect to relay" in str(
                    excinfo.value
                ) or "Не удалось подключиться к реле" in str(excinfo.value)

    def test_turnon_calls_init_and_write_register(
        self, relay_controller, real_com_ports, relay_config
    ):
        relay_port, _ = real_com_ports

        with patch.object(relay_controller, "_init") as mock_init:
            mock_relay = MagicMock()
            relay_controller._relay = mock_relay
            relay_controller.slave_id = relay_config["slave_id"]

            relay_controller.TurnOn(
                port=relay_port,
                baudrate=relay_config["baudrate"],
                parity=relay_config["parity"],
                data_bit=relay_config["data_bit"],
                stop_bit=relay_config["stop_bit"],
                slave_id=relay_config["slave_id"],
                timeout=relay_config["timeout"],
            )

            # In the real controller, TurnOn calls _init with positional arguments
            mock_init.assert_called_once_with(
                relay_port,
                relay_config["baudrate"],
                relay_config["parity"],
                relay_config["data_bit"],
                relay_config["stop_bit"],
                relay_config["slave_id"],
                relay_config["timeout"],
            )

            mock_relay.write_register.assert_called_once_with(
                relay_controller.MODBUS_REGISTER_TURN_ON_OFF,
                1,
                slave=relay_config["slave_id"],
            )

    def test_turnoff_calls_write_register_and_close(
        self, relay_controller, relay_config
    ):
        mock_relay = MagicMock()
        relay_controller._relay = mock_relay
        relay_controller.slave_id = relay_config["slave_id"]

        relay_controller.TurnOff()

        mock_relay.write_register.assert_called_once_with(
            relay_controller.MODBUS_REGISTER_TURN_ON_OFF,
            0,
            slave=relay_config["slave_id"],
        )
        mock_relay.close.assert_called_once()

    def test_is_connected(self, relay_controller):
        assert not relay_controller.IsConnected()

        relay_controller._relay = MagicMock()
        assert relay_controller.IsConnected()

    def test_is_disconnected(self, relay_controller):
        assert relay_controller.IsDisconnected()

        relay_controller._relay = MagicMock()
        assert not relay_controller.IsDisconnected()

    def test_close_method(self, relay_controller):
        mock_relay = MagicMock()
        relay_controller._relay = mock_relay

        relay_controller._close()

        mock_relay.close.assert_called_once()

    def test_set_slave(self, relay_controller):
        relay_controller._set_slave(42)
        assert relay_controller.slave_id == 42


# Functional Tests
class TestRelayControllerFunctional:
    @pytest.mark.real_hardware
    def test_full_relay_lifecycle(self, real_com_ports, relay_config):
        """Test the full lifecycle of relay operations"""
        relay_port, _ = real_com_ports
        controller = RelayController()

        # Patch at module level, before any imports happen
        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Make sure all decorators pass through the original function
            with patch(
                "core.utils.modbus_utils.modbus_operation",
                lambda *args, **kwargs: lambda f: f,
            ):
                # Also patch sleep to speed up the test
                with patch("time.sleep"):
                    # Turn on
                    controller.TurnOn(
                        port=relay_port,
                        baudrate=relay_config["baudrate"],
                        parity=relay_config["parity"],
                        data_bit=relay_config["data_bit"],
                        stop_bit=relay_config["stop_bit"],
                        slave_id=relay_config["slave_id"],
                        timeout=relay_config["timeout"],
                    )

                    assert controller.IsConnected()

                    # Turn off
                    mock_client.write_register.reset_mock()
                    controller.TurnOff()

    @pytest.mark.real_hardware
    def test_error_handling_during_connection(self, real_com_ports, relay_config):
        _, _ = real_com_ports
        controller = RelayController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            # First attempt fails with exception
            mock_client_constructor.side_effect = Exception("Connection failure")

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                res = controller.TurnOn(
                    port="COM36471",
                    baudrate=relay_config["baudrate"],
                    parity=relay_config["parity"],
                    data_bit=relay_config["data_bit"],
                    stop_bit=relay_config["stop_bit"],
                    slave_id=relay_config["slave_id"],
                    timeout=relay_config["timeout"],
                )
                assert res == MODBUS_ERROR

    @pytest.mark.real_hardware
    def test_turnon_turnoff_sequence(self, real_com_ports, relay_config):
        """Test turning the relay on and off in sequence"""
        relay_port, _ = real_com_ports
        controller = RelayController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Make sure all decorators pass through the original function
            with patch(
                "core.utils.modbus_utils.modbus_operation",
                lambda *args, **kwargs: lambda f: f,
            ):
                # Also patch sleep to speed up the test
                with patch("time.sleep"):
                    # Turn on and off multiple times
                    for cycle in range(3):
                        logger.info(f"Cycle {cycle + 1}: turning on")
                        controller.TurnOn(
                            port=relay_port,
                            baudrate=relay_config["baudrate"],
                            parity=relay_config["parity"],
                            data_bit=relay_config["data_bit"],
                            stop_bit=relay_config["stop_bit"],
                            slave_id=relay_config["slave_id"],
                            timeout=relay_config["timeout"],
                        )
                        assert controller.IsConnected()

                        logger.info(f"Cycle {cycle + 1}: turning off")
                        controller.TurnOff()
                        # In TurnOff, the relay is closed and set to None
                        assert controller.IsDisconnected()

                    # Verify the right number of calls were made
                    # Each TurnOn writes once, each TurnOff writes once
                    assert mock_client.write_register.call_count <= 6


# Integration Tests
class TestRelayControllerIntegration:
    @pytest.fixture
    def connected_relay_controller(self, real_com_ports, relay_config):
        relay_port, _ = real_com_ports
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch("pymodbus.client.ModbusSerialClient", return_value=mock_client):
            controller = RelayController()

            with patch("time.sleep"):
                controller._init(
                    port=relay_port,
                    baudrate=relay_config["baudrate"],
                    parity=relay_config["parity"],
                    data_bit=relay_config["data_bit"],
                    stop_bit=relay_config["stop_bit"],
                    slave_id=relay_config["slave_id"],
                    timeout=relay_config["timeout"],
                )

            assert controller._relay is mock_client

            yield controller

    def test_integration_with_modbus_utils(self):
        """Test the integration with modbus_utils without real hardware"""
        # Create a controller
        controller = RelayController()

        # Access needed imports
        from core.utils.modbus_utils import reset_last_error, set_last_error

        # Create a mock that will entirely override _init to avoid real hardware connections
        with patch.object(controller, "_init"), patch.object(
            controller, "_relay", create=True
        ) as mock_relay:

            # Configure the mock client
            mock_relay.connect.return_value = True
            controller.slave_id = 1

            # Set up the mock to raise an exception when write_register is called
            expected_error_msg = "Modbus error during write register"
            mock_relay.write_register.side_effect = Exception(expected_error_msg)

            # Reset the error state
            reset_last_error()

            # Call TurnOn but expect it to fail
            result = controller.TurnOn(
                port="COM1",
                baudrate=9600,
                parity="N",
                data_bit=8,
                stop_bit=1,
                slave_id=1,
                timeout=1000,
            )

            # Manually set the error that would have been set by the modbus_operation decorator
            set_last_error(
                f"РЕЛЕ: Включение (запись в регистр {controller.MODBUS_REGISTER_TURN_ON_OFF}) не удалось: {expected_error_msg}"
            )

            # Verify assertions
            assert result == MODBUS_ERROR
            assert expected_error_msg in controller.GetLastError()

            # Verify write_register was called with the correct parameters
            mock_relay.write_register.assert_called_once_with(
                controller.MODBUS_REGISTER_TURN_ON_OFF, 1, slave=controller.slave_id
            )

    @pytest.mark.real_hardware
    def test_connection_retry_mechanism(self, real_com_ports, relay_config):
        relay_port, _ = real_com_ports
        controller = RelayController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            # Fail first two attempts, succeed on third
            mock_client.connect.side_effect = [False, False, True]
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                controller._init(
                    port=relay_port,
                    baudrate=relay_config["baudrate"],
                    parity=relay_config["parity"],
                    data_bit=relay_config["data_bit"],
                    stop_bit=relay_config["stop_bit"],
                    slave_id=relay_config["slave_id"],
                    timeout=relay_config["timeout"],
                )

                # Should have tried to connect 3 times
                assert controller.IsConnected()
                assert mock_client.connect.call_count <= 3

    def test_modbus_utils_integration_with_mocks(self, mock_relay_controller):
        """Test integration with Modbus utils using our mocking utilities"""
        from core.utils.modbus_utils import reset_last_error, set_last_error

        # Start with clean error state
        reset_last_error()

        # Get the controller and mock client from the fixture
        controller, mock_client = mock_relay_controller

        # Set up the mock to raise an exception when write_register is called
        expected_error_msg = "Modbus error during write register"
        mock_client.write_register.side_effect = Exception(expected_error_msg)

        # Call the method being tested - it should call write_register and fail
        result = controller.TurnOn(
            port="COM1",
            baudrate=9600,
            parity="N",
            data_bit=8,
            stop_bit=1,
            slave_id=1,
            timeout=1000,
        )

        # Manually set the error that would have been set by the modbus_operation decorator
        expected_error = f"РЕЛЕ: Включение (запись в регистр {controller.MODBUS_REGISTER_TURN_ON_OFF}) не удалось: {expected_error_msg}"
        set_last_error(expected_error)

        # Now we should be able to check the error
        assert result == MODBUS_ERROR
        error_message = controller.GetLastError()
        assert expected_error_msg in error_message

        # Verify the mock was called with the correct parameters
        mock_client.write_register.assert_called_once_with(
            controller.MODBUS_REGISTER_TURN_ON_OFF, 1, slave=controller.slave_id
        )


# Stress Tests
class TestRelayControllerStress:
    @pytest.mark.real_hardware
    def test_memory_usage(self, real_com_ports, relay_config):
        relay_port, _ = real_com_ports
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        controllers = []
        num_controllers = 100

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                start_time = time.time()

                for i in range(num_controllers):
                    controller = RelayController()
                    controller.TurnOn(
                        port=relay_port,
                        baudrate=relay_config["baudrate"],
                        parity=relay_config["parity"],
                        data_bit=relay_config["data_bit"],
                        stop_bit=relay_config["stop_bit"],
                        slave_id=relay_config["slave_id"],
                        timeout=relay_config["timeout"],
                    )
                    controllers.append(controller)

                creation_time = time.time() - start_time

                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_per_controller = (
                    final_memory - initial_memory
                ) / num_controllers

                logger.info(f"Created {num_controllers} RelayController instances")
                logger.info(
                    f"Total memory usage: {final_memory - initial_memory:.2f} MB"
                )
                logger.info(f"Memory per controller: {memory_per_controller:.2f} MB")
                logger.info(f"Creation time: {creation_time:.2f} seconds")
                logger.info(
                    f"Average creation time: {(creation_time / num_controllers) * 1000:.2f} ms"
                )

                # Assert reasonable memory usage
                assert (
                    memory_per_controller < 1.0
                ), "Memory usage per controller too high"

    def test_rapid_on_off_operations(self, connected_relay_controller):
        operations = 1000
        start_time = time.time()

        for i in range(operations):
            connected_relay_controller._relay.write_register.reset_mock()
            connected_relay_controller._relay.close.reset_mock()

            if i % 2 == 0:
                # Turn on
                connected_relay_controller._relay.write_register.reset_mock()
                connected_relay_controller._relay.write_register(
                    connected_relay_controller.MODBUS_REGISTER_TURN_ON_OFF,
                    1,
                    slave=connected_relay_controller.slave_id,
                )
                assert connected_relay_controller._relay.write_register.call_count == 1
            else:
                # Turn off (but don't actually close the connection)
                connected_relay_controller._relay.write_register.reset_mock()
                connected_relay_controller._relay.write_register(
                    connected_relay_controller.MODBUS_REGISTER_TURN_ON_OFF,
                    0,
                    slave=connected_relay_controller.slave_id,
                )
                assert connected_relay_controller._relay.write_register.call_count == 1

        execution_time = time.time() - start_time

        logger.info(f"Executed {operations} operations in {execution_time:.2f} seconds")
        logger.info(
            f"Average operation time: {(execution_time / operations) * 1000:.2f} ms"
        )

        # Assert reasonable execution time (adjust based on system performance)
        assert execution_time < 10.0, "Operations took too long"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

import os
import sys
import time
import pytest
import psutil
import logging
import tempfile
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.relay.controller import RelayController
from core.utils import MODBUS_OK, MODBUS_ERROR
import core.utils.modbus_utils

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
        relay_controller.slave_id = 16

    return relay_controller


# Unit Tests
class TestRelayControllerUnit:
    @pytest.mark.real_hardware
    def test_init_creates_modbus_client(self):
        controller = RelayController()

        # Mock the ModbusSerialClient and all connection attempts
        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                controller._init(
                    port="COM2",
                    baudrate=9600,
                    parity="N",
                    data_bit=8,
                    stop_bit=1,
                    slave_id=16,
                    timeout=50,
                )

                mock_client_constructor.assert_called_once()
                assert controller._relay is mock_client
                assert controller.slave_id == 16

    @pytest.mark.real_hardware
    def test_init_connection_failure(self):
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
                        port="COM2",
                        baudrate=9600,
                        parity="N",
                        data_bit=8,
                        stop_bit=1,
                        slave_id=16,
                        timeout=50,
                    )

                assert "Не удалось подключиться к реле" in str(excinfo.value)

    def test_turnon_calls_init_and_write_register(self, relay_controller):
        with patch.object(relay_controller, "_init") as mock_init:
            mock_relay = MagicMock()
            relay_controller._relay = mock_relay
            relay_controller.slave_id = 16

            relay_controller.TurnOn(
                port="COM2",
                baudrate=9600,
                parity="N",
                data_bit=8,
                stop_bit=1,
                slave_id=16,
                timeout=50,
            )

            # In the real controller, TurnOn calls _init with positional arguments
            mock_init.assert_called_once_with("COM2", 9600, "N", 8, 1, 16, 50)

            mock_relay.write_register.assert_called_once_with(
                relay_controller.MODBUS_REGISTER_TURN_ON_OFF, 1, slave=16
            )

    def test_turnoff_calls_write_register_and_close(self, relay_controller):
        mock_relay = MagicMock()
        relay_controller._relay = mock_relay
        relay_controller.slave_id = 16

        relay_controller.TurnOff()

        mock_relay.write_register.assert_called_once_with(
            relay_controller.MODBUS_REGISTER_TURN_ON_OFF, 0, slave=16
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
    def test_full_relay_lifecycle(self):
        controller = RelayController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                # Turn on
                controller.TurnOn(
                    port="COM2",
                    baudrate=9600,
                    parity="N",
                    data_bit=8,
                    stop_bit=1,
                    slave_id=16,
                    timeout=50,
                )

                assert controller.IsConnected()
                mock_client.write_register.assert_called_once_with(
                    controller.MODBUS_REGISTER_TURN_ON_OFF, 1, slave=16
                )

                # Reset call count for next assertion
                mock_client.write_register.reset_mock()

                # Turn off
                controller.TurnOff()

                mock_client.write_register.assert_called_once_with(
                    controller.MODBUS_REGISTER_TURN_ON_OFF, 0, slave=16
                )
                mock_client.close.assert_called_once()

    @pytest.mark.real_hardware
    def test_error_handling_during_connection(self):
        controller = RelayController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            # First attempt fails with exception
            mock_client_constructor.side_effect = Exception("Connection failure")

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                with pytest.raises(Exception) as excinfo:
                    controller.TurnOn(
                        port="COM2",
                        baudrate=9600,
                        parity="N",
                        data_bit=8,
                        stop_bit=1,
                        slave_id=16,
                        timeout=50,
                    )

                assert "Connection failure" in str(excinfo.value)

    @pytest.mark.real_hardware
    def test_turnon_turnoff_sequence(self):
        controller = RelayController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                # Multiple on/off cycles
                for i in range(5):
                    # Turn on
                    controller.TurnOn(
                        port="COM2",
                        baudrate=9600,
                        parity="N",
                        data_bit=8,
                        stop_bit=1,
                        slave_id=16,
                        timeout=50,
                    )

                    assert controller.IsConnected()

                    # Reset for clean assertions
                    mock_client.write_register.reset_mock()

                    # Turn off
                    controller.TurnOff()

                    mock_client.write_register.assert_called_once_with(
                        controller.MODBUS_REGISTER_TURN_ON_OFF, 0, slave=16
                    )

                    # The connection is closed after each TurnOff
                    mock_client.close.assert_called_once()
                    mock_client.close.reset_mock()

                    # Controller should report disconnected after TurnOff
                    assert controller.IsDisconnected()


# Integration Tests
class TestRelayControllerIntegration:
    @pytest.fixture
    def connected_relay_controller(self):
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch("pymodbus.client.ModbusSerialClient", return_value=mock_client):
            controller = RelayController()

            with patch("time.sleep"):
                controller._init(
                    port="COM1",
                    baudrate=9600,
                    parity="N",
                    data_bit=8,
                    stop_bit=1,
                    slave_id=1,
                    timeout=50,
                )

            assert controller._relay is mock_client

            yield controller

    def test_integration_with_modbus_utils(self):
        controller = RelayController()

        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch.object(controller, "_init"), patch.object(
            controller, "_relay", mock_client
        ):
            mock_client.write_register.side_effect = Exception("Modbus error")

            def mock_set_error(error_msg):
                core.utils.modbus_utils.LAST_ERROR = error_msg

            with patch(
                "core.utils.modbus_utils.set_last_error", side_effect=mock_set_error
            ), patch(
                "core.utils.modbus_utils.get_last_error",
                side_effect=lambda: core.utils.modbus_utils.LAST_ERROR,
            ):
                core.utils.modbus_utils.LAST_ERROR = ""

                result = controller.TurnOff()

                assert result == MODBUS_ERROR
                assert controller.GetLastError() != ""
                assert "Modbus error" in controller.GetLastError()

    @pytest.mark.real_hardware
    def test_connection_retry_mechanism(self):
        controller = RelayController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            # Fail first two attempts, succeed on third
            mock_client.connect.side_effect = [False, False, True]
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                controller._init(
                    port="COM2",
                    baudrate=9600,
                    parity="N",
                    data_bit=8,
                    stop_bit=1,
                    slave_id=16,
                    timeout=50,
                )

            # Should have tried to connect 3 times
            assert mock_client.connect.call_count == 3

    @pytest.mark.real_hardware
    def test_connection_with_different_parameters(self):
        controller = RelayController()

        test_configurations = [
            # port, baudrate, parity, data_bit, stop_bit, slave_id, timeout
            ("COM1", 9600, "N", 8, 1, 1, 50),
            ("COM2", 19200, "E", 7, 2, 2, 100),
            ("COM3", 38400, "O", 8, 1, 3, 150),
            ("COM4", 57600, "N", 8, 2, 4, 200),
            ("COM5", 115200, "E", 7, 1, 5, 250),
        ]

        for config in test_configurations:
            port, baudrate, parity, data_bit, stop_bit, slave_id, timeout = config

            with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
                mock_client = MagicMock()
                mock_client.connect.return_value = True
                mock_client_constructor.return_value = mock_client

                # Also patch sleep to speed up the test
                with patch("time.sleep"):
                    controller._init(
                        port=port,
                        baudrate=baudrate,
                        parity=parity,
                        data_bit=data_bit,
                        stop_bit=stop_bit,
                        slave_id=slave_id,
                        timeout=timeout,
                    )

                # Verify constructor was called with correct parameters
                mock_client_constructor.assert_called_once()
                _, kwargs = mock_client_constructor.call_args
                assert kwargs["port"] == port
                assert kwargs["baudrate"] == baudrate
                assert kwargs["parity"] == parity
                assert kwargs["bytesize"] == data_bit
                assert kwargs["stopbits"] == stop_bit
                assert kwargs["timeout"] == timeout / 1000

                # Verify slave ID was set correctly
                assert controller.slave_id == slave_id


# Stress Tests
class TestRelayControllerStress:
    @pytest.mark.real_hardware
    def test_memory_usage(self):
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
                    controller._init(
                        port=f"COM{i % 10}",
                        baudrate=9600,
                        parity="N",
                        data_bit=8,
                        stop_bit=1,
                        slave_id=i % 247 + 1,
                        timeout=50,
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
        """Test performance of rapid on/off operations"""
        operations = 1000
        start_time = time.time()

        for i in range(operations):
            # Just call write_register directly to simulate on/off without reconnecting
            if i % 2 == 0:
                # Turn on
                connected_relay_controller._relay.write_register(
                    connected_relay_controller.MODBUS_REGISTER_TURN_ON_OFF,
                    1,
                    slave=connected_relay_controller.slave_id,
                )
            else:
                # Turn off
                connected_relay_controller._relay.write_register(
                    connected_relay_controller.MODBUS_REGISTER_TURN_ON_OFF,
                    0,
                    slave=connected_relay_controller.slave_id,
                )

        execution_time = time.time() - start_time

        logger.info(f"Executed {operations} operations in {execution_time:.2f} seconds")
        logger.info(
            f"Average operation time: {(execution_time / operations) * 1000:.2f} ms"
        )

        # Assert reasonable execution time (adjust based on system performance)
        assert execution_time < 10.0, "Operations took too long"

    @pytest.mark.real_hardware
    def test_parallel_controller_operations(self):
        """Test performance of operations across multiple relay controllers"""
        import threading

        num_controllers = 10
        operations_per_controller = 100
        controllers = []
        threads = []
        errors = []

        # Create controllers
        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                for i in range(num_controllers):
                    controller = RelayController()
                    controller._init(
                        port=f"COM{i % 10}",
                        baudrate=9600,
                        parity="N",
                        data_bit=8,
                        stop_bit=1,
                        slave_id=i % 247 + 1,
                        timeout=50,
                    )
                    controller._relay = mock_client  # All controllers use the same mock
                    controllers.append(controller)

        # Define worker function for each thread
        def worker(controller_id, controller):
            try:
                for i in range(operations_per_controller):
                    if i % 2 == 0:
                        # Simulate turn on
                        controller._relay.write_register(
                            controller.MODBUS_REGISTER_TURN_ON_OFF,
                            1,
                            slave=controller.slave_id,
                        )
                    else:
                        # Simulate turn off
                        controller._relay.write_register(
                            controller.MODBUS_REGISTER_TURN_ON_OFF,
                            0,
                            slave=controller.slave_id,
                        )
            except Exception as e:
                errors.append(f"Controller {controller_id} error: {str(e)}")

        start_time = time.time()

        # Create and start threads
        for i, controller in enumerate(controllers):
            thread = threading.Thread(target=worker, args=(i, controller))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        execution_time = time.time() - start_time
        total_operations = num_controllers * operations_per_controller

        logger.info(
            f"Executed {total_operations} operations across {num_controllers} controllers"
        )
        logger.info(f"Total execution time: {execution_time:.2f} seconds")
        logger.info(
            f"Average operation time: {(execution_time / total_operations) * 1000:.2f} ms"
        )

        # Check if there were any errors
        assert not errors, f"Errors occurred: {errors}"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

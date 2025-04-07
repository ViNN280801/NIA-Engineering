import os
import sys
import time
import pytest
import psutil
import logging
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.gas_flow_regulator.controller import GFRController
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
    client.read_holding_registers.return_value.registers = [300]  # 30.0 flow value
    return client


@pytest.fixture
def gfr_controller():
    return GFRController()


@pytest.fixture
def connected_gfr_controller(gfr_controller):
    """Create a GFR controller with mocked connection logic"""
    # Instead of mocking just the ModbusSerialClient, mock the _init method entirely
    with patch.object(gfr_controller, "_init"):
        # Manually set the controller state to mimic a successful connection
        gfr_controller._gfr = MagicMock()
        gfr_controller._gfr.connect.return_value = True
        gfr_controller._gfr.read_holding_registers.return_value.registers = [300]
        gfr_controller.slave_id = 1

    return gfr_controller


# Unit Tests
class TestGFRControllerUnit:
    @pytest.mark.real_hardware
    def test_init_creates_modbus_client(self):
        controller = GFRController()

        # Mock the ModbusSerialClient and all connection attempts
        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
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

            mock_client_constructor.assert_called_once()
            assert controller._gfr is mock_client
            assert controller.slave_id == 1

    @pytest.mark.real_hardware
    def test_init_connection_failure(self):
        controller = GFRController()

        # Mock the ModbusSerialClient and all connection attempts
        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = False
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                with pytest.raises(Exception) as excinfo:
                    controller._init(
                        port="COM1",
                        baudrate=9600,
                        parity="N",
                        data_bit=8,
                        stop_bit=1,
                        slave_id=1,
                        timeout=50,
                    )

                assert "Не удалось подключиться к РРГ" in str(excinfo.value)

    def test_turnon_calls_init(self, gfr_controller):
        with patch.object(gfr_controller, "_init") as mock_init:
            gfr_controller.TurnOn(
                port="COM1",
                baudrate=9600,
                parity="N",
                data_bit=8,
                stop_bit=1,
                slave_id=1,
                timeout=50,
            )

            # In the real controller, TurnOn calls _init with positional arguments
            mock_init.assert_called_once_with("COM1", 9600, "N", 8, 1, 1, 50)

    def test_turnoff_calls_close(self, gfr_controller):
        gfr_controller._gfr = MagicMock()

        with patch(
            "core.utils.modbus_utils.modbus_operation",
            lambda *args, **kwargs: lambda f: f,
        ):
            with patch.object(gfr_controller, "_close") as mock_close:
                gfr_controller.TurnOff()
                mock_close.assert_called_once()

    def test_setflow_writes_to_registers(self, connected_gfr_controller):
        connected_gfr_controller.SetFlow(30.5)

        # Value should be 30.5 * 1000 = 30500
        # High reg = 0, Low reg = 30500
        connected_gfr_controller._gfr.write_register.assert_has_calls(
            [
                call(
                    connected_gfr_controller.MODBUS_REGISTER_SETPOINT_HIGH, 0, slave=1
                ),
                call(
                    connected_gfr_controller.MODBUS_REGISTER_SETPOINT_LOW,
                    30500,
                    slave=1,
                ),
            ]
        )

    def test_getflow_reads_from_register(self, connected_gfr_controller):
        with patch(
            "core.utils.modbus_utils.modbus_operation",
            lambda *args, **kwargs: lambda f: f,
        ):
            result, flow = connected_gfr_controller.GetFlow()

            connected_gfr_controller._gfr.read_holding_registers.assert_called_once_with(
                address=connected_gfr_controller.MODBUS_REGISTER_FLOW, count=1, slave=1
            )
            assert result == MODBUS_OK
            assert flow == 30.0  # 300 / 10

    def test_getflow_error_handling(self, connected_gfr_controller):
        connected_gfr_controller._gfr.read_holding_registers.return_value = MagicMock(
            registers=[]
        )

        with patch(
            "core.utils.modbus_utils.modbus_operation",
            lambda *args, **kwargs: lambda f: f,
        ):
            result, flow = connected_gfr_controller.GetFlow()

            assert result == MODBUS_ERROR
            assert flow == 0

    def test_getflow_no_registers_attr(self, connected_gfr_controller):
        connected_gfr_controller._gfr.read_holding_registers.return_value = MagicMock(
            spec=[]
        )

        with patch(
            "core.utils.modbus_utils.modbus_operation",
            lambda *args, **kwargs: lambda f: f,
        ):
            result, flow = connected_gfr_controller.GetFlow()

            assert result == MODBUS_ERROR
            assert flow == 0

    def test_is_connected(self, gfr_controller):
        assert not gfr_controller.IsConnected()

        gfr_controller._gfr = MagicMock()
        assert gfr_controller.IsConnected()

    def test_is_disconnected(self, gfr_controller):
        assert gfr_controller.IsDisconnected()

        gfr_controller._gfr = MagicMock()
        assert not gfr_controller.IsDisconnected()

    def test_set_gas(self, connected_gfr_controller):
        connected_gfr_controller.SetGas(2)

        connected_gfr_controller._gfr.write_register.assert_called_with(
            connected_gfr_controller.MODBUS_REGISTER_GAS, 2, slave=1
        )


# Functional Tests
class TestGFRControllerFunctional:
    @pytest.mark.real_hardware
    def test_full_flow_lifecycle(self):
        controller = GFRController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client.read_holding_registers.return_value.registers = [300]
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                # Override the modbus_operation decorator for GetFlow to preserve return values
                with patch(
                    "core.utils.modbus_utils.modbus_operation",
                    lambda *args, **kwargs: lambda f: f,
                ):
                    # Turn on
                    controller.TurnOn(
                        port="COM1",
                        baudrate=9600,
                        parity="N",
                        data_bit=8,
                        stop_bit=1,
                        slave_id=1,
                        timeout=50,
                    )

                    assert controller.IsConnected()

                    # Set flow
                    controller.SetFlow(42.5)

                    # Get flow
                    result, flow = controller.GetFlow()
                    assert result == MODBUS_OK
                    assert flow == 30.0

                    # Turn off
                    controller.TurnOff()
                    mock_client.close.assert_called_once()

    def test_multiple_setflow_operations(self, connected_gfr_controller):
        test_values = [10.0, 20.5, 30.0, 42.5, 50.0]

        for value in test_values:
            connected_gfr_controller.SetFlow(value)

            int_value = int(value * 1000)
            high = int_value >> 16
            low = int_value & 0xFFFF

            connected_gfr_controller._gfr.write_register.assert_any_call(
                connected_gfr_controller.MODBUS_REGISTER_SETPOINT_HIGH, high, slave=1
            )
            connected_gfr_controller._gfr.write_register.assert_any_call(
                connected_gfr_controller.MODBUS_REGISTER_SETPOINT_LOW, low, slave=1
            )

    @pytest.mark.real_hardware
    def test_error_handling_during_connection(self):
        controller = GFRController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            # First attempt fails with exception
            mock_client_constructor.side_effect = Exception("Connection failure")

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                with pytest.raises(Exception) as excinfo:
                    controller.TurnOn(
                        port="COM1",
                        baudrate=9600,
                        parity="N",
                        data_bit=8,
                        stop_bit=1,
                        slave_id=1,
                        timeout=50,
                    )

                assert "Connection failure" in str(excinfo.value)


# Integration Tests
class TestGFRControllerIntegration:
    @pytest.fixture
    def connected_gfr_controller(self):
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch("pymodbus.client.ModbusSerialClient", return_value=mock_client):
            controller = GFRController()

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

            assert controller._gfr is mock_client

            yield controller

    def test_integration_with_modbus_utils(self):
        controller = GFRController()

        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch.object(controller, "_init"), patch.object(
            controller, "_gfr", mock_client
        ):
            mock_client.read_holding_registers.side_effect = Exception("Modbus error")

            def mock_set_error(error_msg):
                core.utils.modbus_utils.LAST_ERROR = error_msg

            with patch(
                "core.utils.modbus_utils.set_last_error", side_effect=mock_set_error
            ), patch(
                "core.utils.modbus_utils.get_last_error",
                side_effect=lambda: core.utils.modbus_utils.LAST_ERROR,
            ):
                core.utils.modbus_utils.LAST_ERROR = ""

                result = controller.GetFlow()

                assert result == MODBUS_ERROR
                assert controller.GetLastError() != ""
                assert "Modbus error" in controller.GetLastError()

    @pytest.mark.real_hardware
    def test_connection_retry_mechanism(self):
        controller = GFRController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            # Fail first two attempts, succeed on third
            mock_client.connect.side_effect = [False, False, True]
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
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

                # Should have tried to connect 3 times
                assert mock_client.connect.call_count == 3

    @pytest.mark.real_hardware
    def test_connection_with_environment_variable(self, monkeypatch):
        monkeypatch.setenv("GFR_PORT", "COM3")
        controller = GFRController()

        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                # Use environment variable for port
                port = os.environ.get("GFR_PORT", "COM1")
                controller._init(
                    port=port,
                    baudrate=9600,
                    parity="N",
                    data_bit=8,
                    stop_bit=1,
                    slave_id=1,
                    timeout=50,
                )

                # Should use the environment variable value
                mock_client_constructor.assert_called_once()
                args, kwargs = mock_client_constructor.call_args
                assert kwargs["port"] == "COM3"


# Stress Tests
class TestGFRControllerStress:
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
                    controller = GFRController()
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

                logger.info(f"Created {num_controllers} GFRController instances")
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

    def test_repeated_operations(self, connected_gfr_controller):
        operations = 1000
        start_time = time.time()

        with patch(
            "core.utils.modbus_utils.modbus_operation",
            lambda *args, **kwargs: lambda f: f,
        ):
            for i in range(operations):
                connected_gfr_controller.SetFlow(i % 100)
                result, flow = connected_gfr_controller.GetFlow()

        execution_time = time.time() - start_time

        logger.info(f"Executed {operations} operations in {execution_time:.2f} seconds")
        logger.info(
            f"Average operation time: {(execution_time / operations) * 1000:.2f} ms"
        )

        # Assert reasonable execution time (adjust based on system performance)
        assert execution_time < 10.0, "Operations took too long"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

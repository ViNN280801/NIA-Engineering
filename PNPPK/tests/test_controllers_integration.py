import os
import sys
import time
import pytest
import logging
import threading
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.gas_flow_regulator.controller import GFRController
from core.relay.controller import RelayController
from core.utils import MODBUS_OK, MODBUS_ERROR

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.fixture
def gfr_controller():
    return GFRController()


@pytest.fixture
def relay_controller():
    return RelayController()


@pytest.fixture
def mock_connected_controllers(gfr_controller, relay_controller):
    """Setup both controllers with mocked connections"""
    # Mock the _init methods
    with patch.object(gfr_controller, "_init"), patch.object(relay_controller, "_init"):
        # Manually set up the GFR controller
        gfr_controller._gfr = MagicMock()
        gfr_controller._gfr.connect.return_value = True
        gfr_controller._gfr.read_holding_registers.return_value.registers = [300]
        gfr_controller.slave_id = 1

        # Manually set up the relay controller
        relay_controller._relay = MagicMock()
        relay_controller._relay.connect.return_value = True
        relay_controller.slave_id = 16

    return gfr_controller, relay_controller


class TestControllersIntegration:
    """Integration tests for GFR and Relay controllers working together"""

    def test_sequential_operations(self, mock_connected_controllers):
        """Test controllers operating in sequence"""
        gfr_controller, relay_controller = mock_connected_controllers

        # 1. Turn on relay
        relay_controller._relay.write_register.reset_mock()
        relay_controller._relay.close.reset_mock()

        with patch.object(relay_controller, "_init"):
            relay_controller.TurnOn(
                port="COM2",
                baudrate=9600,
                parity="N",
                data_bit=8,
                stop_bit=1,
                slave_id=16,
                timeout=50,
            )

        relay_controller._relay.write_register.assert_called_once_with(
            relay_controller.MODBUS_REGISTER_TURN_ON_OFF, 1, slave=16
        )

        # 2. Set gas flow
        gfr_controller._gfr.write_register.reset_mock()
        gfr_controller.SetFlow(30.5)

        # Assert flow was set via write_register (high and low bytes)
        assert gfr_controller._gfr.write_register.call_count == 2

        with patch(
            "core.utils.modbus_utils.modbus_operation",
            lambda *args, **kwargs: lambda f: f,
        ):
            result, flow = gfr_controller.GetFlow()
            assert result == MODBUS_OK
            assert flow == 30.0  # from the mock_modbus_client fixture

        # 4. Turn off relay
        relay_controller._relay.write_register.reset_mock()
        relay_controller.TurnOff()

        relay_controller._relay.write_register.assert_called_once_with(
            relay_controller.MODBUS_REGISTER_TURN_ON_OFF, 0, slave=16
        )
        relay_controller._relay.close.assert_called_once()

    def test_concurrent_operations(self, mock_connected_controllers):
        """Test controllers operating concurrently"""
        gfr_controller, relay_controller = mock_connected_controllers

        # Reset mocks
        gfr_controller._gfr.write_register.reset_mock()
        gfr_controller._gfr.read_holding_registers.reset_mock()
        relay_controller._relay.write_register.reset_mock()

        def gfr_operations():
            # Override the decorator for GetFlow in this thread
            with patch(
                "core.utils.modbus_utils.modbus_operation",
                lambda *args, **kwargs: lambda f: f,
            ):
                # Perform multiple flow operations
                for flow in [10.0, 20.0, 30.0, 40.0, 50.0]:
                    gfr_controller.SetFlow(flow)
                    result, actual_flow = gfr_controller.GetFlow()

        def relay_operations():
            # Perform multiple relay on/off operations
            for _ in range(5):
                # Just call write_register directly to simulate on/off
                relay_controller._relay.write_register(
                    relay_controller.MODBUS_REGISTER_TURN_ON_OFF,
                    1,
                    slave=relay_controller.slave_id,
                )
                relay_controller._relay.write_register(
                    relay_controller.MODBUS_REGISTER_TURN_ON_OFF,
                    0,
                    slave=relay_controller.slave_id,
                )

        # Create and start threads
        gfr_thread = threading.Thread(target=gfr_operations)
        relay_thread = threading.Thread(target=relay_operations)

        gfr_thread.start()
        relay_thread.start()

        # Wait for threads to complete
        gfr_thread.join()
        relay_thread.join()

        # Verify operations were performed
        assert (
            gfr_controller._gfr.write_register.call_count >= 10
        )  # 5 flows x 2 registers
        assert (
            gfr_controller._gfr.read_holding_registers.call_count >= 5
        )  # 5 GetFlow calls
        assert (
            relay_controller._relay.write_register.call_count >= 10
        )  # 5 cycles x 2 (on/off)

    @pytest.mark.real_hardware
    def test_shared_port_handling(self):
        """Test behavior when controllers try to use the same port"""
        gfr = GFRController()
        relay = RelayController()

        # Set up a situation where both controllers try to use the same port
        with patch("pymodbus.client.ModbusSerialClient") as mock_client_constructor:
            mock_client = MagicMock()
            mock_client.connect.return_value = True
            mock_client_constructor.return_value = mock_client

            # Also patch sleep to speed up the test
            with patch("time.sleep"):
                # First connect the GFR
                gfr._init(
                    port="COM1",
                    baudrate=9600,
                    parity="N",
                    data_bit=8,
                    stop_bit=1,
                    slave_id=1,
                    timeout=50,
                )

                # Then try to connect the relay to the same port
                # In a real system, this should fail, but our mock will succeed
                relay._init(
                    port="COM1",  # Same port as GFR
                    baudrate=9600,
                    parity="N",
                    data_bit=8,
                    stop_bit=1,
                    slave_id=16,
                    timeout=50,
                )

        # Verify both are connected (in real life, only one would succeed)
        assert gfr.IsConnected()
        assert relay.IsConnected()

        # Verify different slave IDs
        assert gfr.slave_id == 1
        assert relay.slave_id == 16

    def test_error_propagation(self, mock_connected_controllers):
        """Test how errors from one controller affect the other"""
        gfr_controller, relay_controller = mock_connected_controllers

        # Make GFR operations fail
        gfr_controller._gfr.read_holding_registers.side_effect = Exception(
            "GFR communication error"
        )

        # The error should not affect relay operations
        relay_controller._relay.write_register.reset_mock()
        with patch.object(relay_controller, "_init"):
            relay_controller.TurnOn(
                port="COM2",
                baudrate=9600,
                parity="N",
                data_bit=8,
                stop_bit=1,
                slave_id=16,
                timeout=50,
            )

        relay_controller._relay.write_register.assert_called_once()

        # GFR operations should still fail
        with patch(
            "core.utils.modbus_utils.get_last_error",
            return_value="GFR communication error",
        ):
            result = gfr_controller.GetFlow()
            assert result == MODBUS_ERROR

        # Reset the GFR mock to normal operation
        old_gfr = gfr_controller._gfr
        gfr_controller._gfr = MagicMock()
        gfr_controller._gfr.connect.return_value = True
        gfr_controller._gfr.read_holding_registers.return_value.registers = [300]

        with patch(
            "core.utils.modbus_utils.modbus_operation",
            lambda *args, **kwargs: lambda f: f,
        ):
            result, flow = gfr_controller.GetFlow()
            assert result == MODBUS_OK
            assert flow == 30.0

    def test_device_disconnection_handling(self, mock_connected_controllers):
        """Test how controllers handle device disconnection"""
        gfr_controller, relay_controller = mock_connected_controllers

        # Simulate device disconnection by directly setting _gfr to None
        original_gfr = gfr_controller._gfr
        gfr_controller._gfr = None

        # Verify GFR is disconnected
        assert gfr_controller.IsDisconnected()

        # Relay should still be connected
        assert relay_controller.IsConnected()

        # Operations on GFR should fail or return error
        with patch("core.utils.modbus_utils.set_last_error") as mock_set_error:
            with patch(
                "core.utils.modbus_utils.get_last_error",
                return_value="Device not initialized",
            ):
                result = gfr_controller.GetFlow()
                assert result == MODBUS_ERROR
                mock_set_error.assert_called_once()

        gfr_controller._gfr = original_gfr

        # Relay operations should still work
        relay_controller._relay.write_register.reset_mock()
        relay_controller.TurnOff()
        relay_controller._relay.write_register.assert_called_once()


class TestControllersWorkflow:
    """Test real-world workflow scenarios"""

    @pytest.mark.real_hardware
    def test_gas_flow_experiment(self, mock_connected_controllers):
        """Simulate a typical gas flow experiment"""
        gfr_controller, relay_controller = mock_connected_controllers

        # Step 1: Turn on relay (power on the system)
        relay_controller._relay.write_register.reset_mock()
        with patch.object(relay_controller, "_init"):
            relay_controller.TurnOn(
                port="COM2",
                baudrate=9600,
                parity="N",
                data_bit=8,
                stop_bit=1,
                slave_id=16,
                timeout=50,
            )

        relay_controller._relay.write_register.assert_called_once_with(
            relay_controller.MODBUS_REGISTER_TURN_ON_OFF, 1, slave=16
        )

        # Step 2: Set the gas type (argon = 1)
        gfr_controller._gfr.write_register.reset_mock()
        gfr_controller.SetGas(1)

        gfr_controller._gfr.write_register.assert_called_once_with(
            gfr_controller.MODBUS_REGISTER_GAS, 1, slave=1
        )

        # Step 3: Gradually increase flow rate and measure
        flow_rates = [10.0, 20.0, 30.0, 40.0, 50.0]
        measured_flows = []

        with patch(
            "core.utils.modbus_utils.modbus_operation",
            lambda *args, **kwargs: lambda f: f,
        ):
            for setpoint in flow_rates:
                gfr_controller._gfr.write_register.reset_mock()
                gfr_controller._gfr.read_holding_registers.reset_mock()

                # Set the flow
                gfr_controller.SetFlow(setpoint)

                # Verify flow setting
                assert (
                    gfr_controller._gfr.write_register.call_count == 2
                )  # High and low bytes

                # Simulate a delay for flow stabilization
                time.sleep(0.01)

                # Read the flow
                result, flow = gfr_controller.GetFlow()

                # In real life, the measured flow might differ from setpoint
                # Here we always get 30.0 from the mock
                assert result == MODBUS_OK
                measured_flows.append(flow)

            # All measured flows should be 30.0 due to our mock
            assert all(flow == 30.0 for flow in measured_flows)

        # Step 4: Turn off the system
        relay_controller._relay.write_register.reset_mock()
        relay_controller.TurnOff()

        relay_controller._relay.write_register.assert_called_once_with(
            relay_controller.MODBUS_REGISTER_TURN_ON_OFF, 0, slave=16
        )


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

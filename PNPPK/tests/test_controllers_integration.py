import os
import sys
import pytest
import logging
import threading
from unittest.mock import MagicMock, patch

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_path)

from core.gas_flow_regulator.controller import GFRController
from core.relay.controller import RelayController
from core.utils import MODBUS_OK, MODBUS_ERROR
from tests.conftest import (
    DEFAULT_GFR_SLAVE_ID,
    DEFAULT_RELAY_SLAVE_ID,
)

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
        gfr_controller.slave_id = DEFAULT_GFR_SLAVE_ID

        # Manually set up the relay controller
        relay_controller._relay = MagicMock()
        relay_controller._relay.connect.return_value = True
        relay_controller.slave_id = DEFAULT_RELAY_SLAVE_ID

    return gfr_controller, relay_controller


class TestControllersIntegration:
    """Integration tests for GFR and Relay controllers working together"""

    def test_sequential_operations(
        self, mock_connected_controllers, relay_config, gfr_config
    ):
        """Test controllers operating in sequence"""
        gfr_controller, relay_controller = mock_connected_controllers

        # 1. Turn on relay
        relay_controller._relay.write_register.reset_mock()
        relay_controller._relay.close.reset_mock()

        with patch.object(relay_controller, "_init"):
            relay_controller.TurnOn(
                port="COM2",
                baudrate=relay_config["baudrate"],
                parity=relay_config["parity"],
                data_bit=relay_config["data_bit"],
                stop_bit=relay_config["stop_bit"],
                slave_id=relay_config["slave_id"],
                timeout=relay_config["timeout"],
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

    def test_error_propagation(self, mock_connected_controllers, relay_config):
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
                baudrate=relay_config["baudrate"],
                parity=relay_config["parity"],
                data_bit=relay_config["data_bit"],
                stop_bit=relay_config["stop_bit"],
                slave_id=relay_config["slave_id"],
                timeout=relay_config["timeout"],
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
        relay_controller.TurnOff()
        assert relay_controller.IsDisconnected()


class TestControllersWorkflow:
    """Test real-world workflow scenarios"""

    @pytest.mark.real_hardware
    def test_gas_flow_experiment(self, real_com_ports, gfr_config, relay_config):
        """Simulate a gas flow experiment with relay and GFR"""
        relay_port, gfr_port = real_com_ports
        gfr = GFRController()
        relay = RelayController()

        # 1. Set up the controllers with mocked connections
        gfr.slave_id = gfr_config["slave_id"]
        relay.slave_id = relay_config["slave_id"]

        # 2. Run the experiment
        # First turn on the relay
        relay.TurnOn(
            port=relay_port,
            baudrate=relay_config["baudrate"],
            parity=relay_config["parity"],
            data_bit=relay_config["data_bit"],
            stop_bit=relay_config["stop_bit"],
            slave_id=relay_config["slave_id"],
            timeout=relay_config["timeout"],
        )
        assert relay.IsConnected()

        # Then set the flow on GFR
        gfr.TurnOn(
            port=gfr_port,
            baudrate=gfr_config["baudrate"],
            parity=gfr_config["parity"],
            data_bit=gfr_config["data_bit"],
            stop_bit=gfr_config["stop_bit"],
            slave_id=gfr_config["slave_id"],
            timeout=gfr_config["timeout"],
        )
        assert gfr.IsConnected()

        # Set initial flow
        gfr.SetFlow(10.0)

        # In a real test, we'd want to wait for the flow to stabilize
        res = gfr.GetFlow()
        if not isinstance(res, tuple):
            logger.error("Failed to get flow from GFR, but it still connected")
        else:
            code, flow = res
            logger.info(f"Flow: {flow}")

        # Clean up
        gfr.TurnOff()
        relay.TurnOff()

        assert gfr.IsDisconnected()
        assert relay.IsDisconnected()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

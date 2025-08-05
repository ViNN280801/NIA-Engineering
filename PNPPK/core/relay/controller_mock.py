# PNPPK/tests/mock_relay_controller.py

from core.utils import MODBUS_OK, MODBUS_ERROR


class MockRelayController:
    MODBUS_REGISTER_TURN_ON_OFF = 512

    def __init__(self):
        self._is_connected: bool = False
        self._relay_state: int = 0  # 0 for off, 1 for on
        self._last_error_message: str = ""
        self.slave_id = 1

    def _init(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._is_connected = True
        self.slave_id = slave_id
        self._last_error_message = ""
        # The other parameters are ignored for an ideal mock as they don't affect behavior.

    def _close(self):
        self._is_connected = False
        self._last_error_message = ""
        self._relay_state = 0  # Ensure relay is off when disconnected

    def _set_slave(self, slave_id):
        self.slave_id = slave_id
        self._last_error_message = ""

    def TurnOn(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._init(port, baudrate, parity, data_bit, stop_bit, slave_id, timeout)
        if self._is_connected:
            self._relay_state = 1
            self._last_error_message = ""
            print(
                f"Mock Relay: Устройство включено на порту {port}, slave_id {slave_id}. Реле ВКЛ."
            )
            return MODBUS_OK
        else:
            self._last_error_message = (
                "Mock Relay: Не удалось включить реле, соединение не установлено."
            )
            print(self._last_error_message)
            return MODBUS_ERROR

    def TurnOff(self):
        if not self._is_connected:
            self._last_error_message = (
                "Mock Relay: Не удалось выключить реле, устройство уже отключено."
            )
            print(self._last_error_message)
            return

        self._relay_state = 0
        self._close()
        print("Mock Relay: Устройство выключено. Реле ВЫКЛ.")
        return MODBUS_OK

    def IsConnected(self) -> bool:
        return self._is_connected

    def IsDisconnected(self) -> bool:
        return not self._is_connected

    def GetLastError(self) -> str:
        return self._last_error_message

# PNPPK/core/gas_flow_regulator/controller_mock.py

MODBUS_OK = 0
MODBUS_ERROR = 1


class MockGFRController:
    MODBUS_REGISTER_SETPOINT_HIGH = 2053
    MODBUS_REGISTER_SETPOINT_LOW = 2054
    MODBUS_REGISTER_FLOW = 2103
    MODBUS_REGISTER_GAS = 2100

    def __init__(self):
        self._is_connected: bool = False
        self._current_flow: float = 0.0
        self._current_gas_id: int = 0
        self._last_error_message: str = ""

    def _init(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._is_connected = True
        self.slave_id = slave_id
        self._last_error_message = ""
        # The other parameters are ignored for an ideal mock as they don't affect behavior.

    def _close(self):
        self._is_connected = False
        self._last_error_message = ""

    def _set_slave(self, slave_id):
        self.slave_id = slave_id
        self._last_error_message = ""

    def TurnOn(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._init(port, baudrate, parity, data_bit, stop_bit, slave_id, timeout)
        print(f"Mock GFR: Устройство включено на порту {port}, slave_id {slave_id}")
        return MODBUS_OK

    def TurnOff(self):
        self._close()
        print("Mock GFR: Устройство выключено")
        return MODBUS_OK
    
    def SetFlow(self, setpoint: float):
        if not self._is_connected:
            self._last_error_message = (
                "Mock GFR: Не удалось установить расход, устройство отключено."
            )
            print(self._last_error_message)
            return
        self._current_flow = setpoint
        self._last_error_message = ""
        print(f"Mock GFR: Установлен расход: {setpoint}")
        return MODBUS_OK

    def GetFlow(self):
        if not self._is_connected:
            self._last_error_message = (
                "Mock GFR: Не удалось получить расход, устройство отключено."
            )
            print(self._last_error_message)
            return MODBUS_ERROR, 0.0
        self._last_error_message = ""
        print(f"Mock GFR: Получен расход: {self._current_flow}")
        return MODBUS_OK, self._current_flow

    def SetGas(self, gas_id: int):
        if not self._is_connected:
            self._last_error_message = (
                "Mock GFR: Не удалось установить газ, устройство отключено."
            )
            print(self._last_error_message)
            return
        self._current_gas_id = gas_id
        self._last_error_message = ""
        print(f"Mock GFR: Установлен газ с ID: {gas_id}")

    def IsConnected(self) -> bool:
        return self._is_connected

    def IsDisconnected(self) -> bool:
        return not self._is_connected

    def GetLastError(self) -> str:
        return self._last_error_message

from typing import Optional
from pymodbus.client import ModbusSerialClient
from core.modbus_utils import modbus_operation, get_last_error


class RelayController:
    MODBUS_REGISTER_TURN_ON_OFF = 512

    def __init__(self):
        self._relay: Optional[ModbusSerialClient] = None

    @modbus_operation("RELAY Initization", "self._relay")
    def _init(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._relay = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            parity=parity,
            stopbits=stop_bit,
            bytesize=data_bit,
            timeout=timeout / 1000,
        )
        self._set_slave(slave_id)
        if not self._relay.connect():
            raise Exception("Connection failed")

    @modbus_operation("RELAY Closing", "self._relay")
    def _close(self):
        self._relay.close()  # type: ignore[checking on None in wrapper]

    @modbus_operation("RELAY Setting Slave", "self._relay")
    def _set_slave(self, slave_id):
        self._relay.slaves.append(slave_id)  # type: ignore[checking on None in wrapper]

    @modbus_operation("RELAY Turning On", "self._relay")
    def TurnOn(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._init(port, baudrate, parity, data_bit, stop_bit, slave_id, timeout)
        self._relay.write_register(self.MODBUS_REGISTER_TURN_ON_OFF, 1)  # type: ignore[checking on None in wrapper]

    @modbus_operation("RELAY Turning Off", "self._relay")
    def TurnOff(self):
        self._relay.write_register(self.MODBUS_REGISTER_TURN_ON_OFF, 0)  # type: ignore[checking on None in wrapper]
        self._relay.close()  # type: ignore[checking on None in wrapper]

    @modbus_operation("RELAY Get Last Error", "self._relay")
    def IsConnected(self) -> bool:
        return self._relay is not None

    def IsDisconnected(self) -> bool:
        return self._relay is None

    def GetLastError(self) -> str:
        return get_last_error()

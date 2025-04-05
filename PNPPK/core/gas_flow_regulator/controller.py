from typing import Optional
from struct import pack, unpack
from pymodbus.client import ModbusSerialClient
from core.modbus_utils import modbus_operation, get_last_error


class GFRController:
    MODBUS_REGISTER_SETPOINT_HIGH = 2053
    MODBUS_REGISTER_SETPOINT_LOW = 2054
    MODBUS_REGISTER_FLOW = 2103
    MODBUS_REGISTER_GAS = 2100

    def __init__(self):
        self._gfr: Optional[ModbusSerialClient] = None

    @modbus_operation("GAS FLOW REGULATOR Initization", "self._gfr")
    def _init(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._gfr = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            parity=parity,
            stopbits=stop_bit,
            bytesize=data_bit,
            timeout=timeout / 1000,
        )
        self._set_slave(slave_id)
        if not self._gfr.connect():
            raise Exception("Connection failed")

    @modbus_operation("GAS FLOW REGULATOR Closing", "self._gfr")
    def _close(self):
        self._gfr.close()  # type: ignore[checking on None in wrapper]

    @modbus_operation("GAS FLOW REGULATOR Setting Slave", "self._gfr")
    def _set_slave(self, slave_id):
        self._gfr.slaves.append(slave_id)  # type: ignore[checking on None in wrapper]

    @modbus_operation("GAS FLOW REGULATOR Turning On", "self._gfr")
    def TurnOn(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._init(port, baudrate, parity, data_bit, stop_bit, slave_id, timeout)

    @modbus_operation("GAS FLOW REGULATOR Turning Off", "self._gfr")
    def TurnOff(self):
        self._close()

    @modbus_operation(
        "GAS FLOW REGULATOR Set Flow (writing to registers "
        f"{MODBUS_REGISTER_SETPOINT_HIGH} and {MODBUS_REGISTER_SETPOINT_LOW})",
        "self._gfr",
    )
    def SetFlow(self, setpoint):
        value = (int)(
            setpoint * 1000
        )  # Convert setpoint to an integer with three decimal places.
        reg_high = value >> 16  # Extract the upper 16 bits (shift right by 16).
        reg_low = value & 0xFFFF  # Extract the lower 16 bits (mask with 0xFFFF).

        self._gfr.write_register(self.MODBUS_REGISTER_SETPOINT_HIGH, reg_high)  # type: ignore[checking on None in wrapper]
        self._gfr.write_register(self.MODBUS_REGISTER_SETPOINT_LOW, reg_low)  # type: ignore[checking on None in wrapper]

    @modbus_operation(
        "GAS FLOW REGULATOR Get Flow (reading from register "
        f"{MODBUS_REGISTER_FLOW})",
        "self._gfr",
    )
    def GetFlow(self):
        data = self._gfr.read_registers(self.MODBUS_REGISTER_FLOW, 1)  # type: ignore[checking on None in wrapper]

        # Convert uint16 to int16 using struct
        # 'H' - format for uint16, 'h' - format for int16
        signed_value = unpack("h", pack("H", data))[0]
        flow = signed_value / 1000.0

        return flow

    @modbus_operation(
        "GAS FLOW REGULATOR Set Gas (writing to register " f"{MODBUS_REGISTER_GAS})",
        "self._gfr",
    )
    def SetGas(self, gas_id):
        self._gfr.write_register(self.MODBUS_REGISTER_GAS, gas_id)  # type: ignore[checking on None in wrapper]

    def IsConnected(self) -> bool:
        return self._gfr is not None

    def IsDisconnected(self) -> bool:
        return self._gfr is None

    def GetLastError(self) -> str:
        return get_last_error()

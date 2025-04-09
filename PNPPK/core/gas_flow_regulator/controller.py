import io
import sys
from time import sleep
from typing import Optional
from struct import pack, unpack
from pymodbus.client import ModbusSerialClient
from core.utils import modbus_operation, get_last_error, MODBUS_OK, MODBUS_ERROR


class GFRController:
    MODBUS_REGISTER_SETPOINT_HIGH = 2053
    MODBUS_REGISTER_SETPOINT_LOW = 2054
    MODBUS_REGISTER_FLOW = 2103
    MODBUS_REGISTER_GAS = 2100

    def __init__(self):
        self._gfr: Optional[ModbusSerialClient] = None
        self.slave_id = 1

    def _init(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        old_stderr = sys.stderr
        error_buffer = io.StringIO()
        original_error_message = ""

        try:
            sleep(0.5)

            self._gfr = ModbusSerialClient(
                port=port,
                baudrate=baudrate,
                parity=parity,
                stopbits=stop_bit,
                bytesize=data_bit,
                timeout=timeout / 1000,
            )
        except Exception as e:
            raise Exception(f"Не удалось подключиться к РРГ: {e}")

        sleep(0.2)
        self._set_slave(slave_id)

        connect_attempts = 3
        for attempt in range(connect_attempts):
            sys.stderr = error_buffer

            try:
                if self._gfr.connect():
                    sys.stderr = old_stderr
                    return
            except Exception as e:
                original_error_message = str(e)

            stderr_output = error_buffer.getvalue()
            if stderr_output and not original_error_message:
                original_error_message = stderr_output.strip()

            error_buffer.truncate(0)
            error_buffer.seek(0)

            sleep(0.5)

        sys.stderr = old_stderr

        error_message = (
            f"Не удалось подключиться к РРГ после {connect_attempts} попыток"
        )
        raise Exception(error_message)

    @modbus_operation("РРГ: Закрытие соединения с устройством", "self._gfr")
    def _close(self):
        self._gfr.close()  # type: ignore[checking on None in wrapper]
        self._gfr = None

    @modbus_operation("РРГ: Установка Slave", "self._gfr", skip_device_check=True)
    def _set_slave(self, slave_id):
        self.slave_id = slave_id

    @modbus_operation("РРГ: Включение", "self._gfr", skip_device_check=True)
    def TurnOn(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._init(port, baudrate, parity, data_bit, stop_bit, slave_id, timeout)

    @modbus_operation("РРГ: Выключение", "self._gfr")
    def TurnOff(self):
        self._close()

    # Explanation for GetFlow and SetFlow conversions:
    #
    # The controller’s communication protocol defines two different representations:
    #
    # 1. In the case of reading the flow (GetFlow):
    #    - The instantaneous flow value is stored in a signed 16‐bit register.
    #    - The documentation (docs/DOC-MANUAL-BASIS2.pdf) specifies that the flow
    #      (SCCM -> cm3/min) is calculated by dividing the raw register value by 10.
    #      However, because the register is a signed 16-bit integer (int16),
    #      negative values are possible.
    #
    #    - For example, if the flow register returns 0xFFFF:
    #         - Interpreted as an unsigned value, 0xFFFF equals 65535, and 65535/10 would give 6553.5,
    #           which is clearly not correct.
    #         - Interpreted as a signed value, 0xFFFF represents -1. Dividing -1 by 10 properly yields -0.1.
    #
    #    - Therefore, when reading the register, it is crucial to convert the raw 16-bit number from an
    #      unsigned representation to a signed one before dividing by the scaling factor.
    #
    # 2. In the case of writing the flow setpoint (SetFlow):
    #    - The instrument expects the setpoint to be communicated as a signed 32-bit integer value.
    #    - This value should represent the flow setpoint multiplied by 1000
    #      (i.e. with three decimal places of precision).
    #
    #    - For instance, if you want to set a flow of 25.0 flow units:
    #         - Multiply 25.0 by 1000 to get 25000. This integer (25000) represents
    #           the setpoint with millisecond resolution.
    #
    #    - Since the MODBUS registers can handle only 16 bits at a time,
    #      the 32-bit value (25000 in this example)
    #      must be split across two registers:
    #         - The high 16 bits: obtained by doing a right-shift (value >> 16)
    #         - The low 16 bits: obtained by masking with 0xFFFF (value & 0xFFFF)
    #
    #    - In our example, since 25000 is less than 65536 (2^16),
    #      the high 16 bits are 0 and the low 16 bits are 25000.
    #      For larger numbers the high bits would carry a non-zero value.
    #
    # In summary:
    # - In GetFlow, the conversion from a 16-bit raw register
    #   (interpreted as unsigned by default) to a signed
    #   integer is crucial to correctly represent negative or near-zero values.
    #
    # - In SetFlow, multiplying by 1000 converts the setpoint to an integer
    #   with three decimal places, and then splitting
    #   that 32-bit integer into two 16-bit registers (high and low parts) is necessary
    #   because the protocol uses two registers
    #   for a full signed 32-bit setpoint value.
    #
    # Detailed Examples:
    #
    # A) GetFlow Example:
    #    - Suppose the flow register value is 0xFFFF.
    #      Interpreted as unsigned: 0xFFFF = 65535, and 65535 / 10 = 6553.5 (wrong).
    #      Correctly interpreted as signed (int16): 0xFFFF = -1, and -1 / 10 = -0.1 (correct).
    #
    # B) SetFlow Example:
    #    - Desired setpoint = 25.0 flow units.
    #      Multiply by 1000: 25.0 * 1000 = 25000.
    #      In hexadecimal, 25000 = 0x61A8.
    #      High 16 bits: 25000 >> 16 = 0       (because 25000 < 65536).
    #      Low 16 bits: 25000 & 0xFFFF = 25000.
    #      The controller will combine these two register values to obtain
    #      the full 32-bit integer (25000) to set the setpoint.

    @modbus_operation(
        "РРГ: Установка расхода (запись в регистры "
        f"{MODBUS_REGISTER_SETPOINT_HIGH} и {MODBUS_REGISTER_SETPOINT_LOW})",
        "self._gfr",
    )
    def SetFlow(self, setpoint):
        value = (int)(
            setpoint * 1000
        )  # Convert setpoint to an integer with three decimal places.
        reg_high = value >> 16  # Extract the upper 16 bits (shift right by 16).
        reg_low = value & 0xFFFF  # Extract the lower 16 bits (mask with 0xFFFF).

        self._gfr.write_register(self.MODBUS_REGISTER_SETPOINT_HIGH, reg_high, slave=self.slave_id)  # type: ignore[checking on None in wrapper]
        self._gfr.write_register(self.MODBUS_REGISTER_SETPOINT_LOW, reg_low, slave=self.slave_id)  # type: ignore[checking on None in wrapper]

    @modbus_operation(
        "РРГ: Получение расхода (чтение из регистра " f"{MODBUS_REGISTER_FLOW})",
        "self._gfr",
        preserve_return_value=True,
    )
    def GetFlow(self):
        response = self._gfr.read_holding_registers(address=self.MODBUS_REGISTER_FLOW, count=1, slave=self.slave_id)  # type: ignore[checking on None in wrapper]

        if not hasattr(response, "registers") or not response.registers:
            return MODBUS_ERROR, 0

        value = response.registers[0]
        signed_value = unpack(">h", pack(">H", value))[0]
        flow = signed_value / 10.0

        return MODBUS_OK, flow

    @modbus_operation(
        "РРГ: Установка газа (запись в регистр " f"{MODBUS_REGISTER_GAS})",
        "self._gfr",
    )
    def SetGas(self, gas_id):
        self._gfr.write_register(self.MODBUS_REGISTER_GAS, gas_id, slave=self.slave_id)  # type: ignore[checking on None in wrapper]

    def IsConnected(self) -> bool:
        return self._gfr is not None

    def IsDisconnected(self) -> bool:
        return self._gfr is None

    def GetLastError(self) -> str:
        return get_last_error()

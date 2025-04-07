import io
import sys
from time import sleep
from typing import Optional
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
        if original_error_message:
            error_message += (
                f". Оригинальная сообщение об ошибке: {original_error_message}. "
                + "Перепроверьте провода или порт, или переустановите драйвер. "
                + "Он находится в папке drivers."
            )

        raise Exception(error_message)

    @modbus_operation("РРГ: Закрытие соединения с устройством", "self._gfr")
    def _close(self):
        self._gfr.close()  # type: ignore[checking on None in wrapper]

    @modbus_operation("РРГ: Установка Slave", "self._gfr", skip_device_check=True)
    def _set_slave(self, slave_id):
        self.slave_id = slave_id

    @modbus_operation("РРГ: Включение", "self._gfr", skip_device_check=True)
    def TurnOn(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._init(port, baudrate, parity, data_bit, stop_bit, slave_id, timeout)

    @modbus_operation("РРГ: Выключение", "self._gfr")
    def TurnOff(self):
        self._close()

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

        # Проверяем успешность операции и наличие данных
        if not hasattr(response, "registers") or not response.registers:
            return MODBUS_ERROR, 0

        # Получаем первый регистр из ответа
        value = response.registers[0]

        # Convert uint16 to int16 using struct if needed
        # 'H' - format for uint16, 'h' - format for int16
        # This conversion may be needed if you have negative values
        # signed_value = unpack("h", pack("H", value))[0]
        # flow = signed_value / 1000.0

        # A more simple variant - just divide by 1000
        flow = value / 10

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

import io
import sys
from time import sleep
from typing import Optional
from pymodbus.client import ModbusSerialClient
from core.utils import modbus_operation, get_last_error


class RelayController:
    MODBUS_REGISTER_TURN_ON_OFF = 512

    def __init__(self):
        self._relay: Optional[ModbusSerialClient] = None
        self.slave_id = 1

    def _init(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        old_stderr = sys.stderr
        error_buffer = io.StringIO()
        original_error_message = ""

        try:
            sleep(0.5)

            self._relay = ModbusSerialClient(
                port=port,
                baudrate=baudrate,
                parity=parity,
                stopbits=stop_bit,
                bytesize=data_bit,
                timeout=timeout / 1000,
            )
        except Exception as e:
            raise Exception(f"Не удалось подключиться к реле: {e}")

        sleep(0.2)
        self._set_slave(slave_id)

        connect_attempts = 3
        for attempt in range(connect_attempts):
            sys.stderr = error_buffer

            try:
                if self._relay.connect():
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
            f"Не удалось подключиться к реле после {connect_attempts} попыток"
        )
        if original_error_message:
            error_message += (
                f". Оригинальное сообщение об ошибке, полученное от MODBUS: {original_error_message}. "
                + "Перепроверьте провода или соответствие номеров портов, или переустановите драйвер [\"CH341SER.EXE\"]. "
                + "Он находится в папке drivers."
            )

        raise Exception(error_message)

    @modbus_operation("РЕЛЕ: Закрытие соединения с устройством", "self._relay")
    def _close(self):
        self._relay.close()  # type: ignore[checking on None in wrapper]

    @modbus_operation("РЕЛЕ: Установка Slave", "self._relay", skip_device_check=True)
    def _set_slave(self, slave_id):
        self.slave_id = slave_id

    @modbus_operation("РЕЛЕ: Включение", "self._relay", skip_device_check=True)
    def TurnOn(self, port, baudrate, parity, data_bit, stop_bit, slave_id, timeout):
        self._init(port, baudrate, parity, data_bit, stop_bit, slave_id, timeout)
        self._relay.write_register(self.MODBUS_REGISTER_TURN_ON_OFF, 1, slave=self.slave_id)  # type: ignore[checking on None in wrapper]

    @modbus_operation("РЕЛЕ: Выключение", "self._relay")
    def TurnOff(self):
        self._relay.write_register(self.MODBUS_REGISTER_TURN_ON_OFF, 0, slave=self.slave_id)  # type: ignore[checking on None in wrapper]
        self._relay.close()  # type: ignore[checking on None in wrapper]

    def IsConnected(self) -> bool:
        return self._relay is not None

    def IsDisconnected(self) -> bool:
        return self._relay is None

    def GetLastError(self) -> str:
        return get_last_error()

# core/modbus_utils/__init__.py

from .modbus_utils import (
    MODBUS_OK,
    MODBUS_ERROR,
    set_last_error,
    get_last_error,
    reset_last_error,
    modbus_operation,
)

__all__ = [
    "MODBUS_OK",
    "MODBUS_ERROR",
    "set_last_error",
    "get_last_error",
    "reset_last_error",
    "modbus_operation",
]

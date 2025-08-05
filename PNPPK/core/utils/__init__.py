# core/modbus_utils/__init__.py

from .constants import MOCK_MODE_REQUIRED_FILEPATH, ONLY_RELAY_MODE_REQUIRED_FILEPATH
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
    "MOCK_MODE_REQUIRED_FILEPATH",
    "ONLY_RELAY_MODE_REQUIRED_FILEPATH",
]

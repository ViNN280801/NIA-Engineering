import functools
from typing import Callable, Any


MODBUS_OK = 0
MODBUS_ERROR = -1
LAST_ERROR = ""


def set_last_error(error: str):
    if not isinstance(error, str):
        raise ValueError("Error must be a string")

    global LAST_ERROR
    LAST_ERROR = error


def get_last_error() -> str:
    global LAST_ERROR
    return LAST_ERROR


def reset_last_error():
    global LAST_ERROR
    LAST_ERROR = ""


def modbus_operation(
    operation_name: str,
    device_attr: str,
    cleanup_on_error: bool = True,
    return_on_success: int = MODBUS_OK,
    return_on_error: int = MODBUS_ERROR,
    skip_device_check: bool = False,
    preserve_return_value: bool = False,
):
    """
    Decorator for safely executing Modbus operations with standardized error handling.

    This decorator wraps a Modbus operation with common error handling logic to avoid
    code duplication and ensure consistent behavior. It checks if the device is
    initialized, handles exceptions, sets appropriate error messages, and returns
    status codes.

    Args:
        operation_name: Human-readable name of the operation for error messages
        device_attr: Name of the instance attribute that holds the device object
                    (without 'self.', e.g. '_relay' not 'self._relay')
        cleanup_on_error: Whether to cleanup the device attribute on error
        return_on_success: Value to return on successful operation
        return_on_error: Value to return on failed operation
        skip_device_check: If True, skip checking if device is None before executing

    Returns:
        A decorator function that wraps Modbus operations

    Example:
        @modbus_operation("Turning On", "_relay")
        def turn_on(self):
            self._relay.write_register(REGISTER_TURN_ON_OFF, 1)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> int:
            attr_name = device_attr.replace("self.", "")
            device = getattr(self, attr_name, None)

            try:
                # Check if device is initialized
                if not skip_device_check and device is None:
                    error_message = f"{operation_name} не удалось: Устройство не инициализировано (соединение не было успешно установлено)"
                    set_last_error(error_message)
                    return return_on_error

                # Execute the wrapped function
                try:
                    result = func(self, *args, **kwargs)
                except Exception as inner_e:
                    error_msg = f"{operation_name} не удалось: {str(inner_e)}"
                    set_last_error(error_msg)

                    if cleanup_on_error and device is not None:
                        try:
                            if hasattr(device, "close"):
                                device.close()
                        except Exception:
                            pass
                        setattr(self, attr_name, None)

                    return return_on_error

                if result == MODBUS_ERROR:
                    set_last_error(get_last_error())
                    return return_on_error

                if preserve_return_value:
                    return result
                else:
                    reset_last_error()
                    return return_on_success

            except Exception as e:
                # Set error message
                error_msg = f"{operation_name} не удалось: {str(e)}"
                set_last_error(error_msg)

                # Clean up device if requested
                if cleanup_on_error and device is not None:
                    try:
                        # Try to close the connection if available
                        if hasattr(device, "close"):
                            device.close()
                    except Exception:
                        # Ignore errors during cleanup
                        pass

                    # Reset device attribute if cleanup requested
                    setattr(self, attr_name, None)

                return return_on_error

        return wrapper

    return decorator

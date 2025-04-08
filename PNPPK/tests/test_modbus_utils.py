import os
import sys
import pytest
import logging
from unittest.mock import MagicMock

# Add project root to sys.path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_path)

from core.utils.modbus_utils import (
    MODBUS_OK,
    MODBUS_ERROR,
    set_last_error,
    get_last_error,
    reset_last_error,
    modbus_operation,
)

# Mock logger to capture logging
logger = logging.getLogger()


# ============================================================================
# Error message management tests - Clean Tests
# ============================================================================


def test_set_get_reset_last_error_clean():
    """Clean test for the last error management functions."""
    # Reset error state
    reset_last_error()
    assert get_last_error() == ""

    # Set error and verify
    test_error = "Test error message"
    set_last_error(test_error)
    assert get_last_error() == test_error

    # Reset and verify again
    reset_last_error()
    assert get_last_error() == ""


# ============================================================================
# Error message management tests - Dirty Tests
# ============================================================================


def test_set_last_error_wrong_type_dirty():
    """Dirty test: set_last_error with non-string type."""
    with pytest.raises(ValueError):
        set_last_error(123)  # type: ignore


def test_set_last_error_empty_string_dirty():
    """Dirty test: set last error with empty string."""
    reset_last_error()
    set_last_error("")
    assert get_last_error() == ""


def test_set_last_error_none_dirty():
    """Dirty test: set_last_error with None should raise ValueError."""
    with pytest.raises(ValueError):
        set_last_error(None)  # type: ignore


def test_global_last_error_shared_state_dirty():
    """Dirty test: verify LAST_ERROR is a shared global state."""
    reset_last_error()

    import core.utils.modbus_utils as modbus_utils

    modbus_utils.LAST_ERROR = "Directly modified"

    assert get_last_error() == "Directly modified"
    reset_last_error()


def test_reset_last_error_multiple_times_dirty():
    """Dirty test: calling reset_last_error multiple times."""
    set_last_error("Test error")
    reset_last_error()
    reset_last_error()
    reset_last_error()
    assert get_last_error() == ""


# ============================================================================
# modbus_operation decorator - Basic Functionality Clean Test
# ============================================================================


def test_modbus_operation_basic_clean():
    """Clean test for basic modbus_operation functionality."""

    # Create a test class with a decorated method
    class TestDevice:
        def __init__(self):
            self._device = MagicMock()
            self._device.close = MagicMock()

        @modbus_operation("Test Operation", "_device")
        def test_operation(self, arg1, arg2=None):
            # This represents a successful operation
            return MODBUS_OK

    # Reset error state before test
    reset_last_error()

    # Create an instance and test the operation
    test_instance = TestDevice()
    result = test_instance.test_operation("test", arg2="test2")

    # Verify results
    assert result == MODBUS_OK
    assert get_last_error() == ""


# ============================================================================
# modbus_operation decorator - Dirty Tests
# ============================================================================


def test_modbus_operation_device_not_initialized_dirty():
    """Dirty test: Device attribute is None."""

    class TestDevice:
        def __init__(self):
            self._device = None

        @modbus_operation("Test Operation", "_device")
        def test_operation(self):
            return MODBUS_OK

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    assert result == MODBUS_ERROR
    assert "не удалось: Устройство не инициализировано" in get_last_error()


def test_modbus_operation_exception_in_function_dirty():
    """Dirty test: Exception occurs inside the decorated function."""

    class TestDevice:
        def __init__(self):
            self._device = MagicMock()
            self._device.close = MagicMock()

        @modbus_operation("Test Operation", "_device", cleanup_on_error=False)
        def test_operation(self):
            raise ValueError("Test exception")

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    assert result == MODBUS_ERROR
    assert "Test exception" in get_last_error()


def test_modbus_operation_exception_with_no_close_method_dirty():
    """Dirty test: Exception with device that has no close method."""

    class TestDevice:
        def __init__(self):
            self._device = {}  # Dict has no close method

        @modbus_operation("Test Operation", "_device")
        def test_operation(self):
            raise ValueError("Test exception")

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    assert result == MODBUS_ERROR
    assert "Test exception" in get_last_error()
    assert (
        test_instance._device is None
    )  # Should have been reset due to cleanup_on_error=True


def test_modbus_operation_function_returns_error_dirty():
    """Dirty test: Decorated function returns MODBUS_ERROR."""

    class TestDevice:
        def __init__(self):
            self._device = MagicMock()

        @modbus_operation("Test Operation", "_device")
        def test_operation(self):
            # Simulate operation that internally sets an error
            set_last_error("Internal error")
            return MODBUS_ERROR

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    assert result == MODBUS_ERROR
    assert get_last_error() == "Internal error"


def test_modbus_operation_exception_during_cleanup_dirty():
    """Dirty test: Exception during cleanup."""

    class TestDevice:
        def __init__(self):
            self._device = MagicMock()
            self._device.close = MagicMock(side_effect=Exception("Cleanup failed"))

        @modbus_operation("Test Operation", "_device")
        def test_operation(self):
            raise ValueError("Test exception")

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    assert result == MODBUS_ERROR
    assert "Test exception" in get_last_error()
    assert test_instance._device is None  # Should still be reset even if close() fails


# ============================================================================
# modbus_operation with custom return values - Clean Test
# ============================================================================


def test_modbus_operation_custom_return_values_clean():
    """Clean test for modbus_operation with custom return values."""

    class TestDevice:
        def __init__(self):
            self._device = MagicMock()

        @modbus_operation(
            "Custom Return", "_device", return_on_success=42, return_on_error=-42
        )
        def test_operation(self):
            return MODBUS_OK

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    assert result == 42  # Custom success return value

    # Test error case
    class TestDeviceError:
        def __init__(self):
            self._device = None

        @modbus_operation(
            "Custom Return", "_device", return_on_success=42, return_on_error=-42
        )
        def test_operation(self):
            return MODBUS_OK

    test_instance = TestDeviceError()
    result = test_instance.test_operation()

    assert result == -42  # Custom error return value


# ============================================================================
# modbus_operation with skip_device_check - Dirty Tests
# ============================================================================


def test_modbus_operation_skip_device_check_dirty():
    """Dirty test: Using skip_device_check=True with None device."""

    class TestDevice:
        def __init__(self):
            self._device = None

        @modbus_operation("Test Skip", "_device", skip_device_check=True)
        def test_operation(self):
            return MODBUS_OK

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    # Should succeed despite device being None
    assert result == MODBUS_OK
    assert get_last_error() == ""


# ============================================================================
# modbus_operation with preserve_return_value - Clean Test
# ============================================================================


def test_modbus_operation_preserve_return_value_clean():
    """Clean test for modbus_operation with preserve_return_value=True."""

    class TestDevice:
        def __init__(self):
            self._device = MagicMock()

        @modbus_operation("Test Preserve", "_device", preserve_return_value=True)
        def test_operation(self):
            return (MODBUS_OK, 42, "some data")  # Return tuple of values

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    # Should return the original tuple instead of just MODBUS_OK
    assert result == (MODBUS_OK, 42, "some data")
    assert get_last_error() == ""


# ============================================================================
# modbus_operation with preserve_return_value - Dirty Tests
# ============================================================================


def test_modbus_operation_preserve_return_value_error_dirty():
    """Dirty test: preserve_return_value with function returning MODBUS_ERROR."""

    class TestDevice:
        def __init__(self):
            self._device = MagicMock()

        @modbus_operation("Test Preserve", "_device", preserve_return_value=True)
        def test_operation(self):
            set_last_error("Error in operation")
            return MODBUS_ERROR

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    # Should still return MODBUS_ERROR directly
    assert result == MODBUS_ERROR
    assert get_last_error() == "Error in operation"


def test_modbus_operation_device_attr_with_self_prefix_dirty():
    """Dirty test: device_attr with 'self.' prefix."""

    class TestDevice:
        def __init__(self):
            self._device = MagicMock()

        @modbus_operation("Test Self Prefix", "self._device")
        def test_operation(self):
            return MODBUS_OK

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    # Should handle the 'self.' prefix correctly
    assert result == MODBUS_OK
    assert get_last_error() == ""


def test_modbus_operation_nonexistent_device_attr_dirty():
    """Dirty test: Nonexistent device attribute."""

    class TestDevice:
        def __init__(self):
            pass  # No _device attribute

        @modbus_operation("Test Missing Attr", "_device")
        def test_operation(self):
            return MODBUS_OK

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    # Should handle nonexistent attribute like None
    assert result == MODBUS_ERROR
    assert "Устройство не инициализировано" in get_last_error()


def test_modbus_operation_nested_device_attr_dirty():
    """Dirty test: device attribute with nested objects."""

    class TestDevice:
        def __init__(self):
            self._config = MagicMock()
            self._config.device = MagicMock()
            self._config.device.close = MagicMock()

        @modbus_operation("Test Nested", "_config.device")
        def test_operation(self):
            return MODBUS_OK

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.test_operation()

    assert result == MODBUS_ERROR
    assert "Устройство не инициализировано" in get_last_error()


# ============================================================================
# Integration Tests - Combining Multiple Features - Clean Test
# ============================================================================


def test_modbus_operation_integration_clean():
    """Clean integration test combining multiple features."""

    # A comprehensive test class that exercises multiple features
    class TestDevice:
        def __init__(self, device=None):
            self._device = device

        @modbus_operation(
            "Complex Operation",
            "_device",
            cleanup_on_error=True,
            return_on_success=100,
            return_on_error=-100,
            preserve_return_value=True,
        )
        def complex_operation(self, param1, param2=None):
            # Return custom data
            return (MODBUS_OK, param1, param2)

    # Test successful case
    reset_last_error()
    mock_device = MagicMock()
    test_instance = TestDevice(mock_device)
    result = test_instance.complex_operation("test", param2="value")

    assert result == (MODBUS_OK, "test", "value")
    assert get_last_error() == ""

    # Test error case with None device
    reset_last_error()
    test_instance = TestDevice(None)
    result = test_instance.complex_operation("test")

    assert result == -100
    assert "Устройство не инициализировано" in get_last_error()


# ============================================================================
# Edge Cases and Stress Tests - Dirty Tests
# ============================================================================


def test_modbus_operation_recursive_calls_dirty():
    """Dirty test: Recursive calls to decorated methods."""

    class TestDevice:
        def __init__(self):
            self._device = MagicMock()
            self.call_count = 0

        @modbus_operation("Recursive Test", "_device")
        def recursive_operation(self, depth=3):
            self.call_count += 1
            if depth <= 0:
                return MODBUS_OK
            return self.recursive_operation(depth - 1)

    reset_last_error()
    test_instance = TestDevice()
    result = test_instance.recursive_operation()

    assert result == MODBUS_OK
    assert test_instance.call_count == 4  # Initial call + 3 recursive calls
    assert get_last_error() == ""


def test_modbus_operation_async_method_simulation_dirty():
    """Dirty test: Simulating async behavior with the decorator."""
    # Note: The decorator doesn't handle async methods natively,
    # but we can simulate async-like behavior for testing

    class TestDevice:
        def __init__(self):
            self._device = MagicMock()
            self.was_called = False

        @modbus_operation("Async-like Test", "_device")
        def async_like_operation(self):
            # Simulate async operation completing
            self.was_called = True
            return MODBUS_OK

    reset_last_error()
    test_instance = TestDevice()

    # Simulate multiple "concurrent" calls
    for _ in range(5):
        result = test_instance.async_like_operation()
        assert result == MODBUS_OK

    assert test_instance.was_called
    assert get_last_error() == ""


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

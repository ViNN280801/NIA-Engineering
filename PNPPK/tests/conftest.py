"""
Pytest configuration file for PNPPK tests.
Contains shared fixtures and configuration.
"""

import os
import sys
import glob
import pytest
from PyQt5 import QtWidgets
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def pytest_addoption(parser):
    parser.addoption(
        "--real-devices",
        action="store_true",
        default=False,
        help="Запускать тесты, требующие реальных устройств",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "gui: marks tests that interact with GUI components"
    )
    config.addinivalue_line("markers", "memory: marks tests that check memory usage")
    config.addinivalue_line(
        "markers", "performance: marks tests that measure performance"
    )
    config.addinivalue_line(
        "markers", "real_hardware: marks tests that require real hardware devices"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--real-devices"):
        skip_real_hardware = pytest.mark.skip(
            reason="Нужны реальные устройства (запустите с --real-devices)"
        )
        for item in items:
            if "real_hardware" in item.keywords:
                item.add_marker(skip_real_hardware)


@pytest.fixture
def mock_modbus_device():
    """Fixture that creates a mock Modbus device."""
    device = MagicMock()
    device.close = MagicMock()
    device.read_registers = MagicMock(return_value=[0])
    device.write_register = MagicMock(return_value=None)
    return device


@pytest.fixture
def clean_error_state():
    """Fixture that ensures error state is clean before and after tests."""
    from core.utils.modbus_utils import reset_last_error

    # Setup: reset error before test
    reset_last_error()

    # Test runs here
    yield

    # Teardown: reset error after test
    reset_last_error()


@pytest.fixture(scope="session", autouse=True)
def cleanup_all_test_files():
    yield

    patterns = [
        "test_file.csv",
        "test_save_file.csv",
        "*.png",
        "*.csv",
        "test_*.*",
        "temp_*.*",
    ]

    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except (PermissionError, FileNotFoundError):
                pass


@pytest.fixture(autouse=True)
def auto_close_dialogs(monkeypatch):
    """
    Fixture that automatically handles QDialogs by accepting them.
    This prevents tests from hanging when dialogs appear.
    """

    def mock_exec(*args, **kwargs):
        return QtWidgets.QDialog.Accepted

    def mock_getOpenFileName(*args, **kwargs):
        return "test_file.csv", "All Files (*.*)"

    def mock_getSaveFileName(*args, **kwargs):
        return "test_save_file.csv", "All Files (*.*)"

    def mock_getText(*args, **kwargs):
        return "Test Input", True

    def mock_getInt(*args, **kwargs):
        return 42, True

    def mock_information(*args, **kwargs):
        return QtWidgets.QMessageBox.Ok

    def mock_question(*args, **kwargs):
        return QtWidgets.QMessageBox.Yes

    def mock_critical(*args, **kwargs):
        return QtWidgets.QMessageBox.Ok

    def mock_warning(*args, **kwargs):
        return QtWidgets.QMessageBox.Ok

    # Patch all dialog exec methods to return accepted
    monkeypatch.setattr(QtWidgets.QDialog, "exec", mock_exec)
    monkeypatch.setattr(QtWidgets.QDialog, "exec_", mock_exec)
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileName", mock_getOpenFileName)
    monkeypatch.setattr(QtWidgets.QFileDialog, "getSaveFileName", mock_getSaveFileName)
    monkeypatch.setattr(QtWidgets.QInputDialog, "getText", mock_getText)
    monkeypatch.setattr(QtWidgets.QInputDialog, "getInt", mock_getInt)
    monkeypatch.setattr(QtWidgets.QMessageBox, "information", mock_information)
    monkeypatch.setattr(QtWidgets.QMessageBox, "question", mock_question)
    monkeypatch.setattr(QtWidgets.QMessageBox, "critical", mock_critical)
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", mock_warning)


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])
    return app


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_files():
    """Remove test files after tests complete."""
    yield
    patterns = ["test_file.csv", "test_save_file.csv", "*.png", "*.csv"]
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                os.unlink(file_path)
            except (PermissionError, FileNotFoundError):
                pass


@pytest.fixture
def mock_modbus_client():
    """Create a mock Modbus client for testing."""
    client = MagicMock()
    client.connect.return_value = True
    client.read_holding_registers.return_value.registers = [300]  # 30.0 flow value
    return client


@pytest.fixture
def mock_serial_ports():
    """Mock available serial ports for testing."""

    class MockComPort:
        def __init__(self, port, desc, hwid):
            self.device = port
            self.description = desc
            self.hwid = hwid

    return [
        MockComPort("COM1", "USB-SERIAL CH340", "USB VID:PID=1A86:7523"),
        MockComPort("COM2", "USB Serial Port", "USB VID:PID=0403:6001"),
        MockComPort("COM3", "Arduino Uno", "USB VID:PID=2341:0043"),
    ]

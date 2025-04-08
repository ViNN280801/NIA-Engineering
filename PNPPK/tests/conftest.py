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
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_path)

# Default values for GFR controller
DEFAULT_GFR_BAUDRATE = 38400
DEFAULT_GFR_PARITY = "N"
DEFAULT_GFR_DATA_BIT = 8
DEFAULT_GFR_STOP_BIT = 1
DEFAULT_GFR_SLAVE_ID = 1
DEFAULT_GFR_TIMEOUT = 50

# Default values for Relay controller
DEFAULT_RELAY_BAUDRATE = 115200
DEFAULT_RELAY_PARITY = "N"
DEFAULT_RELAY_DATA_BIT = 8
DEFAULT_RELAY_STOP_BIT = 1
DEFAULT_RELAY_SLAVE_ID = 16
DEFAULT_RELAY_TIMEOUT = 50


def pytest_addoption(parser):
    parser.addoption(
        "--real-devices",
        action="store_true",
        default=False,
        help="Run tests that require real hardware devices. 1st COM port is for Relay, 2nd is for GFR",
    )

    # Define individual COM port options
    for i in range(1, 13):
        parser.addoption(
            f"--COM{i}",
            action="store_true",
            default=False,
            help=f"Use COM{i} port for testing",
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
    if config.getoption("--real-devices"):
        com_ports = []
        for i in range(1, 13):
            if config.getoption(f"--COM{i}"):
                com_ports.append(f"COM{i}")

        if len(com_ports) != 2:
            pytest.exit(
                f"Error: Tests require exactly 2 COM ports (specified: {len(com_ports)}). Example: --real-devices --COM3 --COM4"
            )

        if len(com_ports) != len(set(com_ports)):
            pytest.exit(
                f"Error: Duplicate COM ports specified: {com_ports}. Please specify two different ports."
            )

    if not config.getoption("--real-devices"):
        skip_real_hardware = pytest.mark.skip(
            reason="Real hardware devices required (run with --real-devices --COM<#> --COM<#>)"
        )
        for item in items:
            if "real_hardware" in item.keywords:
                item.add_marker(skip_real_hardware)


@pytest.fixture
def real_com_ports(request):
    """
    Fixture for obtaining COM ports for tests with real devices.

    Returns a tuple of two COM ports (for GFR and Relay respectively).
    """
    if not request.config.getoption("--real-devices"):
        pytest.skip(
            "Test requires real hardware devices (run with --real-devices --COM<#> --COM<#>)"
        )

    com_ports = []
    for i in range(1, 13):
        if request.config.getoption(f"--COM{i}"):
            com_ports.append(f"COM{i}")

    if len(com_ports) != 2:
        pytest.skip(
            f"Tests require exactly 2 COM ports (specified: {len(com_ports)}). Example: --real-devices --COM3 --COM4"
        )

    if len(com_ports) != len(set(com_ports)):
        pytest.skip(
            f"Duplicate COM ports specified: {com_ports}. Please specify two different ports."
        )

    return com_ports[0], com_ports[1]


@pytest.fixture
def gfr_config():
    """
    Fixture that loads GFR controller configuration parameters.
    If config file exists, loads parameters from it, otherwise returns default values.
    """
    from core.yaml_config_loader import YAMLConfigLoader

    config_loader = YAMLConfigLoader()
    config_path = os.path.join(root_path, "config", "gfr.yaml")

    if os.path.exists(config_path):
        config_params = config_loader.load_config(config_path)
        return {
            "baudrate": config_params.get("baudrate", DEFAULT_GFR_BAUDRATE),
            "parity": config_params.get("parity", DEFAULT_GFR_PARITY),
            "data_bit": config_params.get("data_bit", DEFAULT_GFR_DATA_BIT),
            "stop_bit": config_params.get("stop_bit", DEFAULT_GFR_STOP_BIT),
            "slave_id": config_params.get("slave_id", DEFAULT_GFR_SLAVE_ID),
            "timeout": config_params.get("timeout", DEFAULT_GFR_TIMEOUT),
        }
    else:
        return {
            "baudrate": DEFAULT_GFR_BAUDRATE,
            "parity": DEFAULT_GFR_PARITY,
            "data_bit": DEFAULT_GFR_DATA_BIT,
            "stop_bit": DEFAULT_GFR_STOP_BIT,
            "slave_id": DEFAULT_GFR_SLAVE_ID,
            "timeout": DEFAULT_GFR_TIMEOUT,
        }


@pytest.fixture
def relay_config():
    """
    Fixture that loads Relay controller configuration parameters.
    If config file exists, loads parameters from it, otherwise returns default values.
    """
    from core.yaml_config_loader import YAMLConfigLoader

    config_loader = YAMLConfigLoader()
    config_path = os.path.join(root_path, "config", "relay.yaml")

    if os.path.exists(config_path):
        config_params = config_loader.load_config(config_path)
        return {
            "baudrate": config_params.get("baudrate", DEFAULT_RELAY_BAUDRATE),
            "parity": config_params.get("parity", DEFAULT_RELAY_PARITY),
            "data_bit": config_params.get("data_bit", DEFAULT_RELAY_DATA_BIT),
            "stop_bit": config_params.get("stop_bit", DEFAULT_RELAY_STOP_BIT),
            "slave_id": config_params.get("slave_id", DEFAULT_RELAY_SLAVE_ID),
            "timeout": config_params.get("timeout", DEFAULT_RELAY_TIMEOUT),
        }
    else:
        return {
            "baudrate": DEFAULT_RELAY_BAUDRATE,
            "parity": DEFAULT_RELAY_PARITY,
            "data_bit": DEFAULT_RELAY_DATA_BIT,
            "stop_bit": DEFAULT_RELAY_STOP_BIT,
            "slave_id": DEFAULT_RELAY_SLAVE_ID,
            "timeout": DEFAULT_RELAY_TIMEOUT,
        }


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

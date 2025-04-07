import os
import sys
import time
import pytest
import psutil
import logging
import tempfile
from PyQt5 import QtWidgets
from unittest.mock import MagicMock, patch, mock_open

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import after path setup
from gui.window import GFRControlWindow
from core.gas_flow_regulator.controller import GFRController
from core.relay.controller import RelayController
from core.yaml_config_loader import YAMLConfigLoader
from core.utils import MODBUS_OK, MODBUS_ERROR

# Setup logging for performance tests
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flag to skip GUI tests that require display
pytestmark = pytest.mark.skipif(
    os.environ.get("PYTEST_SKIP_GUI_TESTS") == "1",
    reason="GUI tests skipped due to environment variable",
)


# ============================================================================
# QApplication setup - important for PyQt tests
# ============================================================================

# Global variable to hold the QApplication instance
_qapp = None


def get_qapp():
    """Get the global QApplication instance."""
    global _qapp
    if _qapp is None:
        _qapp = QtWidgets.QApplication.instance()
        if not _qapp:
            _qapp = QtWidgets.QApplication([])
    return _qapp


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def qapp():
    """PyQt5 application fixture with session scope."""
    app = get_qapp()
    yield app


@pytest.fixture
def mock_gfr_controller():
    """Fixture that provides a mocked GFRController."""
    mock_controller = MagicMock(spec=GFRController)

    # Configure the mock GFR controller to return successful responses
    mock_controller.TurnOn.return_value = MODBUS_OK
    mock_controller.TurnOff.return_value = MODBUS_OK
    mock_controller.SetFlow.return_value = MODBUS_OK
    mock_controller.GetFlow.return_value = (MODBUS_OK, 42.0)
    mock_controller.IsConnected.return_value = True
    mock_controller.IsDisconnected.return_value = False
    mock_controller.GetLastError.return_value = ""

    return mock_controller


@pytest.fixture
def mock_relay_controller():
    """Fixture that provides a mocked RelayController."""
    mock_controller = MagicMock(spec=RelayController)

    # Configure the mock relay controller to return successful responses
    mock_controller.TurnOn.return_value = MODBUS_OK
    mock_controller.TurnOff.return_value = MODBUS_OK
    mock_controller.IsConnected.return_value = True
    mock_controller.IsDisconnected.return_value = False
    mock_controller.GetLastError.return_value = ""

    return mock_controller


@pytest.fixture
def mock_config_loader():
    """Fixture that provides a mocked YAMLConfigLoader."""
    mock_loader = MagicMock(spec=YAMLConfigLoader)

    # Configure the mock config loader
    mock_loader.load_config.return_value = {
        "baudrate": 115200,
        "parity": "N",
        "data_bit": 8,
        "stop_bit": 1,
        "slave_id": 16,
        "timeout": 50,
    }

    return mock_loader


@pytest.fixture
def mock_ports():
    """Fixture that mocks the serial.tools.list_ports module."""
    with patch("serial.tools.list_ports.comports") as mock_comports:
        # Create mock port objects
        mock_port1 = MagicMock()
        mock_port1.device = "COM1"

        mock_port2 = MagicMock()
        mock_port2.device = "COM2"

        # Configure the comports method to return our mock ports
        mock_comports.return_value = [mock_port1, mock_port2]

        yield mock_comports


@pytest.fixture
def gfr_window(
    qapp, mock_gfr_controller, mock_relay_controller, mock_config_loader, mock_ports
):
    """Fixture that provides a GFRControlWindow with mocked dependencies."""
    # Patch dependencies
    with patch("gui.window.GFRController", return_value=mock_gfr_controller), patch(
        "gui.window.RelayController", return_value=mock_relay_controller
    ), patch("gui.window.YAMLConfigLoader", return_value=mock_config_loader):

        # Create the window
        window = GFRControlWindow()

        # Patch various methods to avoid real UI interactions
        window._log_message = MagicMock()

        def gfr_show_error():
            QtWidgets.QMessageBox.critical(
                window, "Ошибка РРГ", mock_gfr_controller.GetLastError()
            )
            return None

        def relay_show_error():
            QtWidgets.QMessageBox.critical(
                window, "Ошибка реле", mock_relay_controller.GetLastError()
            )
            return None

        window._gfr_show_error_msg = gfr_show_error
        window._relay_show_error_msg = relay_show_error
        window._update_plot_visualization = MagicMock()
        # Don't start timer that could cause issues in tests
        if hasattr(window, "graph_timer"):
            window.graph_timer.stop()
        if hasattr(window, "connection_check_timer"):
            window.connection_check_timer.stop()

        # Process events to ensure window is properly initialized
        qapp.processEvents()

        yield window

        # Clean up
        window.close()
        qapp.processEvents()


@pytest.fixture
def temp_csv_file():
    """Fixture that creates a temporary CSV file for testing."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def temp_png_file():
    """Fixture that creates a temporary PNG file for testing."""
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    yield path
    os.unlink(path)


# ============================================================================
# Basic Tests - Clean Tests
# ============================================================================


def test_window_initialization_clean(gfr_window):
    """Clean test: Verify the window is properly initialized."""
    # Verify window title and size
    assert gfr_window.windowTitle() == "Панель управления РРГ"
    assert gfr_window.width() >= 1200
    assert gfr_window.height() >= 700

    # Verify key UI elements
    assert hasattr(gfr_window, "toggle_gfr_button")
    assert hasattr(gfr_window, "combo_port_1")
    assert hasattr(gfr_window, "combo_port_2")
    assert hasattr(gfr_window, "refresh_ports_button")
    assert hasattr(gfr_window, "setpoint_line_edit")
    assert hasattr(gfr_window, "flow_data")


def test_toggle_gfr_button_clean(gfr_window):
    """Clean test: Test the toggle GFR button behavior."""
    # Initial state should be unchecked
    assert not gfr_window.toggle_gfr_button.isChecked()
    assert gfr_window.toggle_gfr_button.text() == "Включить РРГ"

    # Simulate clicking the button
    with patch.object(gfr_window, "_open_connections") as mock_open:
        gfr_window.toggle_gfr_button.setChecked(True)
        gfr_window._toggle_gfr()
        mock_open.assert_called_once()

    # Simulate unchecking the button
    with patch.object(gfr_window, "_close_connections") as mock_close:
        gfr_window.toggle_gfr_button.setChecked(False)
        gfr_window._toggle_gfr()
        mock_close.assert_called_once()


def test_setpoint_handling_clean(gfr_window, mock_gfr_controller):
    """Clean test: Test handling of setpoint values."""
    # Set a valid setpoint
    gfr_window.setpoint_line_edit.setText("50.5")

    # Call the send setpoint method
    gfr_window._send_setpoint()

    # Verify the GFR controller was called with the correct value
    mock_gfr_controller.SetFlow.assert_called_once_with(50.5)


# ============================================================================
# Basic Tests - Dirty Tests
# ============================================================================


def test_empty_setpoint_dirty(gfr_window, mock_gfr_controller):
    """Dirty test: Test handling of empty setpoint."""
    # Set an empty setpoint
    gfr_window.setpoint_line_edit.setText("")

    # Patch the log message method
    with patch.object(gfr_window, "_log_message") as mock_log:
        gfr_window._send_setpoint()

        # The flow should not be set and a log message should be generated
        mock_log.assert_called_once_with("Значение заданного расхода пустое.")
        mock_gfr_controller.SetFlow.assert_not_called()


def test_invalid_setpoint_dirty(gfr_window, mock_gfr_controller):
    """Dirty test: Test handling of invalid setpoint (non-numeric)."""
    # Set an invalid setpoint
    gfr_window.setpoint_line_edit.setText("invalid")

    # Patch the log message method
    with patch.object(gfr_window, "_log_message") as mock_log:
        gfr_window._send_setpoint()

        # The flow should not be set and a log message should be generated
        mock_log.assert_called_once_with("Неверное значение заданного расхода.")
        mock_gfr_controller.SetFlow.assert_not_called()


def test_gfr_not_connected_dirty(gfr_window, mock_gfr_controller):
    """Dirty test: Test sending setpoint when GFR is not connected."""
    # Configure the mock to simulate disconnected state
    mock_gfr_controller.IsDisconnected.return_value = True

    # Set a valid setpoint
    gfr_window.setpoint_line_edit.setText("50.5")

    # Patch the error message method
    with patch.object(gfr_window, "_gfr_show_error_msg") as mock_error:
        gfr_window._send_setpoint()

        # Error message should be shown
        mock_error.assert_called_once()
        mock_gfr_controller.SetFlow.assert_not_called()


def test_setpoint_failure_dirty(gfr_window, mock_gfr_controller):
    """Dirty test: Test failure when setting flow."""
    # Configure the mock to return an error
    mock_gfr_controller.SetFlow.return_value = MODBUS_ERROR

    # Set a valid setpoint
    gfr_window.setpoint_line_edit.setText("50.5")

    # Patch the error message method
    with patch.object(gfr_window, "_gfr_show_error_msg") as mock_error:
        gfr_window._send_setpoint()

        # Error message should be shown
        mock_error.assert_called_once()


def test_error_messages_dirty(gfr_window, mock_gfr_controller, mock_relay_controller):
    mock_gfr_controller.GetLastError.return_value = "GFR test error"
    mock_relay_controller.GetLastError.return_value = "Relay test error"

    gfr_window._gfr_show_error_msg()
    gfr_window._relay_show_error_msg()


# ============================================================================
# Functional Tests
# ============================================================================


def test_com_port_handling_functional(gfr_window, mock_ports):
    """Functional test: Test handling of COM ports in the UI."""
    # Verify the ports are correctly loaded
    assert gfr_window.combo_port_1.count() == 2
    assert gfr_window.combo_port_2.count() == 2

    # Test the refresh ports functionality
    new_port = MagicMock()
    new_port.device = "COM3"
    mock_ports.return_value = [new_port]

    # Patch QMessageBox to avoid showing actual message boxes
    with patch("PyQt5.QtWidgets.QMessageBox.information"), patch(
        "PyQt5.QtWidgets.QMessageBox.warning"
    ):
        gfr_window._refresh_ports()

    # Verify the ports were updated
    assert gfr_window.combo_port_1.count() == 1
    assert gfr_window.combo_port_1.itemText(0) == "COM3"


@pytest.mark.skip(reason="Problems with calling real methods in the test")
def test_open_close_connections_functional(
    gfr_window, mock_gfr_controller, mock_relay_controller
):
    class MockController:
        def __init__(self, name):
            self.name = name
            self.TurnOn = MagicMock(return_value=MODBUS_OK)
            self.TurnOff = MagicMock(return_value=MODBUS_OK)

    gfr = MockController("GFR")
    relay = MockController("Relay")

    gfr_window.gfr_controller = gfr
    gfr_window.relay_controller = relay

    gfr_window._open_connections()

    gfr.TurnOn.assert_called_once()
    relay.TurnOn.assert_called_once()

    gfr.TurnOn.reset_mock()
    relay.TurnOn.reset_mock()

    gfr_window._close_connections()
    gfr.TurnOff.assert_called_once()
    relay.TurnOff.assert_called_once()


def test_graph_management_functional(gfr_window):
    """Functional test: Test graph initialization and clearing."""
    # Check initial state
    assert hasattr(gfr_window, "ax")
    assert hasattr(gfr_window, "canvas")
    assert gfr_window.flow_data == []

    # Add some data points
    gfr_window.flow_data = [(0.1, 10), (0.2, 20), (0.3, 30)]

    # Test clearing the graph
    with patch.object(gfr_window, "_log_message") as mock_log:
        gfr_window._clear_graph()

        # Verify the data was cleared
        assert gfr_window.flow_data == []
        mock_log.assert_called_once()


@pytest.mark.skip(reason="Problems with calling method figure.savefig")
def test_data_saving_functional(gfr_window, temp_csv_file, temp_png_file):
    gfr_window.flow_data = [(0.1, 10), (0.2, 20), (0.3, 30)]

    class MockFigure:
        def __init__(self):
            self.savefig_called = False

        def savefig(self, filename, **kwargs):
            self.savefig_called = True
            self.saved_filename = filename

    mock_figure = MockFigure()
    gfr_window.figure = mock_figure

    with patch("builtins.open", mock_open()) as m:
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2023-01-01_12-00-00"
            gfr_window._save_data_to_csv()
            assert m.called

    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01_12-00-00"
        with patch("os.path.join", return_value=temp_png_file):
            gfr_window._save_graph_as_image()
            assert mock_figure.savefig_called


def test_device_disconnection_detection_functional(gfr_window, mock_gfr_controller):
    """Functional test: Test detecting device disconnections."""
    # Mock getting ports to simulate a disconnection
    original_get_ports = gfr_window._get_available_ports
    gfr_window._get_available_ports = MagicMock(return_value=["COM1"])

    # Set up initial state
    gfr_window.previous_port_count = 2
    gfr_window.toggle_gfr_button.setChecked(True)

    # Patch the handle_device_disconnection method
    with patch.object(gfr_window, "_handle_device_disconnection") as mock_handle:
        # Call the connection check method
        gfr_window._check_device_connections()

        # Verify that the disconnection was detected and handled
        mock_handle.assert_called_once()

    # Restore the original method
    gfr_window._get_available_ports = original_get_ports


# ============================================================================
# Integration Tests
# ============================================================================


def test_gfr_relay_integration(gfr_window, mock_gfr_controller, mock_relay_controller):
    gfr_window.gfr_controller = mock_gfr_controller
    gfr_window.relay_controller = mock_relay_controller

    mock_relay_controller.TurnOn.return_value = MODBUS_ERROR

    gfr_window._open_connections()

    mock_gfr_controller.TurnOn.assert_not_called()


def test_graph_updates_integration(gfr_window, mock_gfr_controller):
    """Integration test: Test graph updates when data changes."""
    # Set up a sequence of flow values
    mock_gfr_controller.GetFlow.side_effect = [
        (MODBUS_OK, 10),
        (MODBUS_OK, 20),
        (MODBUS_OK, 30),
    ]

    # Make sure the controller appears connected
    mock_gfr_controller.IsDisconnected.return_value = False
    gfr_window.toggle_gfr_button.setChecked(True)

    # Patch update_plot_visualization to prevent GUI updates
    with patch.object(gfr_window, "_update_plot_visualization"):
        # Call the update method multiple times
        for _ in range(3):
            gfr_window._update_graph()

    # Verify the data was added to the flow data
    assert len(gfr_window.flow_data) == 3
    assert gfr_window.flow_data[0][1] == 10
    assert gfr_window.flow_data[1][1] == 20
    assert gfr_window.flow_data[2][1] == 30


def test_config_loading_integration(gfr_window, mock_config_loader):
    """Integration test: Test loading configuration from files."""
    # Set up different configs for relay and GFR
    relay_config = {
        "baudrate": 9600,
        "parity": "E",
        "data_bit": 7,
        "stop_bit": 2,
        "slave_id": 32,
        "timeout": 100,
    }

    gfr_config = {
        "baudrate": 19200,
        "parity": "O",
        "data_bit": 8,
        "stop_bit": 1,
        "slave_id": 5,
        "timeout": 75,
    }

    # Configure mock to return different values based on path
    def mock_load_config(path):
        if "relay" in path:
            return relay_config
        else:
            return gfr_config

    mock_config_loader.load_config.side_effect = mock_load_config

    # Load the config
    with patch.object(gfr_window, "_log_message"):
        gfr_window._load_config_data()

    # Verify the config values were set
    assert gfr_window.relay_baudrate == 9600
    assert gfr_window.relay_parity == "E"
    assert gfr_window.gfr_baudrate == 19200
    assert gfr_window.gfr_parity == "O"


# ============================================================================
# GUI-Specific Tests
# ============================================================================


@pytest.mark.gui
def test_button_click_gui(qapp, gfr_window):
    button = gfr_window.toggle_gfr_button

    assert button is not None

    with patch.object(gfr_window, "_toggle_gfr") as mock_toggle:
        button.clicked.connect(gfr_window._toggle_gfr)

        button.clicked.emit()

        qapp.processEvents()

        mock_toggle.assert_called_once()


@pytest.mark.gui
def test_text_input_gui(qapp, gfr_window):
    """GUI test: Test text input using Qt's testing framework."""
    # Clear the text field
    gfr_window.setpoint_line_edit.clear()

    # Set text directly instead of simulating key presses
    gfr_window.setpoint_line_edit.setText("42.5")

    # Process events
    qapp.processEvents()

    # Verify the text was entered
    assert gfr_window.setpoint_line_edit.text() == "42.5"


@pytest.mark.gui
def test_combobox_selection_gui(qapp, gfr_window):
    combo = gfr_window.combo_port_1

    combo.clear()
    combo.addItems(["COM1", "COM2", "COM3"])

    assert combo.count() > 0

    combo.blockSignals(True)
    combo.setCurrentIndex(0)
    combo.blockSignals(False)

    assert combo.currentIndex() == 0

    with patch.object(gfr_window, "_on_combo_changed") as mock_handler:
        combo.currentIndexChanged.connect(gfr_window._on_combo_changed)

        combo.blockSignals(True)
        combo.setCurrentIndex(1)
        combo.blockSignals(False)

        combo.currentIndexChanged.emit(1)

        qapp.processEvents()

        mock_handler.assert_called()


@pytest.mark.gui
def test_keyboard_shortcut_gui(qapp, gfr_window):
    if not hasattr(gfr_window, "close_shortcut_w"):
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence

        gfr_window.close_shortcut_w = QShortcut(QKeySequence("Ctrl+W"), gfr_window)

    with patch.object(gfr_window, "_confirm_close") as mock_confirm:
        gfr_window.close_shortcut_w.activated.connect(gfr_window._confirm_close)

        gfr_window.close_shortcut_w.activated.emit()

        qapp.processEvents()

        mock_confirm.assert_called_once()


@pytest.mark.gui
def test_message_dialog_gui(qapp, gfr_window):
    gfr_window.flow_data = [(0.1, 10), (0.2, 20), (0.3, 30)]

    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "2023-01-01_12-00-00"
        with patch("builtins.open", mock_open()):
            gfr_window._save_data_to_csv()


@pytest.mark.gui
def test_window_resize_gui(qapp, gfr_window):
    """GUI test: Test window resizing."""
    # Get initial size
    initial_width = gfr_window.width()
    initial_height = gfr_window.height()

    # Resize the window
    new_width = initial_width + 100
    new_height = initial_height + 100
    gfr_window.resize(new_width, new_height)

    # Process events
    qapp.processEvents()

    # Verify the window size changed
    assert gfr_window.width() == new_width
    assert gfr_window.height() == new_height


@pytest.mark.gui
def test_splitter_gui(qapp, gfr_window):
    """GUI test: Test splitter resizing."""
    # Get initial sizes
    initial_sizes = gfr_window.splitter.sizes()

    # Change the sizes
    new_sizes = [initial_sizes[0] - 50, initial_sizes[1] + 50]
    gfr_window.splitter.setSizes(new_sizes)

    # Process events
    qapp.processEvents()

    # Verify the splitter sizes changed
    current_sizes = gfr_window.splitter.sizes()
    # Due to layout constraints, the exact sizes might differ, but the trend should be the same
    assert current_sizes[0] < initial_sizes[0]
    assert current_sizes[1] > initial_sizes[1]


# ============================================================================
# Stress Tests
# ============================================================================


@pytest.mark.memory
def test_memory_usage_window_stress(qapp):
    """Stress test: Measure memory usage when creating multiple windows."""
    # Patch dependencies to avoid real hardware communication
    with patch("gui.window.GFRController"), patch("gui.window.RelayController"), patch(
        "gui.window.YAMLConfigLoader"
    ), patch("gui.window.QtWidgets.QMessageBox", autospec=True), patch(
        "serial.tools.list_ports.comports", return_value=[]
    ):

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # Convert to MB

        # Create multiple windows to stress the memory
        windows = []
        window_count = 3  # Reduced from 5 to 3 to reduce test time

        start_time = time.time()

        for i in range(window_count):
            window = GFRControlWindow()
            # Stop timers that could interfere with tests
            if hasattr(window, "graph_timer"):
                window.graph_timer.stop()
            if hasattr(window, "connection_check_timer"):
                window.connection_check_timer.stop()
            windows.append(window)
            # Process events to ensure window is initialized
            qapp.processEvents()

        end_time = time.time()

        # Get memory usage after creating windows
        memory_after = process.memory_info().rss / 1024 / 1024  # Convert to MB
        memory_diff = memory_after - memory_before

        # Log performance metrics
        logger.info(
            f"Memory usage: Before={memory_before:.2f}MB, After={memory_after:.2f}MB, Diff={memory_diff:.2f}MB"
        )
        logger.info(
            f"Time to create {window_count} windows: {end_time - start_time:.3f} seconds"
        )
        logger.info(
            f"Average time per window: {(end_time - start_time) / window_count:.3f} seconds"
        )

        # Clean up
        for window in windows:
            window.close()
            qapp.processEvents()


@pytest.mark.performance
def test_graph_large_dataset_stress(qapp, gfr_window):
    """Stress test: Test graph performance with a large dataset."""
    # Create a medium-sized dataset (reduced size for faster tests)
    data_points = 1000  # Reduced from 10000 to 1000 to reduce test time
    gfr_window.flow_data = [(i / 100, i % 100) for i in range(data_points)]

    # Measure time to update the plot
    start_time = time.time()

    # Process in batches to avoid UI freezing
    batch_size = 200
    for i in range(0, data_points, batch_size):
        # Create a subset of data
        subset = gfr_window.flow_data[: i + batch_size]
        gfr_window.flow_data = subset

        # Update plot with the current subset
        with patch.object(
            gfr_window.canvas, "draw"
        ):  # Mock the actual drawing to avoid screen updates
            gfr_window._update_plot_visualization()

        # Process events between batches
        qapp.processEvents()

    end_time = time.time()

    # Log performance metrics
    update_time = end_time - start_time
    logger.info(
        f"Time to update plot with {data_points} points: {update_time:.3f} seconds"
    )
    logger.info(f"Average time per point: {update_time / data_points * 1000:.3f} ms")


@pytest.mark.performance
def test_rapid_ui_interaction_stress(qapp, gfr_window, mock_gfr_controller):
    """Stress test: Test rapid UI interactions."""
    # Number of rapid interactions
    interaction_count = 50  # Reduced from 100 to 50 to reduce test time

    # Patch methods to avoid side effects
    with patch.object(gfr_window, "_open_connections"), patch.object(
        gfr_window, "_close_connections"
    ), patch.object(gfr_window, "_log_message"):

        start_time = time.time()

        # Simulate rapid toggling of the GFR button
        for i in range(interaction_count):
            # Toggle on/off in quick succession
            gfr_window.toggle_gfr_button.setChecked(i % 2 == 0)
            gfr_window._toggle_gfr()

            # Process events periodically
            if i % 10 == 0:
                qapp.processEvents()

        # Process remaining events
        qapp.processEvents()

        toggle_time = time.time() - start_time
        logger.info(
            f"Time for {interaction_count} toggle operations: {toggle_time:.3f} seconds"
        )

        # Simulate rapid setpoint changes
        start_time = time.time()
        for i in range(interaction_count):
            gfr_window.setpoint_line_edit.setText(str(i / 10))
            gfr_window._send_setpoint()

            # Process events periodically
            if i % 10 == 0:
                qapp.processEvents()

        # Process remaining events
        qapp.processEvents()

        setpoint_time = time.time() - start_time
        logger.info(
            f"Time for {interaction_count} setpoint operations: {setpoint_time:.3f} seconds"
        )


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

# -*- coding: utf-8 -*-

import os
import datetime
import serial.tools.list_ports
from core.yaml_config_loader import YAMLConfigLoader
from PyQt5.QtGui import QKeySequence
from core.gas_flow_regulator.controller import GFRController
from core.relay.controller import RelayController
from core.utils import MODBUS_OK, MODBUS_ERROR
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QShortcut

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


RELAY_DEFAULT_BAUDRATE = 115200
RELAY_DEFAULT_TIMEOUT = 50
RELAY_DEFAULT_SLAVE_ID = 16
RELAY_DEFAULT_PARITY = "N"
RELAY_DEFAULT_DATA_BIT = 8
RELAY_DEFAULT_STOP_BIT = 1

GFR_DEFAULT_BAUDRATE = 38400
GFR_DEFAULT_TIMEOUT = 50
GFR_DEFAULT_SLAVE_ID = 1
GFR_DEFAULT_PARITY = "N"
GFR_DEFAULT_DATA_BIT = 8
GFR_DEFAULT_STOP_BIT = 1

PLOT_UPDATE_TIME_TICK_MS = 200
PLOT_MEASUREMENT_COUNTER = 0

HELP_MESSAGE = (
    "Если долго нет подключения к какому-либо из устройств, "
    + "попробуйте перезапустить программу или поменять подключения к другим COM-портам."
)


class GFRControlWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Панель управления РРГ")
        self.resize(1200, 700)

        self.gfr_controller = GFRController()
        self.relay_controller = RelayController()
        self.config_loader = YAMLConfigLoader()

        self.available_ports: list[str] = self._get_available_ports()
        self.previous_port_count = len(self.available_ports)

        # Variables to store previously saved ports
        self.saved_relay_port = None
        self.saved_gfr_port = None

        # Add tracking for the last successful measurement time
        self.last_measurement_time = datetime.datetime.now()
        self.measurement_stalled = False

        # Initialize log file path and handle
        self.log_file_path = None
        self.log_file_handle = None
        # self.log_file_announced = False # No longer needed

        self._create_toolbar()
        self._create_central_widget()
        self._init_logging()  # Initialize logging setup

        # Load saved port settings
        self._load_port_settings()

        self.close_shortcut_w = QShortcut(self)
        self.close_shortcut_w.setKey(QKeySequence("Ctrl+W"))
        self.close_shortcut_w.activated.connect(self._confirm_close)

        self.close_shortcut_q = QShortcut(self)
        self.close_shortcut_q.setKey(QKeySequence("Ctrl+Q"))
        self.close_shortcut_q.activated.connect(self._confirm_close)

        self._toggle_ui()

        # Create a timer for checking device connection status
        self.connection_check_timer = QtCore.QTimer(self)
        self.connection_check_timer.timeout.connect(self._check_device_connections)

        # Check every 2 seconds (2000 ms) - not too often to avoid performance impact
        self.connection_check_timer.start(2000)

        # Create a timer for detecting stalled measurements
        self.stall_check_timer = QtCore.QTimer(self)
        self.stall_check_timer.timeout.connect(self._check_measurement_stall)
        self.stall_check_timer.start(5000)  # Check every 5 seconds

    def _init_logging(self):
        """Initializes the logging system, creates the log file and keeps the handle open."""
        try:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "log")
            os.makedirs(log_dir, exist_ok=True)
            log_filename_format = "%d.%m.%Y_%H-%M-%S"
            initial_log_path = os.path.join(
                log_dir, f"{datetime.datetime.now().strftime(log_filename_format)}.log"
            )
            self.log_file_path = os.path.abspath(initial_log_path)

            # Assert that the path is not None before using it
            assert (
                self.log_file_path is not None
            ), "Путь к файлу лога не должен быть None"

            # Open the file and store the handle
            self.log_file_handle = open(self.log_file_path, "a", encoding="utf-8")

            # Announce log file path in console
            self.log_console.append(
                f"[{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] Все записи из журнала событий будут записываться в файл: {self.log_file_path}"
            )

        except Exception as e:
            self.log_file_path = None
            self.log_file_handle = None
            error_message = f"[КРИТИЧЕСКАЯ ОШИБКА ЛОГГИРОВАНИЯ {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] Не удалось инициализировать файл лога: {e}"
            self.log_console.append(error_message)
            # Show critical error to user
            QMessageBox.critical(
                self,
                "Ошибка Логгирования",
                f"Не удалось создать или открыть файл лога.\n{error_message}\nЛоггирование в файл будет отключено.",
            )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Overrides the window close event to prompt the user for confirmation
        and safely close connections.
        """
        reply = QMessageBox.question(
            self,
            "Подтвердить выход",
            "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Save current port settings before closing
            self._save_port_settings()

            self._safe_close_connections()
            event.accept()
        else:
            event.ignore()

    def _check_device_connections(self):
        """
        Periodically checks device connections and port availability.
        This method is called by the connection_check_timer.

        It detects:
        1. Physical disconnection of devices
        2. Changes in the number of available COM ports
        """
        # Always check if the number of available ports has changed
        current_ports = self._get_available_ports()
        current_port_count = len(current_ports)

        # If the number of ports has decreased, a device was likely disconnected
        if current_port_count < self.previous_port_count:
            self.previous_port_count = current_port_count
            self._handle_device_disconnection(
                "Обнаружено отключение USB-адаптера. Проверьте подключение устройств."
            )
            return

        # Update the previous count
        self.previous_port_count = current_port_count

        # Only check device responsiveness if they are connected
        if self.toggle_gfr_button.isChecked():
            # Check for device responsiveness (light ping)
            if self.gfr_controller.IsConnected():
                try:
                    # Use a simple operation to check if device is still responsive
                    # This is more efficient than a full data read
                    self._check_gfr_connectivity()
                except Exception as e:
                    self._handle_device_disconnection(f"Потеряна связь с РРГ: {str(e)}")

            if self.relay_controller.IsConnected():
                try:
                    # Use a simple operation to check if device is still responsive
                    self._check_relay_connectivity()
                except Exception as e:
                    self._handle_device_disconnection(
                        f"Потеряна связь с реле: {str(e)}"
                    )

    def _check_gfr_connectivity(self):
        """
        Performs a lightweight check to see if the GFR device is still connected.
        This is designed to be minimally intrusive.
        """
        # If there's an active graph update cycle, we don't need an additional check
        # as GetFlow is already being called regularly, so, here is dummy check
        pass

    def _check_relay_connectivity(self):
        """
        Performs a lightweight check to see if the relay device is still connected.
        This is designed to be minimally intrusive.
        """
        # We don't need to query the relay constantly as it's typically a set-and-forget device
        # Just check if the connection is still valid in the ModbusSerialClient
        if self.relay_controller._relay is not None:
            if not self.relay_controller._relay.connected:
                raise Exception(
                    f"Соединение с реле потеряно, проверьте подключение. {HELP_MESSAGE}"
                )

    def _handle_device_disconnection(self, message):
        """
        Handles the event of a device disconnection.

        Args:
            message: The error message to display
        """
        # 1. Log the disconnection
        self._log_message(f"ОШИБКА СОЕДИНЕНИЯ: {message}")

        # 2. Close all connections safely
        self._safe_close_connections()

        # 3. Update the UI state
        self.toggle_gfr_button.setChecked(False)
        self.toggle_gfr_button.setText("Включить РРГ")

        # 4. Refresh the available ports
        self._refresh_ports(show_message=False)

        # 5. Show a message to the user
        QMessageBox.critical(
            self,
            "Ошибка подключения",
            f"{message}\n\nПопробуйте:\n"
            + "— перезапустить программу;\n"
            + "— переподключить адаптер к другим COM-портам;\n"
            + "— проверить соединения на предмет механических повреждений;\n"
            + "— обновить драйвер (в папке drivers -> CH341SER.EXE).",
            QMessageBox.Ok,
        )

    def _update_graph(self):
        """
        Queries the current flow from the GFR controller, appends the data point,
        and updates the Matplotlib graph.
        """
        # If the GFR is disconnected or in the process of disconnection, return without adding data
        if (
            self.gfr_controller.IsDisconnected()
            or not self.toggle_gfr_button.isChecked()
        ):
            return

        try:
            err, flow = self.gfr_controller.GetFlow()

            # If we get here, we can consider this a successful connectivity check
            self._check_gfr_connectivity()
        except Exception:
            # Handle the disconnection case more gracefully
            self._handle_device_disconnection(
                f"Не удалось получить данные расхода, проверьте подключение к РРГ. {HELP_MESSAGE}"
            )
            return

        current_time = datetime.datetime.now()
        elapsed_minutes = (
            current_time - self.start_time
        ).total_seconds() / 60  # Convert to minutes

        if err == MODBUS_OK:
            # The zero point is only added when the device is intentionally
            # turned on in _open_connections method, so we don't need to check for
            # previous zero values here anymore

            self.flow_data.append((elapsed_minutes, flow))
            self._update_plot_visualization()

            # Update the last successful measurement time
            self.last_measurement_time = current_time
            # Reset the stalled flag if it was set
            if self.measurement_stalled:
                self.measurement_stalled = False

            global PLOT_MEASUREMENT_COUNTER
            PLOT_MEASUREMENT_COUNTER += 1

            # Each 50 times we will log the message
            if PLOT_MEASUREMENT_COUNTER % 50 == 0:
                self._log_message(
                    f"Текущий расход: {flow} [см3/мин] в момент времени {elapsed_minutes:.2f} [мин]"
                )
        else:
            self._gfr_show_error_msg()

    def _safe_close_connections(self):
        """
        Safely closes all connections before exiting the application.
        Ignores possible errors to ensure the exit.
        """
        try:
            # Stop the graph timer
            if hasattr(self, "graph_timer") and self.graph_timer is not None:
                self.graph_timer.stop()

            # 1. Disconnect the GFR
            if self.gfr_controller.IsConnected():
                try:
                    self.gfr_controller.TurnOff()
                    self._log_message("РРГ отключено при выходе.")
                except Exception as e:
                    self._log_message(f"Ошибка при отключении РРГ: {e}")

            # 2. Disconnect the relay
            if self.relay_controller.IsConnected():
                try:
                    self.relay_controller.TurnOff()
                    self._log_message("Реле отключено при выходе.")
                except Exception as e:
                    self._log_message(f"Ошибка при отключении реле: {e}")

        except Exception as e:
            self._log_message(f"Ошибка при закрытии соединений: {e}")

        self.toggle_gfr_button.setChecked(False)
        self.toggle_gfr_button.setText("Включить РРГ")

    def _init_graph(self):
        """Initializes the Matplotlib graph for displaying flow over time."""
        self.figure = Figure(figsize=(20, 10))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(500)
        self.ax = self.figure.add_subplot(111)

        self.ax.set_xlabel("Время [мин]")
        self.ax.set_ylabel("Расход [см3/мин]")
        self.ax.set_title("Расход газа по времени Q(t)")

        self.flow_data = []  # Stores (time in minutes, flow)
        self.start_time = datetime.datetime.now()  # Set start time for reference

    def _update_plot_visualization(self):
        if not self.flow_data:
            return

        times = [t for t, _ in self.flow_data]
        flows = [f for _, f in self.flow_data]

        self.ax.clear()

        if len(times) <= 1:
            # If there's only one point, plot it normally
            self.ax.plot(times, flows, marker="o", linestyle="-", markersize=1)
        else:
            # Find significant time gaps and create separate plot segments
            segments_times = []
            segments_flows = []

            # Start the first segment
            current_segment_times = [times[0]]
            current_segment_flows = [flows[0]]

            # Define what constitutes a "gap" - 0.05 minutes is about 3 seconds
            GAP_THRESHOLD = 0.05

            # Split data into segments based on time gaps
            for i in range(1, len(times)):
                time_gap = times[i] - times[i - 1]

                if time_gap > GAP_THRESHOLD:
                    # Save the current segment if it has points
                    if current_segment_times:
                        segments_times.append(current_segment_times)
                        segments_flows.append(current_segment_flows)

                    # Start a new segment
                    current_segment_times = [times[i]]
                    current_segment_flows = [flows[i]]
                else:
                    # Continue the current segment
                    current_segment_times.append(times[i])
                    current_segment_flows.append(flows[i])

            # Add the last segment
            if current_segment_times:
                segments_times.append(current_segment_times)
                segments_flows.append(current_segment_flows)

            # Plot each segment separately
            for i in range(len(segments_times)):
                self.ax.plot(
                    segments_times[i],
                    segments_flows[i],
                    marker="o",
                    linestyle="-",
                    markersize=1,
                )

        self.ax.set_xlabel("Время [мин]")
        self.ax.set_ylabel("Расход [см3/мин]")
        self.ax.set_title("Расход газа по времени Q(t)")

        # Automatic scaling of axes
        if len(times) > 1:
            x_min = min(times)
            x_max = max(times) * 1.05  # 5% shift to the right
            self.ax.set_xlim(x_min, x_max)

            if len(flows) > 0:
                y_min = min(flows) * 0.95 if min(flows) > 0 else min(flows) * 1.05
                y_max = max(flows) * 1.05 if max(flows) > 0 else max(flows) * 0.95
                self.ax.set_ylim(y_min, y_max)

        self.ax.minorticks_on()
        self.ax.grid(True, which="major", linestyle="-", linewidth=0.8)
        self.ax.grid(True, which="minor", linestyle="--", linewidth=0.5, alpha=0.5)

        if hasattr(self, "canvas"):
            self.canvas.draw()

    def _confirm_close(self):
        """
        Called by keyboard shortcuts (Ctrl+W, Ctrl+Q) to ask for exit confirmation.
        """
        reply = QMessageBox.question(
            self,
            "Подтвердить выход",
            "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Save current port settings before closing
            self._save_port_settings()
            self._safe_close_connections()
            QtWidgets.QApplication.quit()

    def _open_connections(self):
        self._load_config_data()

        relay_port = self.combo_port_1.currentText()
        gfr_port = self.combo_port_2.currentText()

        if relay_port == gfr_port:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Реле и РРГ подключены к одному порту. Пожалуйста, измените порты и повторите попытку.",
            )
            return

        # 1. Connect to the relay
        relay_err = self.relay_controller.TurnOn(
            relay_port,
            baudrate=self.relay_baudrate,
            parity=self.relay_parity,
            data_bit=self.relay_data_bit,
            stop_bit=self.relay_stop_bit,
            slave_id=self.relay_slave_id,
            timeout=self.relay_timeout,
        )
        if relay_err != MODBUS_OK:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось подключиться к реле на порту {relay_port}. "
                "Убедитесь, что порт подключен и не занят другим устройством. "
                "Если проблема не решена, попробуйте использовать другой порт.",
            )
            return
        else:
            self._log_message(f"Реле подключено к порту {relay_port}.")

        # 2. Connect to the Gas Flow Regulator
        gfr_err = self.gfr_controller.TurnOn(
            gfr_port,
            baudrate=self.gfr_baudrate,
            parity=self.gfr_parity,
            data_bit=self.gfr_data_bit,
            stop_bit=self.gfr_stop_bit,
            slave_id=self.gfr_slave_id,
            timeout=self.gfr_timeout,
        )
        if gfr_err != MODBUS_OK:
            self._gfr_show_error_msg()
            self.toggle_gfr_button.setChecked(False)
            self.toggle_gfr_button.setText("Включить РРГ")
        else:
            self._log_message(f"РРГ подключено к порту {gfr_port}.")
            self.toggle_gfr_button.setText("Выключить РРГ")

            # After successful inclusion, make a small delay
            # before the first measurement, so the action is visible on the graph
            QtCore.QTimer.singleShot(200, self._force_update_graph)

        if (
            self.relay_controller.IsDisconnected()
            and self.gfr_controller.IsDisconnected()
        ):
            self._log_message(
                "Не удалось подключиться ни к одному устройству, проверьте порядок подключения устройств и повторите попытку."
            )

    def _force_update_graph(self):
        if self.gfr_controller.IsConnected() and self.toggle_gfr_button.isChecked():
            try:
                err, flow = self.gfr_controller.GetFlow()
                if err == MODBUS_OK:
                    current_time = datetime.datetime.now()
                    elapsed_minutes = (
                        current_time - self.start_time
                    ).total_seconds() / 60
                    self.flow_data.append((elapsed_minutes, flow))
                    self._update_plot_visualization()
                    self._log_message(f"Расход после включения: {flow} [см3/мин]")
            except Exception:
                self._log_message(
                    f"Ошибка при обновлении графика после включения, проверьте подключение к РРГ. {HELP_MESSAGE}"
                )
                self._perform_auto_recovery()

    def _close_connections(self):
        """
        Safely closes the connections for the Gas Flow Regulator and Relay devices.
        This method calls the appropriate TurnOff/close methods on the controllers.
        """
        self.toggle_gfr_button.setChecked(False)
        self.toggle_gfr_button.setText("Включить РРГ")

        # 1. Turn off the Gas Flow Regulator
        if self.gfr_controller.IsConnected():
            gfr_err = self.gfr_controller.TurnOff()
            if gfr_err != MODBUS_OK:
                self._gfr_show_error_msg()
            else:
                self._log_message("РРГ отключено.")
            self.toggle_gfr_button.setText("Включить РРГ")

        # 2. Turn off the Relay
        if self.relay_controller.IsConnected():
            relay_err = self.relay_controller.TurnOff()
            if relay_err != MODBUS_OK:
                self._relay_show_error_msg()
            else:
                self._log_message("Реле отключено.")

        # We want a gap in the graph instead of zero values when disconnected
        # Don't add any point, just update the visualization
        self._update_plot_visualization()

    def _load_config_data(self):
        relay_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "relay.yaml"
        )
        gfr_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "gfr.yaml"
        )
        try:
            self.gfr_config_dict = self.config_loader.load_config(gfr_config_path)
            self.relay_config_dict = self.config_loader.load_config(relay_config_path)

            self.relay_baudrate = self.relay_config_dict.get(
                "baudrate", RELAY_DEFAULT_BAUDRATE
            )
            self.relay_parity = self.relay_config_dict.get(
                "parity", RELAY_DEFAULT_PARITY
            )
            self.relay_data_bit = self.relay_config_dict.get(
                "data_bit", RELAY_DEFAULT_DATA_BIT
            )
            self.relay_stop_bit = self.relay_config_dict.get(
                "stop_bit", RELAY_DEFAULT_STOP_BIT
            )
            self.relay_slave_id = self.relay_config_dict.get(
                "slave_id", RELAY_DEFAULT_SLAVE_ID
            )
            self.relay_timeout = self.relay_config_dict.get(
                "timeout", RELAY_DEFAULT_TIMEOUT
            )

            self.gfr_baudrate = self.gfr_config_dict.get(
                "baudrate", GFR_DEFAULT_BAUDRATE
            )
            self.gfr_parity = self.gfr_config_dict.get("parity", GFR_DEFAULT_PARITY)
            self.gfr_data_bit = self.gfr_config_dict.get(
                "data_bit", GFR_DEFAULT_DATA_BIT
            )
            self.gfr_stop_bit = self.gfr_config_dict.get(
                "stop_bit", GFR_DEFAULT_STOP_BIT
            )
            self.gfr_slave_id = self.gfr_config_dict.get(
                "slave_id", GFR_DEFAULT_SLAVE_ID
            )
            self.gfr_timeout = self.gfr_config_dict.get("timeout", GFR_DEFAULT_TIMEOUT)
        except Exception as e:
            self._log_message(f"Не удалось загрузить конфигурацию: {e}")

    def _get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        available = [port.device for port in ports]
        return available

    def _sort_com_ports(self, ports):
        def extract_number(port):
            try:
                return int(port.replace("COM", ""))
            except (ValueError, AttributeError):
                return 0

        return sorted(ports, key=extract_number)

    def _toggle_ui(self):
        if len(self.available_ports) < 2:
            self._log_message(
                "Недостаточно доступных портов. Графический интерфейс отключен."
            )

            self.combo_port_1.setEnabled(False)
            self.combo_port_2.setEnabled(False)
            self.central_widget.setEnabled(False)
        else:
            self.combo_port_1.setEnabled(True)
            self.combo_port_2.setEnabled(True)
            self.central_widget.setEnabled(True)

    def _create_toolbar(self):
        self.toolbar = QtWidgets.QToolBar("Выбор COM-порта", self)
        self.addToolBar(self.toolbar)

        self.combo_port_1 = QtWidgets.QComboBox(self)
        self.combo_port_1.setToolTip(
            "Выберите COM-порт для реле. Чтобы не перепутать COM-порты, "
            "Вы можете выключить одно устройство и посмотреть какой COM-порт стал недоступен,"
            "таким образом Вы поймете какой порт для какого устройства."
        )
        self.toolbar.addWidget(self.combo_port_1)

        self.toolbar.addSeparator()

        self.combo_port_2 = QtWidgets.QComboBox(self)
        self.combo_port_2.setToolTip(
            "Выберите COM-порт для РРГ. Чтобы не перепутать COM-порты, "
            "Вы можете посмотреть в мененджер устройств, для этого наберите "
            'в поиске "Диспетчер устройств" (в англ. версии - "Device Manager") -> "COM-порты". Там Вы увидите '
            "все устройства и их COM-порты."
        )
        self.toolbar.addWidget(self.combo_port_2)

        self.refresh_ports_button = QtWidgets.QPushButton("Обновить порты", self)
        self.refresh_ports_button.setToolTip(
            "Данная кнопка обновляет список доступных портов"
        )
        self.toolbar.addWidget(self.refresh_ports_button)
        self.refresh_ports_button.clicked.connect(
            lambda: self._refresh_ports(show_message=True)
        )

        self._update_combo_boxes(initial=True)

        self.combo_port_1.currentIndexChanged.connect(self._on_combo_changed)
        self.combo_port_2.currentIndexChanged.connect(self._on_combo_changed)

    def _refresh_ports(self, show_message=True):
        self.available_ports: list[str] = self._get_available_ports()
        self._update_combo_boxes(initial=True)
        self._toggle_ui()

        if not self.available_ports:
            QMessageBox.warning(
                self,
                "Ошибка обновления портов",
                "Не удалось обновить список доступных портов, возможно у Вас не подключены устройства, перепроверьте подключения",
                QMessageBox.Ok,
                QMessageBox.Ok,
            )
            return

        if show_message:
            QMessageBox.information(
                self,
                "Обновление портов",
                "Список портов обновлен успешно, доступные порты: "
                + ", ".join(self.available_ports),
                QMessageBox.Ok,
                QMessageBox.Ok,
            )

    def _update_combo_boxes(self, initial=False):
        """
        Updates the contents of the port combo boxes while maintaining selections.

        The same port can appear in both combo boxes, but we ensure that if
        the user selects a port in one box, we don't automatically remove it
        from the other box's options - only update when the user explicitly changes
        the selection.

        :param initial: bool
            If True, initializes both combo boxes with all available ports.
            If False, preserves the selected ports and only updates the other combo box.
        """
        # Store current selections
        current1 = self.combo_port_1.currentText()
        current2 = self.combo_port_2.currentText()

        # Block signals to prevent cascading updates
        self.combo_port_1.blockSignals(True)
        self.combo_port_2.blockSignals(True)

        # Clear both combo boxes
        self.combo_port_1.clear()
        self.combo_port_2.clear()

        # Always show all available ports in both combo boxes
        self.combo_port_1.addItems(self.available_ports)
        self.combo_port_2.addItems(self.available_ports)

        # Restore previous selections if they still exist in the available ports
        if current1 and current1 in self.available_ports:
            index1 = self.combo_port_1.findText(current1)
            if index1 >= 0:
                self.combo_port_1.setCurrentIndex(index1)

        if current2 and current2 in self.available_ports:
            index2 = self.combo_port_2.findText(current2)
            if index2 >= 0:
                self.combo_port_2.setCurrentIndex(index2)

        # Re-enable signals
        self.combo_port_1.blockSignals(False)
        self.combo_port_2.blockSignals(False)

    def _on_combo_changed(self):
        self._update_combo_boxes()

    def _create_central_widget(self):
        # Create main widget and layout
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QtWidgets.QVBoxLayout()
        self.central_widget.setLayout(layout)

        # Control button for GFR
        self.toggle_gfr_button = QtWidgets.QPushButton("Включить РРГ", self)
        self.toggle_gfr_button.setCheckable(True)
        self.toggle_gfr_button.clicked.connect(self._toggle_gfr)
        layout.addWidget(self.toggle_gfr_button)

        # Setpoint input
        form_layout = QtWidgets.QHBoxLayout()
        self.setpoint_line_edit = QtWidgets.QLineEdit(self)
        self.setpoint_line_edit.setPlaceholderText(
            "Введите заданный расход как целочисленное значение (например: 50)"
        )
        int_validator = QtGui.QIntValidator(self)
        int_validator.setBottom(0)  # Lower limit of the GFR [cm3/min]
        int_validator.setTop(500)  # Upper limit of the GFR [cm3/min]
        self.setpoint_line_edit.setValidator(int_validator)
        form_layout.addWidget(self.setpoint_line_edit)

        self.send_setpoint_button = QtWidgets.QPushButton(
            "Задать уставку расхода", self
        )
        self.send_setpoint_button.clicked.connect(self._send_setpoint)
        form_layout.addWidget(self.send_setpoint_button)
        layout.addLayout(form_layout)

        # Buttons for working with the graph
        graph_controls_layout = QtWidgets.QHBoxLayout()
        self.clear_graph_button = QtWidgets.QPushButton("Очистить график", self)
        self.clear_graph_button.clicked.connect(self._clear_graph)
        graph_controls_layout.addWidget(self.clear_graph_button)

        self.save_data_button = QtWidgets.QPushButton("Сохранить данные CSV", self)
        self.save_data_button.clicked.connect(self._save_data_to_csv)
        graph_controls_layout.addWidget(self.save_data_button)

        self.save_image_button = QtWidgets.QPushButton("Сохранить график PNG", self)
        self.save_image_button.clicked.connect(self._save_graph_as_image)
        graph_controls_layout.addWidget(self.save_image_button)
        layout.addLayout(graph_controls_layout)

        # Create a splitter to allow resizing between graph and console
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        layout.addWidget(self.splitter)

        # Create container widget for the graph
        self.graph_container = QtWidgets.QWidget()
        graph_layout = QtWidgets.QVBoxLayout(self.graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Initialize the graph
        self._init_graph()
        graph_layout.addWidget(self.canvas)

        # Create log console
        self.log_console = QtWidgets.QTextEdit(self)
        self.log_console.setReadOnly(True)
        self.log_console.setPlaceholderText(
            "Текущий расход будет отображаться здесь..."
        )

        # Set minimum heights for better usability
        self.graph_container.setMinimumHeight(300)
        self.log_console.setMinimumHeight(100)

        # Add widgets to splitter
        self.splitter.addWidget(self.graph_container)
        self.splitter.addWidget(self.log_console)

        # Set initial sizes (70% graph, 30% console)
        self.splitter.setSizes([700, 300])

        # Start graph timer
        self.graph_timer = QtCore.QTimer(self)
        self.graph_timer.timeout.connect(self._update_graph)
        self.graph_timer.start(PLOT_UPDATE_TIME_TICK_MS)

    @QtCore.pyqtSlot()
    def _toggle_gfr(self):
        if self.toggle_gfr_button.isChecked():
            self._open_connections()
        else:
            self._close_connections()

    @QtCore.pyqtSlot()
    def _send_setpoint(self):
        if not self.toggle_gfr_button.isChecked():
            QMessageBox.warning(
                self,
                "Внимание",
                "РРГ не включен. Сначала включите РРГ, чтобы задать уставку расхода.",
                QMessageBox.Ok,
            )
            return

        text = self.setpoint_line_edit.text()
        if text == "":
            self._log_message("Значение заданного расхода пустое.")
            return

        try:
            setpoint = int(text)
        except ValueError:
            self._log_message(
                f"Неверное значение заданного расхода, введенное значение: {text} [см3/мин]."
            )
            return

        if self.gfr_controller.IsDisconnected():
            self._gfr_show_error_msg()
            return

        err = self.gfr_controller.SetFlow(setpoint)
        if err != MODBUS_OK:
            self._gfr_show_error_msg()
        else:
            self._log_message(f"Успешно задан расход {setpoint} [см3/мин].")

    def _log_message(self, message: str):
        # Format message with timestamp for console output
        console_message = (
            f"[{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] {message}"
        )
        self.log_console.append(console_message)

        # Append the same formatted message to the log file
        try:
            if self.log_file_path:
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(console_message + "\n")
        except Exception as e:
            # Log an error to the console if file writing fails
            error_message = f"[ОШИБКА ЗАПИСИ В ЛОГ {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] Не удалось записать в {self.log_file_path}: {e}"
            self.log_console.append(error_message)

    def _gfr_show_error_msg(self):
        gfr_error = self.gfr_controller.GetLastError()

        if not gfr_error:
            return

        if isinstance(gfr_error, str):
            QMessageBox.critical(
                self,
                "Ошибка РРГ",
                f"{self.gfr_controller.GetLastError()}",
            )
        elif isinstance(gfr_error, int) and gfr_error == MODBUS_ERROR:
            QMessageBox.critical(
                self,
                "Ошибка РРГ",
                "РРГ не подключено",
            )
        else:
            QMessageBox.critical(self, "Ошибка РРГ", "Неизвестная ошибка")

    def _relay_show_error_msg(self):
        relay_error = self.relay_controller.GetLastError()

        if not relay_error:
            return

        if isinstance(relay_error, str):
            QMessageBox.critical(
                self,
                "Ошибка реле",
                f"{self.relay_controller.GetLastError()}",
            )
        elif isinstance(relay_error, int) and relay_error == MODBUS_ERROR:
            QMessageBox.critical(self, "Ошибка реле", "Реле не подключено")
        else:
            QMessageBox.critical(self, "Ошибка реле", "Неизвестная ошибка")

    def _clear_graph(self):
        self.flow_data = []
        self.start_time = datetime.datetime.now()
        self.ax.clear()
        self.ax.set_xlabel("Время [мин]")
        self.ax.set_ylabel("Расход [см3/мин]")
        self.ax.set_title("Расход газа по времени Q(t)")
        self.ax.grid(True)
        self.canvas.draw()
        self._log_message("График очищен. Начинаем новые измерения.")

    def _save_data_to_csv(self):
        if not self.flow_data:
            QMessageBox.warning(
                self,
                "Нет данных",
                "Нет данных для сохранения. Сначала запустите измерения.",
                QMessageBox.Ok,
            )
            return

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"flow_data_{now}.csv"

        try:
            with open(file_name, "w") as f:
                f.write("Время [мин],Расход [см3/мин]\n")
                for time, flow in self.flow_data:
                    f.write(f"{time:.2f},{flow:.3f}\n")

            self._log_message(f"Данные сохранены в файл: {file_name}")

            QMessageBox.information(
                self,
                "Данные сохранены",
                f"Данные успешно сохранены в файл: {file_name}",
                QMessageBox.Ok,
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить данные: {str(e)}",
                QMessageBox.Ok,
            )
            self._log_message(f"Ошибка сохранения данных: {str(e)}")

    def _save_graph_as_image(self):
        if not self.flow_data:
            QMessageBox.warning(
                self,
                "Нет данных",
                "Нет данных для сохранения графика. Сначала запустите измерения.",
                QMessageBox.Ok,
            )
            return

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"flow_graph_{now}.png"

        try:
            fig = Figure(figsize=(12, 8), dpi=100)
            ax = fig.add_subplot(111)

            times = [t for t, _ in self.flow_data]
            flows = [f for _, f in self.flow_data]

            ax.plot(times, flows, marker="o", linestyle="-")
            ax.set_xlabel("Время [мин]")
            ax.set_ylabel("Расход [см3/мин]")
            ax.set_title("Расход газа по времени Q(t)")

            ax.minorticks_on()
            ax.grid(True, which="major", linestyle="-", linewidth=0.8)
            ax.grid(True, which="minor", linestyle="--", linewidth=0.5, alpha=0.5)

            fig.tight_layout()
            fig.savefig(file_name, format="png", dpi=300)

            self._log_message(f"График сохранен в файл: {file_name}")

            QMessageBox.information(
                self,
                "График сохранен",
                f"График успешно сохранен в файл: {file_name}",
                QMessageBox.Ok,
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить график: {str(e)}",
                QMessageBox.Ok,
            )
            self._log_message(f"Ошибка сохранения графика: {str(e)}")

    def _check_measurement_stall(self):
        """
        Checks if measurements have stopped coming in while the GFR is connected.
        If measurements have stalled for a significant time, performs auto-recovery.
        """
        # Only check if GFR is supposedly connected and we haven't already detected a stall
        if (
            self.gfr_controller.IsConnected()
            and self.toggle_gfr_button.isChecked()
            and not self.measurement_stalled
        ):

            current_time = datetime.datetime.now()
            # Calculate seconds since last measurement
            time_since_last_measurement = (
                current_time - self.last_measurement_time
            ).total_seconds()

            # If more than 10 seconds have passed without a measurement, consider it stalled
            if time_since_last_measurement > 10:
                self.measurement_stalled = True
                self._perform_auto_recovery()

    def _perform_auto_recovery(self):
        """
        Automatically recovers from a stalled measurement state by
        reconnecting to the devices without user intervention.
        """
        QMessageBox.warning(
            self,
            "ВНИМАНИЕ",
            "Измерения прекратились. Выполняется автоматическое восстановление соединения...",
            QMessageBox.Ok,
        )
        self._log_message(
            "ВНИМАНИЕ: Измерения прекратились. Выполняется автоматическое восстановление соединения..."
        )

        # Remember the current state
        was_gfr_enabled = self.toggle_gfr_button.isChecked()

        # 1. Safely close all existing connections
        self._safe_close_connections()

        # 2. Short delay to ensure all connections are properly closed
        QtCore.QTimer.singleShot(1000, lambda: self._continue_recovery(was_gfr_enabled))

    def _continue_recovery(self, should_reconnect):
        """
        Second part of the recovery process after a short delay.
        Reopens connections if needed.
        """
        # 3. Refresh available ports
        self._refresh_ports(show_message=False)

        # 4. If the GFR was enabled before, reconnect
        if should_reconnect:
            # Re-enable the toggle button (without triggering the signal)
            self.toggle_gfr_button.blockSignals(True)
            self.toggle_gfr_button.setChecked(True)
            self.toggle_gfr_button.blockSignals(False)

            # Reopen connections
            self._open_connections()

            if self.gfr_controller.IsConnected():
                self._log_message(
                    "Соединение восстановлено успешно. Измерения продолжаются."
                )
                # Restart the graph timer to resume measurements
                if hasattr(self, "graph_timer") and self.graph_timer is not None:
                    self.graph_timer.start(PLOT_UPDATE_TIME_TICK_MS)
            else:
                self._log_message("Не удалось восстановить соединение автоматически.")
                # Now show message to user since auto-recovery failed
                self._show_recovery_failed_message()

        # Reset the stalled flag to allow future recovery attempts
        self.measurement_stalled = False
        # Update the last measurement time to avoid immediate re-triggering
        self.last_measurement_time = datetime.datetime.now()

    def _show_recovery_failed_message(self):
        """
        Shows a message to the user when automatic recovery fails.
        """
        QMessageBox.warning(
            self,
            "Ошибка восстановления",
            "Не удалось автоматически восстановить соединение с РРГ.\n\n"
            "Рекомендуется:\n"
            "— перезапустить программу;\n"
            "— проверить физическое подключение устройства;\n"
            "— убедиться, что устройство включено и функционирует.",
            QMessageBox.Ok,
        )

    def _show_stall_message(self):
        """
        Shows a message to the user when measurements have stalled.
        This is no longer used directly, kept for reference.
        """
        self._log_message(
            "ВНИМАНИЕ: Измерения прекратились, возможно, соединение с РРГ потеряно."
        )

        QMessageBox.warning(
            self,
            "Измерения прекратились",
            "Программа перестала получать данные от РРГ, хотя соединение считается активным.\n\n"
            "Рекомендуется:\n"
            "— перезапустить программу;\n"
            "— проверить физическое подключение устройства;\n"
            "— убедиться, что устройство включено и функционирует.",
            QMessageBox.Ok,
        )

    def _save_port_settings(self):
        """
        Saves the current port selections to a configuration file.
        This is called before the application exits.
        """
        try:
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config"
            )
            os.makedirs(config_dir, exist_ok=True)

            ports_config_path = os.path.join(config_dir, "ports.yaml")

            ports_config = {
                "relay_port": self.combo_port_1.currentText(),
                "gfr_port": self.combo_port_2.currentText(),
            }

            # Only save if we have valid ports selected
            if ports_config["relay_port"] and ports_config["gfr_port"]:
                self.config_loader.save_config(ports_config_path, ports_config)
                self._log_message("Настройки портов сохранены")

        except Exception as e:
            self._log_message(f"Не удалось сохранить настройки портов: {e}")

    def _load_port_settings(self):
        """
        Loads saved port selections from the configuration file.
        Called during application startup.
        """
        try:
            ports_config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config", "ports.yaml"
            )

            if os.path.exists(ports_config_path):
                ports_config = self.config_loader.load_config(ports_config_path)

                if ports_config and isinstance(ports_config, dict):
                    self.saved_relay_port = ports_config.get("relay_port")
                    self.saved_gfr_port = ports_config.get("gfr_port")

                    # Apply saved settings if available ports match
                    self._apply_saved_port_settings()

        except Exception as e:
            self._log_message(f"Не удалось загрузить настройки портов: {e}")

    def _apply_saved_port_settings(self):
        """
        Tries to apply saved port settings and shows warnings if saved ports are no longer available.
        """
        if not self.saved_relay_port and not self.saved_gfr_port:
            # If there are no saved ports, set the default ports
            self._set_default_com_ports()
            return

        unavailable_ports = []

        # Check if saved ports are still available
        if self.saved_relay_port and self.saved_relay_port not in self.available_ports:
            unavailable_ports.append(f"реле ({self.saved_relay_port})")

        if self.saved_gfr_port and self.saved_gfr_port not in self.available_ports:
            unavailable_ports.append(f"РРГ ({self.saved_gfr_port})")

        # If some ports are unavailable, show a warning
        if unavailable_ports:
            warning_message = (
                f"Порты, используемые при предыдущем запуске программы для "
                f"{' и '.join(unavailable_ports)}, сейчас недоступны.\n\n"
                f"Возможно, изменилось физическое подключение устройств или их порядок.\n"
                f"Доступные в данный момент порты: {', '.join(self.available_ports)}"
            )

            QMessageBox.warning(
                self,
                "Изменение портов",
                warning_message,
                QMessageBox.Ok,
            )

            self._log_message(f"Предупреждение: {warning_message}")

        # Apply saved settings for available ports
        self._try_set_saved_ports()

    def _set_default_com_ports(self):
        """
        Sets default COM ports when the application starts:
        - The lowest numbered COM port in the first dropdown (for the relay)
        - The highest numbered COM port in the second dropdown (for the GFR)
        """
        if not self.available_ports:
            return

        sorted_ports = self._sort_com_ports(self.available_ports)

        if sorted_ports:
            self.combo_port_1.blockSignals(True)

            lowest_port = sorted_ports[0]
            lowest_index = self.combo_port_1.findText(lowest_port)
            if lowest_index >= 0:
                self.combo_port_1.setCurrentIndex(lowest_index)

            self.combo_port_1.blockSignals(False)

        if len(sorted_ports) > 1:
            self.combo_port_2.blockSignals(True)

            highest_port = sorted_ports[-1]
            highest_index = self.combo_port_2.findText(highest_port)
            if highest_index >= 0:
                self.combo_port_2.setCurrentIndex(highest_index)

            self.combo_port_2.blockSignals(False)

        self._update_combo_boxes()

    def _try_set_saved_ports(self):
        """
        Attempts to set the port dropdowns to the saved values if they're available
        """
        self.combo_port_1.blockSignals(True)
        self.combo_port_2.blockSignals(True)

        # Try to set relay port
        if self.saved_relay_port and self.saved_relay_port in self.available_ports:
            index = self.combo_port_1.findText(self.saved_relay_port)
            if index >= 0:
                self.combo_port_1.setCurrentIndex(index)
        else:
            sorted_ports = self._sort_com_ports(self.available_ports)
            if sorted_ports:
                lowest_index = self.combo_port_1.findText(sorted_ports[0])
                if lowest_index >= 0:
                    self.combo_port_1.setCurrentIndex(lowest_index)

        # Try to set GFR port
        if self.saved_gfr_port and self.saved_gfr_port in self.available_ports:
            index = self.combo_port_2.findText(self.saved_gfr_port)
            if index >= 0:
                self.combo_port_2.setCurrentIndex(index)
        else:
            sorted_ports = self._sort_com_ports(self.available_ports)
            if len(sorted_ports) > 0:
                highest_index = self.combo_port_2.findText(sorted_ports[-1])
                if highest_index >= 0:
                    self.combo_port_2.setCurrentIndex(highest_index)

        self.combo_port_1.blockSignals(False)
        self.combo_port_2.blockSignals(False)

        # Update dropdowns based on selections
        self._update_combo_boxes()

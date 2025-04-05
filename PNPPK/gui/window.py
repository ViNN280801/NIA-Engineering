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


RELAY_DEFAULT_BAUDRATE = 9600
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

PLOT_UPDATE_TIME_TICK_MS = 50


class GFRControlWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Панель управления РРГ")
        self.resize(1200, 700)

        self.gfr_controller = GFRController()
        self.relay_controller = RelayController()
        self.config_loader = YAMLConfigLoader()

        self.available_ports: list[str] = self._get_available_ports()

        self._create_toolbar()
        self._create_central_widget()

        self.close_shortcut_w = QShortcut(self)
        self.close_shortcut_w.setKey(QKeySequence("Ctrl+W"))
        self.close_shortcut_w.activated.connect(self._confirm_close)

        self.close_shortcut_q = QShortcut(self)
        self.close_shortcut_q.setKey(QKeySequence("Ctrl+Q"))
        self.close_shortcut_q.activated.connect(self._confirm_close)

        self._disable_ui()
        self._load_config_data()

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
            self._close_connections()
            event.accept()
        else:
            event.ignore()

    def _init_graph(self):
        """Initializes the Matplotlib graph for displaying flow over time."""
        self.figure = Figure(figsize=(20, 10))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(500)
        self.ax = self.figure.add_subplot(111)

        self.ax.set_xlabel("Время [мин]")
        self.ax.set_ylabel("Расход [см3/мин]")
        self.ax.set_title("Расход газа по времени Qm(t)")

        self.flow_data = []  # Stores (time in minutes, flow)
        self.start_time = datetime.datetime.now()  # Set start time for reference

        central_widget = self.centralWidget()
        if central_widget is not None:
            layout = central_widget.layout()
            if layout is not None:
                layout.addWidget(self.canvas)
            else:
                raise ValueError("DEBUG: Layout is None, cannot add graph")
        else:
            raise ValueError("DEBUG: Central widget is None, cannot add graph")

    def _update_graph(self):
        """
        Queries the current flow from the GFR controller, appends the data point,
        and updates the Matplotlib graph.
        """
        if self.gfr_controller.IsDisconnected():
            return

        err, flow = self.gfr_controller.GetFlow()
        current_time = datetime.datetime.now()
        elapsed_minutes = (
            current_time - self.start_time
        ).total_seconds() / 60  # Convert to minutes

        if err == MODBUS_OK:
            self.flow_data.append((elapsed_minutes, flow))
            self.flow_data = self.flow_data[-60:]  # Keep only last 60 data points

            times = [t for t, _ in self.flow_data]
            flows = [f for _, f in self.flow_data]

            self.ax.clear()
            self.ax.plot(times, flows, marker="o", linestyle="-")

            self.ax.set_xlabel("Время [мин]")
            self.ax.set_ylabel("Расход [см3/мин]")
            self.ax.set_title("Расход газа по времени Qm(t)")

            self.ax.minorticks_on()
            self.ax.grid(True, which="major", linestyle="-", linewidth=0.8)
            self.ax.grid(True, which="minor", linestyle="--", linewidth=0.5, alpha=0.5)

            if hasattr(self, "canvas"):
                self.canvas.draw()

            self._log_message(
                f"Текущий расход: {flow} [см3/мин] в момент времени {elapsed_minutes:.2f} [мин]"
            )
        else:
            self._gfr_show_error_msg()

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
            self._close_connections()
            QtWidgets.QApplication.quit()

    def _open_connections(self):
        # 1. Connect to the relay
        relay_port = self.combo_port_1.currentText()
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
            self._relay_show_error_msg()
            return
        else:
            self._log_message(f"Реле подключено к порту {relay_port}.")

        # 2. Connect to the Gas Flow Regulator
        gfr_port = self.combo_port_2.currentText()
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

    def _close_connections(self):
        """
        Safely closes the connections for the Gas Flow Regulator and Relay devices.
        This method calls the appropriate TurnOff/close methods on the controllers.
        """
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

    def _load_config_data(self):
        gfr_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "gfr.yaml"
        )
        relay_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "relay.yaml"
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

            self._log_message(
                f"Конфигурация загружена успешно из файлов: [{gfr_config_path}; {relay_config_path}]. Параметры конфигурации:"
            )
            self._log_message(
                f"РРГ:\nBaudrate: {self.gfr_baudrate} [бит/с]\n"
                f"Parity: {self.gfr_parity}\n"
                f"Data bit: {self.gfr_data_bit}\n"
                f"Stop bit: {self.gfr_stop_bit}\n"
                f"Slave ID: {self.gfr_slave_id}\n"
                f"Timeout: {self.gfr_timeout} [мс]"
            )
            self._log_message(
                f"\nРеле:\nBaudrate: {self.relay_baudrate} [бит/с]\n"
                f"Parity: {self.relay_parity}\n"
                f"Data bit: {self.relay_data_bit}\n"
                f"Stop bit: {self.relay_stop_bit}\n"
                f"Slave ID: {self.relay_slave_id}\n"
                f"Timeout: {self.relay_timeout} [мс]"
            )
        except Exception as e:
            self._log_message(f"Не удалось загрузить конфигурацию: {e}")

    def _get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        available = [port.device for port in ports]
        return available

    def _disable_ui(self):
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
            "Вы можете посмотреть в мененджер устройств, для этого наберите "
            'в поиске "Менеджер устройств" -> "COM-порты". Там Вы увидите '
            "все устройства и их COM-порты."
        )
        self.toolbar.addWidget(self.combo_port_1)

        self.toolbar.addSeparator()

        self.combo_port_2 = QtWidgets.QComboBox(self)
        self.combo_port_2.setToolTip(
            "Выберите COM-порт для РРГ. Чтобы не перепутать COM-порты, "
            "Вы можете посмотреть в мененджер устройств, для этого наберите "
            'в поиске "Менеджер устройств" -> "COM-порты". Там Вы увидите '
            "все устройства и их COM-порты."
        )
        self.toolbar.addWidget(self.combo_port_2)

        self.refresh_ports_button = QtWidgets.QPushButton("Обновить порты", self)
        self.refresh_ports_button.setToolTip(
            "Данная кнопка обновляет список доступных портов"
        )
        self.toolbar.addWidget(self.refresh_ports_button)
        self.refresh_ports_button.clicked.connect(self._refresh_ports)

        self._update_combo_boxes(initial=True)

        self.combo_port_1.currentIndexChanged.connect(self._on_combo_changed)
        self.combo_port_2.currentIndexChanged.connect(self._on_combo_changed)

    def _refresh_ports(self):
        self.available_ports: list[str] = self._get_available_ports()
        self._update_combo_boxes(initial=True)

        if not self.available_ports:
            QMessageBox.warning(
                self,
                "Ошибка обновления портов",
                "Не удалось обновить список доступных портов, возможно у Вас не подключены устройства, перепроверьте подключения",
                QMessageBox.Ok,
                QMessageBox.Ok,
            )
            return

        QMessageBox.information(
            self,
            "Обновление портов",
            "Список портов обновлен успешно, доступные порты: "
            + ", ".join(self.available_ports),
            QMessageBox.Ok,
            QMessageBox.Ok,
        )

    def _update_combo_boxes(self, initial=False):
        current1 = self.combo_port_1.currentText()
        current2 = self.combo_port_2.currentText()

        self.combo_port_1.blockSignals(True)
        self.combo_port_2.blockSignals(True)

        self.combo_port_1.clear()
        self.combo_port_2.clear()

        ports_for_combo1 = list(self.available_ports)
        ports_for_combo2 = list(self.available_ports)
        if not initial:
            if current2 in ports_for_combo1:
                ports_for_combo1.remove(current2)
            if current1 in ports_for_combo2:
                ports_for_combo2.remove(current1)

        self.combo_port_1.addItems(ports_for_combo1)
        self.combo_port_2.addItems(ports_for_combo2)

        if current1 in ports_for_combo1:
            self.combo_port_1.setCurrentIndex(ports_for_combo1.index(current1))
        if current2 in ports_for_combo2:
            self.combo_port_2.setCurrentIndex(ports_for_combo2.index(current2))

        self.combo_port_1.blockSignals(False)
        self.combo_port_2.blockSignals(False)

    def _on_combo_changed(self):
        self._update_combo_boxes()

    def _create_central_widget(self):
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QtWidgets.QVBoxLayout()
        self.central_widget.setLayout(layout)

        self.toggle_gfr_button = QtWidgets.QPushButton("Включить РРГ", self)
        self.toggle_gfr_button.setCheckable(True)
        self.toggle_gfr_button.clicked.connect(self._toggle_gfr)
        layout.addWidget(self.toggle_gfr_button)

        form_layout = QtWidgets.QHBoxLayout()

        self.setpoint_line_edit = QtWidgets.QLineEdit(self)
        self.setpoint_line_edit.setPlaceholderText(
            "Введите заданный расход в дробной форме (например: 50.5)"
        )
        double_validator = QtGui.QDoubleValidator(self)
        self.setpoint_line_edit.setValidator(double_validator)
        form_layout.addWidget(self.setpoint_line_edit)

        self.send_setpoint_button = QtWidgets.QPushButton(
            "Отправить заданный расход", self
        )
        self.send_setpoint_button.clicked.connect(self._send_setpoint)
        form_layout.addWidget(self.send_setpoint_button)

        layout.addLayout(form_layout)

        # --- Initialize the graph ---
        self._init_graph()
        self.graph_timer = QtCore.QTimer(self)
        self.graph_timer.timeout.connect(self._update_graph)
        self.graph_timer.start(PLOT_UPDATE_TIME_TICK_MS)

        self.log_console = QtWidgets.QTextEdit(self)
        self.log_console.setReadOnly(True)
        self.log_console.setPlaceholderText(
            "Текущий расход будет отображаться здесь..."
        )
        layout.addWidget(self.log_console)

    @QtCore.pyqtSlot()
    def _toggle_gfr(self):
        if self.toggle_gfr_button.isChecked():
            self._open_connections()
        else:
            self._close_connections()

    @QtCore.pyqtSlot()
    def _send_setpoint(self):
        text = self.setpoint_line_edit.text()
        if text == "":
            self._log_message("Значение заданного расхода пустое.")
            return

        try:
            setpoint = float(text)
        except ValueError:
            self._log_message("Неверное значение заданного расхода.")
            return

        if self.gfr_controller.IsDisconnected():
            self._gfr_show_error_msg()
            return

        err = self.gfr_controller.SetFlow(setpoint)
        if err != MODBUS_OK:
            self._gfr_show_error_msg()
        else:
            self._log_message(f"Заданный расход {setpoint} отправлен успешно.")

    def _log_message(self, message: str):
        self.log_console.append(message)

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
                "Ошибка РРГ",
                f"{self.relay_controller.GetLastError()}",
            )
        elif isinstance(relay_error, int) and relay_error == MODBUS_ERROR:
            QMessageBox.critical(self, "Ошибка РРГ", "Реле не подключено")
        else:
            QMessageBox.critical(self, "Ошибка РРГ", "Неизвестная ошибка")

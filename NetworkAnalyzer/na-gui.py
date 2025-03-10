import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QMessageBox,
    QToolButton,
    QTabWidget,
    QFileDialog,
    QComboBox,
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QTimer
from network_analyzer import NetworkUsageAnalyzer, NetworkSpeedAnalyzer
from util import GraphPlotter, I18N


class QTextEditLogger(logging.Handler):
    """
    A custom logging handler that outputs log messages to a QTextEdit widget.

    Attributes:
        text_edit (QTextEdit): The QTextEdit widget where log messages are displayed.
    """

    def __init__(self, text_edit):
        """
        Initialize the QTextEditLogger with a QTextEdit widget.

        Args:
            text_edit (QTextEdit): The QTextEdit widget where log messages will be displayed.
        """
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        """
        Emit a log record.

        Args:
            record (LogRecord): The log record to be emitted.
        """
        msg = self.format(record)
        self.text_edit.append(msg)


class NetworkAnalyzerGUI(QWidget):
    """
    Main GUI class for the Network Analyzer application.

    Attributes:
        analysis_duration (int): Duration of the analysis in minutes.
        analyze_speed (bool): Whether to analyze speed.
        analyze_usage (bool): Whether to analyze network usage.
        frequency (int): Frequency of measurements in minutes.
        xtick_interval (int): Interval for X-ticks in graphs.
        infinite_analysis (bool): Whether to perform analysis indefinitely.
        speed_timer (QTimer): Timer for speed analysis tasks.
        usage_timer (QTimer): Timer for usage analysis tasks.
        speed_logger (Logger): Logger for speed analysis.
        usage_logger (Logger): Logger for usage analysis.
        speed_analyzer (NetworkSpeedAnalyzer): Analyzer for network speed.
        usage_analyzer (NetworkUsageAnalyzer): Analyzer for network usage.
        plotter (GraphPlotter): Plotter for generating graphs from analysis data.
    """

    def __init__(self, lang="en"):
        """
        Initialize the NetworkAnalyzerGUI with default settings.
        """
        super().__init__()

        self.language = lang
        self.i18n = I18N(lang)

        self.analysis_duration = 60
        self.analyze_speed = True
        self.analyze_usage = True
        self.frequency = 1
        self.xtick_interval = 5
        self.infinite_analysis = False

        self.speed_timer = QTimer()
        self.usage_timer = QTimer()

        self.plotter = GraphPlotter(None, None)

        self.initUI()

    def initUI(self):
        try:
            self.setWindowTitle("Network Analyzer")
            self.setGeometry(100, 100, 800, 600)
            self.setWindowIcon(QIcon("imgs/na.ico"))

            self.tabs = QTabWidget()
            self.settings_tab = QWidget()
            self.plots_tab = QWidget()

            self.tabs.addTab(self.settings_tab, self.i18n.get("settings_tab"))
            self.tabs.addTab(self.plots_tab, self.i18n.get("plots_tab"))

            layout = QVBoxLayout()

            self.lang_label = QLabel()
            self.lang_label.setText(self.i18n.get("menu_change_language"))
            layout.addWidget(self.lang_label)
            
            self.language_combo = QComboBox()
            self.language_combo.addItem("English", "en")
            self.language_combo.addItem("Русский", "ru")
            self.language_combo.currentIndexChanged.connect(self.change_language)
            layout.addWidget(self.language_combo)

            layout.addWidget(self.tabs)
            self.setLayout(layout)

            self.initSettingsTab()
            self.initPlotsTab()
        except Exception as e:
            QMessageBox.critical(
                self,
                self.i18n.get("internal_error"),
                f"{self.i18n.get('internal_error_occurred')}: {e}",
            )
            logging.error(f"{self.i18n.get('internal_error_occurred')}: {e}")

    def change_language(self):
        self.language = self.language_combo.currentData()
        self.i18n = I18N(self.language)
        QMessageBox.information(self, self.i18n.get("menu_change_language"), f"Language changed to {self.language_combo.currentText()}")
        self.retranslate_ui()

    def retranslate_ui(self):
        self.lang_label.setText(self.i18n.get("menu_change_language"))
        self.infinite_checkbox.setText(self.i18n.get("infinite_analysis"))
        self.duration_label.setText(self.i18n.get("analysis_duration"))
        self.speed_checkbox.setText(self.i18n.get("analyze_speed"))
        self.usage_checkbox.setText(self.i18n.get("analyze_usage"))
        self.frequency_label.setText(self.i18n.get("measurement_frequency"))
        self.xtick_label.setText(self.i18n.get("xtick_interval"))
        self.start_button.setText(self.i18n.get("start_analysis"))
        self.stop_button.setText(self.i18n.get("stop_analysis"))
        self.select_files_button.setText(self.i18n.get("select_files"))
        self.clear_plots_button.setText(self.i18n.get("clear_plots"))
        self.tabs.setTabText(self.tabs.indexOf(self.settings_tab), self.i18n.get("settings_tab"))
        self.tabs.setTabText(self.tabs.indexOf(self.plots_tab), self.i18n.get("plots_tab"))
    
    def initSettingsTab(self):
        """
        Initialize the Settings tab.
        """
        try:
            layout = QVBoxLayout()

            # Infinite analysis checkbox
            infinite_layout = QHBoxLayout()
            self.infinite_checkbox = QCheckBox("Infinite analysis")
            self.infinite_checkbox.stateChanged.connect(self.toggle_infinite_analysis)
            infinite_button = self.create_help_button("Perform analysis indefinitely.")
            infinite_layout.addWidget(self.infinite_checkbox)
            infinite_layout.addWidget(infinite_button)
            layout.addLayout(infinite_layout)

            # Analysis duration input
            duration_layout = QHBoxLayout()
            self.duration_label = QLabel("Analysis Duration (minutes):")
            self.duration_input = QSpinBox()
            self.duration_input.setRange(1, 1440)
            self.duration_input.setValue(self.analysis_duration)
            duration_button = self.create_help_button(
                "Set the duration of analysis in minutes. (1-1440)"
            )
            duration_layout.addWidget(self.duration_label)
            duration_layout.addWidget(self.duration_input)
            duration_layout.addWidget(duration_button)
            layout.addLayout(duration_layout)

            # Analyze speed checkbox
            speed_layout = QHBoxLayout()
            self.speed_checkbox = QCheckBox("Analyze speed")
            self.speed_checkbox.setChecked(self.analyze_speed)
            speed_button = self.create_help_button(
                "Enable to analyze download and upload speed."
            )
            speed_layout.addWidget(self.speed_checkbox)
            speed_layout.addWidget(speed_button)
            layout.addLayout(speed_layout)

            # Analyze usage checkbox
            usage_layout = QHBoxLayout()
            self.usage_checkbox = QCheckBox("Analyze network usage")
            self.usage_checkbox.setChecked(self.analyze_usage)
            usage_button = self.create_help_button(
                "Enable to analyze network data usage."
            )
            usage_layout.addWidget(self.usage_checkbox)
            usage_layout.addWidget(usage_button)
            layout.addLayout(usage_layout)

            # Frequency input
            frequency_layout = QHBoxLayout()
            self.frequency_label = QLabel("Frequency of measurements (minutes):")
            self.frequency_input = QSpinBox()
            self.frequency_input.setRange(1, 60)
            self.frequency_input.setValue(self.frequency)
            frequency_button = self.create_help_button(
                "Set the frequency of measurements in minutes. (1-60)"
            )
            frequency_layout.addWidget(self.frequency_label)
            frequency_layout.addWidget(self.frequency_input)
            frequency_layout.addWidget(frequency_button)
            layout.addLayout(frequency_layout)

            # X-tick interval input
            xtick_layout = QHBoxLayout()
            self.xtick_label = QLabel("X-Tick Interval for Graphs:")
            self.xtick_input = QSpinBox()
            self.xtick_input.setRange(1, 10)
            self.xtick_input.setValue(self.xtick_interval)
            xtick_button = self.create_help_button(
                "Set the interval for X-ticks in graphs. (1-10)"
            )
            xtick_layout.addWidget(self.xtick_label)
            xtick_layout.addWidget(self.xtick_input)
            xtick_layout.addWidget(xtick_button)
            layout.addLayout(xtick_layout)

            # Start and Stop buttons
            buttons_layout = QHBoxLayout()
            self.start_button = QPushButton("Start Analysis")
            self.start_button.clicked.connect(self.start_analysis)
            self.stop_button = QPushButton("Stop Analysis")
            self.stop_button.clicked.connect(self.stop_analysis)
            self.stop_button.setEnabled(False)  # Initially disabled
            buttons_layout.addWidget(self.start_button)
            buttons_layout.addWidget(self.stop_button)
            layout.addLayout(buttons_layout)

            # Log output
            self.log_output = QTextEdit()
            self.log_output.setReadOnly(True)
            layout.addWidget(self.log_output)

            self.log_handler = QTextEditLogger(self.log_output)
            self.log_handler.setFormatter(
                logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
            )
            logging.getLogger().addHandler(self.log_handler)
            logging.getLogger().setLevel(
                logging.INFO
            )  # Ensure root logger level is set

            self.settings_tab.setLayout(layout)
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during initSettingsTab: {e}")

    def set_fields_enabled(self, enabled):
        """
        Enable or disable all input fields and checkboxes.

        Args:
            enabled (bool): True to enable fields, False to disable.
        """
        self.infinite_checkbox.setEnabled(enabled)
        self.duration_input.setEnabled(enabled and not self.infinite_analysis)
        self.speed_checkbox.setEnabled(enabled)
        self.usage_checkbox.setEnabled(enabled)
        self.frequency_input.setEnabled(enabled)
        self.xtick_input.setEnabled(enabled)
        self.select_files_button.setEnabled(enabled)
        self.clear_plots_button.setEnabled(enabled)

    def initPlotsTab(self):
        """
        Initialize the Plots tab.
        """
        try:
            layout = QVBoxLayout()

            # Select files button
            self.select_files_button = QPushButton("Select Files")
            self.select_files_button.clicked.connect(self.select_files)
            layout.addWidget(self.select_files_button)

            # Clear plots button
            self.clear_plots_button = QPushButton("Clear")
            self.clear_plots_button.clicked.connect(self.clear_plots)
            layout.addWidget(self.clear_plots_button)

            # Placeholder for plot area
            self.plot_area = QTabWidget()
            layout.addWidget(self.plot_area)

            self.plots_tab.setLayout(layout)
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during initPlotsTab: {e}")

    def clear_plots(self):
        """
        Clear all plots from the plot area.
        """
        try:
            self.plot_area.clear()
            self.log_message("All plots have been cleared.")
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during clear_plots: {e}")

    def create_help_button(self, tooltip_text):
        """
        Create a help button with a tooltip.

        Args:
            tooltip_text (str): The text to display in the tooltip.

        Returns:
            QToolButton: A tool button with the specified tooltip.
        """
        button = QToolButton(self)
        button.setText("?")
        button.setFont(QFont("Arial", 10, QFont.Bold))
        button.setStyleSheet(
            """
            QToolButton {
                border: 1px solid black;
                border-radius: 10px;
                background-color: lightgray;
                min-width: 20px;
                min-height: 20px;
            }
            """
        )
        button.setToolTip(tooltip_text)
        button.setEnabled(False)
        return button

    def toggle_infinite_analysis(self):
        """
        Toggle the infinite analysis setting based on the checkbox state.
        """
        self.infinite_analysis = self.infinite_checkbox.isChecked()
        self.duration_label.setEnabled(not self.infinite_analysis)
        self.duration_input.setEnabled(not self.infinite_analysis)

    def start_analysis(self):
        """
        Start the network analysis based on the user settings.
        """
        try:
            self.analysis_duration = self.duration_input.value()
            self.analyze_speed = self.speed_checkbox.isChecked()
            self.analyze_usage = self.usage_checkbox.isChecked()
            self.frequency = self.frequency_input.value()
            self.xtick_interval = self.xtick_input.value()

            if not self.analyze_speed and not self.analyze_usage:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Please enable at least one of speed or usage analysis.",
                )
                self.speed_checkbox.setStyleSheet("background-color: lightblue")
                self.usage_checkbox.setStyleSheet("background-color: lightblue")
                return

            if self.frequency > self.analysis_duration and not self.infinite_analysis:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Frequency cannot be greater than the analysis duration.",
                )
                return

            self.log_output.clear()
            self.log_message("Starting analysis...")

            # Disable fields during analysis
            self.set_fields_enabled(False)

            # Initialize loggers and analyzers
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            if not os.path.exists("logs"):
                os.makedirs("logs")
            if not os.path.exists("results"):
                os.makedirs("results")

            speed_csv_file = None
            usage_csv_file = None

            if self.analyze_speed:
                speed_log_file = os.path.join("logs", f"{now}_speed.log")
                speed_csv_file = os.path.join("results", f"{now}_speed_measurement.csv")
                self.speed_logger = self.setup_logger("speed", speed_log_file)
                self.speed_analyzer = NetworkSpeedAnalyzer(
                    speed_csv_file, self.speed_logger
                )
                self.speed_timer.timeout.connect(self.speed_job)
                self.speed_timer.start(
                    self.frequency * 60 * 1000
                )  # frequency in minutes

            if self.analyze_usage:
                usage_log_file = os.path.join("logs", f"{now}_data_usage.log")
                usage_csv_file = os.path.join("results", f"{now}_network_usage.csv")
                self.usage_logger = self.setup_logger("usage", usage_log_file)
                self.usage_analyzer = NetworkUsageAnalyzer(
                    usage_csv_file, self.usage_logger
                )
                self.usage_timer.timeout.connect(self.usage_job)
                self.usage_timer.start(
                    self.frequency * 60 * 1000
                )  # frequency in minutes

            self.plotter = GraphPlotter(
                usage_csv_file if self.analyze_usage else None,
                speed_csv_file if self.analyze_speed else None,
            )

            if self.usage_logger:
                self.usage_logger.info(
                    f"Network Usage Analyzer: Starting the analysis..."
                )
            if self.speed_logger:
                self.speed_logger.info(
                    f"Network Speed Analyzer: Starting the analysis..."
                )

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            if not self.infinite_analysis:
                QTimer.singleShot(
                    self.analysis_duration * 60 * 1000, self.stop_analysis
                )
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during start_analysis: {e}")
            self.set_fields_enabled(True)  # Re-enable fields in case of error

    def stop_analysis(self):
        """
        Stop the ongoing network analysis.
        """
        try:
            self.log_message("Stopping analysis...")
            if self.speed_timer.isActive():
                self.speed_timer.stop()
            if self.usage_timer.isActive():
                self.usage_timer.stop()
            self.plotter.plot_graphs(self.xtick_interval)
            self.log_message("Analysis stopped and graphs plotted.")

            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

            # Re-enable fields after analysis
            self.set_fields_enabled(True)
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during stop_analysis: {e}")

    def speed_job(self):
        """
        Perform a speed analysis job.
        """
        try:
            download_speed, upload_speed = self.speed_analyzer.measure_speed()
            if download_speed is not None and upload_speed is not None:
                self.speed_analyzer.write_to_csv(download_speed, upload_speed)
                self.log_message(
                    f"Speed job: Download {download_speed / 1_000_000:.2f} Mbps, Upload {upload_speed / 1_000_000:.2f} Mbps"
                )
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during speed_job: {e}")

    def usage_job(self):
        """
        Perform a network usage analysis job.
        """
        try:
            sent_bytes, recv_bytes = self.usage_analyzer.get_network_usage()
            if sent_bytes is not None and recv_bytes is not None:
                self.usage_analyzer.write_to_csv(sent_bytes, recv_bytes)
                self.log_message(
                    f"Usage job: Sent {sent_bytes / (1024 * 1024):.2f} MB, Received {recv_bytes / (1024 * 1024):.2f} MB"
                )
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during usage_job: {e}")

    def log_message(self, message):
        """
        Log a message to the logging framework.

        Args:
            message (str): The message to log.
        """
        try:
            logging.info(message)
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during log_message: {e}")

    def setup_logger(self, name, log_file):
        """
        Setup a logger with a file handler and a console handler.

        Args:
            name (str): The name of the logger.
            log_file (str): The file where logs will be saved.

        Returns:
            Logger: The configured logger.
        """
        try:
            handler = logging.FileHandler(log_file)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(self.log_handler.formatter)

            handler.setFormatter(
                logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
            )

            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)
            logger.addHandler(console_handler)

            return logger
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during setup_logger: {e}")

    def select_files(self):
        """
        Open a file dialog to select result files for plotting.
        """
        try:
            if not os.path.exists("results"):
                QMessageBox.warning(
                    self, "Warning", "The results/ directory does not exist."
                )
                return

            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.ExistingFiles)
            file_dialog.setDirectory("results/")
            if file_dialog.exec_():
                selected_files = file_dialog.selectedFiles()
                self.plot_files(selected_files)
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during select_files: {e}")

    def plot_files(self, files):
        """
        Plot the selected files in the plot area.

        Args:
            files (list of str): List of file paths to plot.
        """
        try:
            self.plot_area.clear()
            for file in files:
                tab = QWidget()
                layout = QVBoxLayout()

                plot_label = QLabel(f"Plot for {file}")
                layout.addWidget(plot_label)

                from matplotlib.backends.backend_qt5agg import (
                    FigureCanvasQTAgg as FigureCanvas,
                )
                from matplotlib.figure import Figure

                figure = Figure()
                canvas = FigureCanvas(figure)
                ax = figure.add_subplot(111)

                if "speed" in file:
                    self.plotter.plot_speed_graph(file, ax, self.xtick_interval)
                elif "usage" in file:
                    self.plotter.plot_usage_graph(file, ax, self.xtick_interval)

                layout.addWidget(canvas)

                tab.setLayout(layout)
                self.plot_area.addTab(tab, os.path.basename(file))
        except Exception as e:
            QMessageBox.critical(
                self, "InternalError", f"An internal error occurred: {e}"
            )
            logging.error(f"An internal error occurred during plot_files: {e}")


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    plt.set_loglevel("WARNING")

    app = QApplication(sys.argv)
    gui = NetworkAnalyzerGUI()
    gui.show()
    sys.exit(app.exec_())

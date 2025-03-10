import sys
import logging
from discrepancy_finder import DiscrepancyFinder
from pandas import ExcelFile, read_excel
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout,
    QWidget, QComboBox, QTextEdit, QFileDialog, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon


class DiscrepancyFinderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("Initializing DiscrepancyFinderWindow UI.")
        self.setWindowIcon(QIcon("images/icon.png"))
        self.setWindowTitle("Discrepancy Finder")
        self.setGeometry(300, 150, 450, 500)
        self.file_path = None
        self.validator = None
        self.columns = []

        layout = QVBoxLayout()

        # Drag-and-drop area with clear button
        file_layout = QHBoxLayout()
        self.label = QLabel("Drag and drop your Excel file here", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            "QLabel { border: 2px dashed #aaa; font-size: 14px; padding: 20px; }")
        self.label.mousePressEvent = self.open_file_dialog  # Handle manual file selection
        file_layout.addWidget(self.label)

        self.clear_button = QPushButton("✖", self)  # Clear button
        self.clear_button.setFixedSize(30, 30)
        self.clear_button.setStyleSheet(
            "QPushButton { color: red; font-size: 16px; }")
        self.clear_button.clicked.connect(self.clear_file)
        self.clear_button.setVisible(False)
        file_layout.addWidget(self.clear_button)

        layout.addLayout(file_layout)

        # Sheet selector
        self.sheet_combo = QComboBox(self)
        layout.addWidget(QLabel("Select a sheet:", self))
        layout.addWidget(self.sheet_combo)

        # Column selection dropdowns
        layout.addWidget(QLabel("Group by column:", self))
        self.group_by_combo = QComboBox(self)
        layout.addWidget(self.group_by_combo)

        layout.addWidget(QLabel("Compare column 1:", self))
        self.compare_1_combo = QComboBox(self)
        layout.addWidget(self.compare_1_combo)

        layout.addWidget(QLabel("Compare column 2:", self))
        self.compare_2_combo = QComboBox(self)
        layout.addWidget(self.compare_2_combo)

        # Find button
        self.find_button = QPushButton("Find Discrepancies", self)
        self.find_button.clicked.connect(self.find_discrepancies)
        layout.addWidget(self.find_button)

        # Results output
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        # Set main widget and layout
        main_widget = QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Allow drag and drop
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            if url.isLocalFile() and url.toString().endswith('.xlsx'):
                self.file_path = url.toLocalFile()

                if not self.file_path:
                    logging.warning("File path is not set.")
                    return

                self.label.setText(f"File loaded: {self.file_path}")
                self.clear_button.setVisible(True)
                logging.info(f"File loaded: {self.file_path}")
                self.load_sheets()
                return
        self.label.setText("Invalid file. Please drop a valid .xlsx file.")
        logging.warning("Invalid file format dropped.")

    def open_file_dialog(self, event):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.file_path = file_path
            self.label.setText(f"File loaded: {self.file_path}")
            self.clear_button.setVisible(True)
            logging.info(f"File manually loaded: {self.file_path}")
            self.load_sheets()

    def clear_file(self):
        self.file_path = None
        self.label.setText("Drag and drop your Excel file here")
        self.sheet_combo.clear()
        self.group_by_combo.clear()
        self.compare_1_combo.clear()
        self.compare_2_combo.clear()
        self.results_text.clear()
        self.clear_button.setVisible(False)
        logging.info("File cleared by user.")

    def load_sheets(self):
        try:
            excel_file = ExcelFile(self.file_path)
            self.sheet_combo.clear()
            self.sheet_combo.addItems(excel_file.sheet_names)
            self.sheet_combo.currentIndexChanged.connect(self.load_columns)
            logging.info(f"Sheets loaded: {excel_file.sheet_names}")
        except Exception as e:
            logging.exception("Error loading sheets: %s", e)
            self.label.setText(f"Error loading file")

    def load_columns(self):
        try:
            sheet_name = self.sheet_combo.currentText()
            df = read_excel(self.file_path, sheet_name=sheet_name)
            self.columns = df.columns.tolist()
            self.group_by_combo.clear()
            self.compare_1_combo.clear()
            self.compare_2_combo.clear()

            self.group_by_combo.addItems(self.columns)
            self.compare_1_combo.addItems(self.columns)
            self.compare_2_combo.addItems(self.columns)

            logging.info(f"Columns loaded for sheet '{
                         sheet_name}': {self.columns}")
        except Exception as e:
            logging.exception("Error loading columns: %s", e)
            self.label.setText(f"Error loading columns")

    def find_discrepancies(self):
        """
        Finds discrepancies in the selected sheet using user-specified columns.
        """
        sheet_name = self.sheet_combo.currentText()
        group_by = self.group_by_combo.currentText()
        compare_1 = self.compare_1_combo.currentText()
        compare_2 = self.compare_2_combo.currentText()

        if not all([sheet_name, group_by, compare_1, compare_2, self.file_path]):
            self.results_text.setText(
                "Please load a file, select a sheet, and choose columns.")
            logging.warning("Incomplete input for discrepancy finding.")
            return

        try:
            logging.info(f"Finding discrepancies in sheet '{sheet_name}' with group_by='{
                group_by}', compare_1='{compare_1}', compare_2='{compare_2}'.")
            self.validator = DiscrepancyFinder(self.file_path)

            # Get discrepancies
            discrepancies = self.validator.get_discrepancies(
                sheet_name, group_by, compare_1, compare_2)

            # Display results
            if discrepancies:
                result_text = "Discrepancies found between rows:\n"
                result_text += "\n".join(f"{pair[0]
                                            } - {pair[1]}" for pair in discrepancies)
            else:
                result_text = "No discrepancies found."

            self.results_text.setText(result_text)
            logging.info("Discrepancy finding completed successfully.")
        except Exception as e:
            logging.exception("Error finding discrepancies")
            self.results_text.setText(f"Error processing sheet: {e}")


def main():
    app = QApplication(sys.argv)
    window = DiscrepancyFinderWindow()
    window.show()
    sys.exit(app.exec_())

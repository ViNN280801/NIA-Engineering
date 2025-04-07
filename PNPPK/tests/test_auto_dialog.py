import os
import sys
import glob
import pytest
from PyQt5 import QtWidgets

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gui.window import GFRControlWindow
from tests.conftest import auto_close_dialogs


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_files():
    yield
    patterns = ["test_file.csv", "test_save_file.csv", "*.png", "*.csv"]
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                os.unlink(file_path)
            except (PermissionError, FileNotFoundError):
                pass


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])
    return app


@pytest.fixture
def dialog_window(qapp):
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Тестовое окно")
    window.resize(300, 200)

    central_widget = QtWidgets.QWidget()
    window.setCentralWidget(central_widget)

    layout = QtWidgets.QVBoxLayout(central_widget)

    message_button = QtWidgets.QPushButton("Показать сообщение")
    file_button = QtWidgets.QPushButton("Выбрать файл")
    input_button = QtWidgets.QPushButton("Ввести текст")

    layout.addWidget(message_button)
    layout.addWidget(file_button)
    layout.addWidget(input_button)

    message_button.clicked.connect(
        lambda: ignore_result(QtWidgets.QMessageBox.information)(
            window, "Информация", "Это информационное сообщение"
        )
    )

    file_button.clicked.connect(
        lambda: ignore_result(QtWidgets.QFileDialog.getOpenFileName)(
            window, "Выберите файл", "", "All Files (*.*)"
        )
    )

    input_button.clicked.connect(
        lambda: ignore_result(QtWidgets.QInputDialog.getText)(
            window, "Ввод текста", "Введите текст:"
        )
    )

    return window


def test_show_message_dialog_auto_closing(qapp, dialog_window, auto_close_dialogs):
    result = QtWidgets.QMessageBox.information(
        dialog_window,
        "Тестовое сообщение",
        "Это сообщение должно автоматически закрыться",
    )

    assert result == QtWidgets.QMessageBox.Ok

    result = QtWidgets.QMessageBox.question(
        dialog_window,
        "Тестовый вопрос",
        "Это вопрос должен автоматически получить ответ Да",
    )

    assert result == QtWidgets.QMessageBox.Yes


def test_file_dialog_auto_closing(qapp, dialog_window, auto_close_dialogs):
    filename, _ = QtWidgets.QFileDialog.getOpenFileName(
        dialog_window,
        "Выберите файл для тестирования",
        "",
        "Text Files (*.txt);;All Files (*.*)",
    )

    assert filename == "test_file.csv"

    save_filename, _ = QtWidgets.QFileDialog.getSaveFileName(
        dialog_window, "Сохраните файл", "", "CSV Files (*.csv)"
    )

    assert save_filename == "test_save_file.csv"


def test_input_dialog_auto_closing(qapp, dialog_window, auto_close_dialogs):
    text, ok = QtWidgets.QInputDialog.getText(
        dialog_window, "Ввод текста", "Введите ваше имя:"
    )

    assert text == "Test Input"
    assert ok is True

    number, ok = QtWidgets.QInputDialog.getInt(
        dialog_window, "Ввод числа", "Введите ваш возраст:", min=0, max=120
    )

    assert number == 42
    assert ok is True


def test_gfr_window_dialog_auto_closing(qapp, auto_close_dialogs):
    try:
        from unittest.mock import patch

        with patch("gui.window.GFRController"), patch(
            "gui.window.RelayController"
        ), patch("gui.window.YAMLConfigLoader"), patch(
            "serial.tools.list_ports.comports", return_value=[]
        ):

            window = GFRControlWindow()

            if hasattr(window, "_save_data_to_csv"):
                window.flow_data = [(0.1, 10), (0.2, 20)]
                with patch("builtins.open", create=True):
                    window._save_data_to_csv()

            window.close()
            qapp.processEvents()

    except ImportError:
        pytest.skip("GFRControlWindow не доступен для тестирования")


def ignore_result(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    return wrapper


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

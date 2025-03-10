import schedule
import time
import signal
import sys
import os
import logging
from datetime import datetime
from .network_usage_analyzer import NetworkUsageAnalyzer, NETWORK_USAGE_ANALYZER
from .network_speed_analyzer import NetworkSpeedAnalyzer, NETWORK_SPEED_ANALYZER
from util import GraphPlotter, I18N


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()

    handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger


class Menu:
    def __init__(self, lang="en"):
        self.i18n = I18N(lang)
        self.analysis_duration = 60
        self.analyze_speed = True
        self.analyze_usage = True
        self.frequency = 1
        self.xtick_interval = 5
        self.infinite_analysis = True
        self.speed_logger = None
        self.usage_logger = None
        self.usage_analyzer = None
        self.speed_analyzer = None
        self.plotter = None
        signal.signal(signal.SIGINT, self.exit_gracefully)
        if hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, self.exit_gracefully)

    def show_menu(self):
        while True:
            print("\nMenu:")
            print(f"1. {self.i18n.get('menu_start_scan')}")
            print(f"2. {self.i18n.get('menu_change_settings')}")
            print(f"3. {self.i18n.get('menu_show_settings')}")
            print(f"4. {self.i18n.get('menu_exit')}")
            print(f"5. Change Language")
            choice = input(self.i18n.get("menu_enter_choice"))

            if choice == "1":
                self.start_analysis()
            elif choice == "2":
                self.change_settings()
            elif choice == "3":
                self.show_settings()
            elif choice == "4":
                self.exit_program()
            elif choice == "5":
                self.change_language()
            else:
                print(self.i18n.get("menu_invalid_choice"))

    def change_language(self):
        print("Select language: ")
        print("1. English")
        print("2. Russian")
        choice = input("Enter your choice: ")
        if choice == "1":
            self.language = "en"
        elif choice == "2":
            self.language = "ru"
        else:
            print("Invalid choice. Please try again.")
            return
        self.i18n = I18N(self.language)
        print(f"Language changed to {self.language}")

    def show_settings(self):
        print(f"\n{self.i18n.get('current_settings')}:")
        print(f"{self.i18n.get('analysis_duration')}: {self.analysis_duration} minutes")
        print(
            f"{self.i18n.get('infinite_analysis')}: {self.i18n.get('yes') if self.infinite_analysis else self.i18n.get('no')}"
        )
        print(
            f"{self.i18n.get('analyze_speed')}: {self.i18n.get('yes') if self.analyze_speed else self.i18n.get('no')}"
        )
        print(
            f"{self.i18n.get('analyze_usage')}: {self.i18n.get('yes') if self.analyze_usage else self.i18n.get('no')}"
        )
        print(f"{self.i18n.get('measurement_frequency')}: {self.frequency} minutes")
        print(f"{self.i18n.get('xtick_interval')}: {self.xtick_interval}")

    def change_settings(self):
        while True:
            print("\nSettings:")
            print(f"1. {self.i18n.get('set_analysis_duration')}")
            print(f"2. {self.i18n.get('analyze_speed_question')}")
            print(f"3. {self.i18n.get('analyze_usage_question')}")
            print(f"4. {self.i18n.get('set_frequency')}")
            print(f"5. {self.i18n.get('set_xtick_interval')}")
            print(f"6. {self.i18n.get('infinite_analysis')}")
            print(f"7. {self.i18n.get('menu_exit')}")
            choice = input(self.i18n.get("menu_enter_choice"))

            if choice == "1":
                self.set_analysis_duration()
            elif choice == "2":
                self.set_analyze_speed()
            elif choice == "3":
                self.set_analyze_usage()
            elif choice == "4":
                self.set_frequency()
            elif choice == "5":
                self.set_xtick_interval()
            elif choice == "6":
                self.set_infinite_analysis()
            elif choice == "7":
                break
            else:
                print(self.i18n.get("menu_invalid_choice"))

    def set_infinite_analysis(self):
        choice = (
            input(f"{self.i18n.get('infinite_analysis')}? (yes/no): ").strip().lower()
        )
        if choice in ["y", "yes", "д", "да"]:
            self.infinite_analysis = True
        elif choice in ["n", "no", "н", "нет"]:
            self.infinite_analysis = False
        else:
            print(self.i18n.get("menu_invalid_choice"))

    def set_analysis_duration(self):
        try:
            self.analysis_duration = int(
                input(f"{self.i18n.get('analysis_duration')}: ")
            )
        except ValueError:
            print(self.i18n.get("menu_invalid_choice"))

    def set_analyze_speed(self):
        choice = (
            input(f"{self.i18n.get('analyze_speed_question')}? (yes/no): ")
            .strip()
            .lower()
        )
        if choice in ["y", "yes", "д", "да"]:
            self.analyze_speed = True
        elif choice in ["n", "no", "н", "нет"]:
            self.analyze_speed = False
        else:
            print(self.i18n.get("menu_invalid_choice"))

    def set_analyze_usage(self):
        choice = (
            input(f"{self.i18n.get('analyze_usage_question')}? (yes/no): ")
            .strip()
            .lower()
        )
        if choice in ["y", "yes", "д", "да"]:
            self.analyze_usage = True
        elif choice in ["n", "no", "н", "нет"]:
            self.analyze_usage = False
        else:
            print(self.i18n.get("menu_invalid_choice"))

    def set_frequency(self):
        try:
            self.frequency = int(input(f"{self.i18n.get('set_frequency')}: "))
        except ValueError:
            print(self.i18n.get("menu_invalid_choice"))

    def set_xtick_interval(self):
        try:
            self.xtick_interval = int(input(f"{self.i18n.get('set_xtick_interval')}: "))
        except ValueError:
            print(self.i18n.get("menu_invalid_choice"))

    def start_analysis(self):
        if not self.analyze_speed and not self.analyze_usage:
            print(self.i18n.get("enable_at_least_one_analysis"))
            return

        if not os.path.exists("logs"):
            os.makedirs("logs")

        if not os.path.exists("results"):
            os.makedirs("results")

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        speed_csv_file = None
        usage_csv_file = None

        if self.analyze_speed:
            speed_log_file = os.path.join("logs", f"{now}_speed.log")
            speed_csv_file = os.path.join("results", f"{now}_speed_measurement.csv")
            self.speed_logger = setup_logger("speed", speed_log_file)
            self.speed_analyzer = NetworkSpeedAnalyzer(
                speed_csv_file, self.speed_logger
            )
            schedule.every(self.frequency).minutes.do(self.speed_job)

        if self.analyze_usage:
            usage_log_file = os.path.join("logs", f"{now}_data_usage.log")
            usage_csv_file = os.path.join("results", f"{now}_network_usage.csv")
            self.usage_logger = setup_logger("usage", usage_log_file)
            self.usage_analyzer = NetworkUsageAnalyzer(
                usage_csv_file, self.usage_logger
            )
            schedule.every(self.frequency).minutes.do(self.usage_job)

        self.plotter = GraphPlotter(
            usage_csv_file if self.analyze_usage else None,
            speed_csv_file if self.analyze_speed else None,
        )

        if self.usage_logger:
            self.usage_logger.info(self.i18n.get("usage_analyzer_starting"))
        if self.speed_logger:
            self.speed_logger.info(self.i18n.get("speed_analyzer_starting"))

        if not self.infinite_analysis:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(self.analysis_duration * 60)

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.exit_gracefully()

    def usage_job(self):
        sent_bytes, recv_bytes = self.usage_analyzer.get_network_usage()
        if sent_bytes is not None and recv_bytes is not None:
            self.usage_analyzer.write_to_csv(sent_bytes, recv_bytes)

    def speed_job(self):
        download_speed, upload_speed = self.speed_analyzer.measure_speed()
        if download_speed is not None and upload_speed is not None:
            self.speed_analyzer.write_to_csv(download_speed, upload_speed)

    def exit_gracefully(self, signum=None, frame=None):
        if self.usage_logger:
            self.usage_logger.info(self.i18n.get("received_exit_signal"))
        if self.speed_logger:
            self.speed_logger.info(self.i18n.get("received_exit_signal"))
        schedule.clear()
        if self.plotter:
            self.plotter.plot_graphs(self.xtick_interval)
        print(self.i18n.get("analysis_stopped_plotted"))
        sys.exit(0)

    def exit_program(self):
        self.exit_gracefully()

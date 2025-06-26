import sys
import logging
from typing import Optional, List, Tuple, Dict
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QComboBox, QProgressBar, QMessageBox, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QListWidget
)
from matplotlib import pyplot as plt

from core.scrap import ExchangeRateAPIClient
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from core.workers import ChartWorker, RateWorker, PredictWorker
from datetime import date

from core.settings import SettingsService, ThemeSettingsDialog
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(BASE_DIR, "icons", "ico.png")


logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

scrapper = ExchangeRateAPIClient()


class App(object):
    def __init__(self, app: QApplication) -> None:
        self.progressBar = None
        self.pushButton_settings = None
        self.label = None
        self.comboBox_days = None
        self.predict_btn = None
        self.pushButton_clear_delete = None
        self.pushButton_chart = None
        self.pushButton_show = None
        self.listWidget = None
        self.currencies = None
        self.chart_worker: Optional[ChartWorker] = None
        self.rate_worker: Optional[RateWorker] = None
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvas] = None
        self.rate_cache: Dict[str, str] = {}
        self.chart_cache: Dict[Tuple[str, int], Tuple[List[date], List[float]]] = {}

        self.app = app
        self.settings = SettingsService()
        self.is_dark_theme = self.settings.load_theme()

    def setupUi(self, MainWindow: QMainWindow) -> None:
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1040, 600)  # чуть шире
        MainWindow.setWindowTitle("Курси Валют")

        try:
            MainWindow.setWindowIcon(QtGui.QIcon(icon_path))

        except Exception as e:
            logging.warning(f"Не удалось загрузить иконку: {e}")

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        # Загрузка темы
        try:
            if self.is_dark_theme:
                with open(os.path.join(BASE_DIR, "styles", "dark.css"), "r", encoding="utf-8") as f:

                    self.app.setStyleSheet(f.read())
            else:
                with open(os.path.join(BASE_DIR, "styles", "style.css"), "r", encoding="utf-8") as f:

                    self.app.setStyleSheet(f.read())
        except Exception as e:
            logging.error(f"Ошибка загрузки стилей: {e}")

        self.currencies = scrapper.get_symbols()["symbols"]

        # Левая часть
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)

        self.listWidget = QListWidget()
        self.listWidget.setFixedSize(220, 350)  # чуть меньше высота
        for cur in self.currencies.keys():
            self.listWidget.addItem(cur)
        self.listWidget.setCurrentRow(0)

        self.pushButton_show = QPushButton("Показати курс")
        self.pushButton_show.setFixedSize(220, 40)
        self.pushButton_show.setToolTip("Показати актуальний курс обраної валюти")
        self.pushButton_show.clicked.connect(self.start_rate_worker)

        self.pushButton_chart = QPushButton("Графік")
        self.pushButton_chart.setFixedSize(220, 40)
        self.pushButton_chart.setToolTip("Побудувати графік курсу")
        self.pushButton_chart.clicked.connect(self.start_chart_worker)

        self.pushButton_clear_delete = QPushButton("Очистити / Видалити графік")
        self.pushButton_clear_delete.setFixedSize(220, 40)
        self.pushButton_clear_delete.setToolTip("Очистити графік і кеш")
        self.pushButton_clear_delete.clicked.connect(self.clear_and_delete_chart)

        self.predict_btn = QPushButton("Предікт на завтра")
        self.predict_btn.setFixedSize(220, 40)
        self.predict_btn.setToolTip("Подивитися предікт курса вибранної валюти до UAH на базі машинного навчання.")
        self.predict_btn.clicked.connect(self.on_predict_button_clicked)

        self.comboBox_days = QComboBox()
        self.comboBox_days.setFixedSize(220, 30)
        self.comboBox_days.setToolTip("Виберiть перiод для графiку.")
        self.comboBox_days.addItem("30 днів", 30)
        self.comboBox_days.addItem("90 днів", 90)
        self.comboBox_days.addItem("1 рік", 365)

        self.label = QLabel("Оберіть валюту та натисніть «Показати курс»")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 20px;")

        self.progressBar = QProgressBar()
        self.progressBar.setFixedSize(220, 20)
        self.progressBar.setRange(0, 0)  # Непрерывный режим
        self.progressBar.setVisible(False)

        # Добавляем в левую колонку
        left_layout.addWidget(self.listWidget)
        left_layout.addWidget(self.pushButton_show)
        left_layout.addWidget(self.pushButton_chart)
        left_layout.addWidget(self.pushButton_clear_delete)
        left_layout.addWidget(self.predict_btn)
        left_layout.addWidget(self.comboBox_days)
        left_layout.addWidget(self.progressBar)
        left_layout.addWidget(self.label)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)

        top_bar = QHBoxLayout()
        top_bar.addStretch()  # отодвигает кнопку вправо

        self.pushButton_settings = QPushButton()
        self.pushButton_settings.setFixedSize(30, 30)
        self.pushButton_settings.setToolTip("Налаштування")

        icon = QtGui.QIcon(icon_path)
        self.pushButton_settings.setIcon(icon)
        self.pushButton_settings.setIconSize(QtCore.QSize(24, 24))
        self.pushButton_settings.setFlat(True)

        self.pushButton_settings.clicked.connect(self.open_settings)

        top_bar.addWidget(self.pushButton_settings)

        right_layout.addLayout(top_bar)

        right_layout.addStretch()  # <--- эта строка важна!

        self.chart_container = QVBoxLayout()
        right_layout.addLayout(self.chart_container)


        right_layout.addLayout(top_bar)
        # Контейнер для графика
        self.chart_container = QVBoxLayout()
        right_layout.addLayout(self.chart_container)

        # Основной layout
        main_layout = QHBoxLayout(self.centralwidget)
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)

        self.right_layout = self.chart_container

    def clear_and_delete_chart(self) -> None:
        if self.canvas:
            self.right_layout.removeWidget(self.canvas)
            self.canvas.setParent(None)
            self.canvas.deleteLater()
            self.canvas = None
            self.figure = None
        self.chart_cache.clear()
        if self.label.text() != "Завантаження графіка...":
            self.label.setText("Оберіть валюту та натисніть «Показати курс»")

    def show_error(self, message: str) -> None:
        logging.error(message)
        self.label.setText(message)
        self.progressBar.setVisible(False)
        ret = QMessageBox.warning(None, "Помилка", message, QMessageBox.Retry | QMessageBox.Close)
        if ret == QMessageBox.Retry:
            if "курсу" in message.lower():
                self.start_rate_worker()
            elif "графіка" in message.lower():
                self.start_chart_worker()

    def start_rate_worker(self) -> None:
        if self.rate_worker and self.rate_worker.isRunning():
            self.show_error("Запит курсу вже виконується. Будь ласка, зачекайте.")
            return
        item = self.listWidget.currentItem()
        if not item:
            self.show_error("Будь ласка, оберіть валюту зі списку.")
            return
        selected_currency = item.text()

        if selected_currency in self.rate_cache:
            self.label.setText(self.rate_cache[selected_currency])
            return

        self.label.setText("Завантаження курсу...")
        self.progressBar.setVisible(True)

        if self.rate_worker and self.rate_worker.isRunning():
            self.rate_worker.quit()
            self.rate_worker.wait()

        self.rate_worker = RateWorker(selected_currency, scrapper=scrapper)
        self.rate_worker.finished.connect(self.on_rate_ready)
        self.rate_worker.error.connect(self.on_rate_error)
        self.rate_worker.finished.connect(lambda: self.progressBar.setVisible(False))
        self.rate_worker.start()

    def on_rate_ready(self, text: str) -> None:
        self.label.setText(text)
        item = self.listWidget.currentItem()
        if item:
            currency = item.text()
            self.rate_cache[currency] = text

    def on_rate_error(self, msg: str) -> None:
        self.show_error("Помилка завантаження курсу: " + msg)

    def start_chart_worker(self) -> None:

        if self.chart_worker and self.chart_worker.isRunning():
            self.show_error("Запит графіка вже виконується. Будь ласка, зачекайте.")
            return
        if self.canvas:
            self.right_layout.removeWidget(self.canvas)
            self.canvas.setParent(None)
            self.canvas.deleteLater()
            self.canvas = None
            self.figure = None
        item = self.listWidget.currentItem()
        if not item:
            self.show_error("Будь ласка, оберіть валюту зі списку.")
            return
        currency = item.text()
        days = self.comboBox_days.currentData()
        key = (currency, days)
        if key in self.chart_cache:
            self.show_chart(*self.chart_cache[key])
            return

        self.label.setText("Завантаження графіка...")
        self.progressBar.setVisible(True)

        if self.chart_worker and self.chart_worker.isRunning():
            self.chart_worker.quit()
            self.chart_worker.wait()

        self.chart_worker = ChartWorker(currency, days)
        self.chart_worker.finished.connect(self.on_chart_ready)
        self.chart_worker.error.connect(self.on_chart_error)
        self.chart_worker.finished.connect(lambda: self.progressBar.setVisible(False))
        self.chart_worker.start()

    def on_chart_ready(self, dates: List[date], rates: List[float]) -> None:

        key = (self.listWidget.currentItem().text(), self.comboBox_days.currentData())
        self.chart_cache[key] = (dates, rates)
        self.show_chart(dates, rates)

    def on_chart_error(self, msg: str) -> None:
        self.show_error("Помилка завантаження графіка: " + msg)

    def show_chart(self, dates: list, rates: list) -> None:
        if self.canvas:
            self.right_layout.removeWidget(self.canvas)
            self.canvas.setParent(None)
            self.canvas.deleteLater()
        chart_settings = self.settings.load_chart_settings()
        line_color = chart_settings.get("line_color", "#2d78d8")
        self.figure = plt.Figure(figsize=(7, 5))
        self.canvas = FigureCanvas(self.figure)
        self.right_layout.addWidget(self.canvas)

        ax = self.figure.add_subplot(111)
        ax.clear()

        # Проверка данных
        if not dates or not rates or len(dates) != len(rates):
            self.show_error("Немає даних для побудови графіка.")
            return

        chart_settings = self.settings.load_chart_settings()
        chart_type = chart_settings.get("chart_type", "Лінійний")
        show_grid = chart_settings.get("show_grid", True)
        show_sma = chart_settings.get("show_sma", False)

        has_label = False

        if chart_type == "Лінійний":
            ax.plot(dates, rates, label="Курс", color=line_color)
            has_label = True
        elif chart_type == "Баровий":
            ax.bar(dates, rates, label="Баровий", color=line_color)
            has_label = True
        elif chart_type == "Точечний":
            ax.scatter(dates, rates, label="Точечний", color=line_color)
            has_label = True
        elif chart_type == "Діаграмма розбросу":
            ax.scatter(dates, rates, label='Курс (точки)',color = line_color)
            has_label = True


        if show_sma and len(rates) >= 5:
            window = 5
            sma = [sum(rates[i - window:i]) / window for i in range(window, len(rates) + 1)]
            ax.plot(dates[window - 1:], sma, label="SMA", linestyle="--", color="orange")
            has_label = True

        if has_label:
            ax.legend()

        ax.grid(show_grid)
        ax.set_title("Динаміка курсу")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Курс")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%Y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.figure.autofmt_xdate()
        self.label.setText("Графiк побудовано.")
        self.canvas.draw()
    def on_predict_button_clicked(self):

        item = self.listWidget.currentItem()

        if not item:
            self.show_error("Будь ласка, оберіть валюту зі списку.")

            return
        self.progressBar.setVisible(True)
        selected_currency = item.text()
        self.predict_worker = PredictWorker(selected_currency, days=30)
        self.predict_worker.finished.connect(self.on_predict_finished)
        self.predict_worker.error.connect(self.on_predict_error)
        self.predict_worker.start()
        self.label.setText("Виконується предікт...")

    def on_predict_finished(self, result_text: str):
        self.label.setText(result_text)
        self.progressBar.setVisible(False)
    def on_predict_error(self, error_text: str):
        self.progressBar.setVisible(False)
        self.show_error(error_text)
    def open_settings(self)-> None:
        settings_service = SettingsService()
        dlg = ThemeSettingsDialog(settings_service=settings_service)
        if dlg.exec_and_save():
            print("Налаштування змінені.")
            if dlg.is_dark_theme:
                self.apply_dark_theme()
            else:
                self.apply_light_theme()
            # Не вызывать сразу обновление графика
            chart_settings = dlg.selected_chart_settings()
            self.settings.save_chart_settings(chart_settings)
            # self.apply_chart_settings(chart_settings)  <-- убрать или закомментировать
        else:
            print("Налаштування не змінені.")

    def apply_dark_theme(self) -> None:
        try:
            with open(os.path.join(BASE_DIR, "styles", "dark.css"), "r", encoding="utf-8") as f:

                self.app.setStyleSheet(f.read())
            self.is_dark_theme = True
            self.settings.save_theme(True)

        except Exception as e:
            logging.error(f"Помилка завантаження темної теми: {e}")

    def apply_light_theme(self) -> None:
        try:
            with open(os.path.join(BASE_DIR, "styles", "style.css"), "r", encoding="utf-8") as f:

                self.app.setStyleSheet(f.read())
            self.is_dark_theme = False
            self.settings.save_theme(False)

        except Exception as e:
            logging.error(f"Помилка завантаженная свiтлої теми: {e}")

    def apply_chart_settings(self, chart_settings: dict) -> None:
        if not self.figure or not self.canvas:
            return  # график еще не построен

        # Получаем параметры
        chart_type = chart_settings.get("chart_type", "Лінійний")
        show_grid = chart_settings.get("show_grid", True)
        show_sma = chart_settings.get("show_sma", False)

        # Получаем текущие данные графика из кеша (если есть)
        current_item = self.listWidget.currentItem()
        if not current_item:
            return
        currency = current_item.text()
        days = self.comboBox_days.currentData()
        key = (currency, days)
        if key not in self.chart_cache:
            return
        dates, rates = self.chart_cache[key]

        ax = self.figure.axes[0]
        ax.clear()
        chart_settings = self.settings.load_chart_settings()
        line_color = chart_settings.get("line_color", "#2d78d8")
        # Отрисовка графика по типу
        if chart_type == "Лінійний":
            ax.plot(dates, rates, label="Курс", color=line_color)
            has_label = True
        elif chart_type == "Баровий":
            ax.bar(dates, rates, label="Баровий", color=line_color)
            has_label = True
        elif chart_type == "Точечний":
            ax.scatter(dates, rates, label="Точечний", color=line_color)
            has_label = True
        elif chart_type == "Діаграмма розбросу":
            ax.scatter(dates, rates, label='Курс (точки)', color=line_color)
            has_label = True

        if show_grid:
            ax.grid(True)
        else:
            ax.grid(False)

        if show_sma:
            window = 5
            if len(rates) >= window:
                sma = [sum(rates[i - window:i]) / window for i in range(window, len(rates) + 1)]
                ax.plot(dates[window - 1:], sma, label="SMA", linestyle="--", color="orange")

        ax.set_title("Динаміка курсу")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Курс")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%Y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.figure.autofmt_xdate()

        ax.legend()
        self.canvas.draw()

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    application = App(app)
    application.setupUi(main_window)
    main_window.show()
    sys.exit(app.exec_())
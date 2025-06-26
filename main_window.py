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

# ВАЖНО: базовая директория — папка, где лежит этот скрипт
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("Current working dir:", os.getcwd())
print("Base dir:", BASE_DIR)

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

        # Загрузка иконки через абсолютный путь
        icon_path = os.path.join(BASE_DIR, "icons", "ico.png")
        try:
            MainWindow.setWindowIcon(QtGui.QIcon(icon_path))
        except Exception as e:
            logging.warning(f"Не удалось загрузить иконку: {e}")

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        # Загрузка темы через абсолютный путь
        try:
            if self.is_dark_theme:
                dark_css_path = os.path.join(BASE_DIR, "styles", "dark.css")
                with open(dark_css_path, "r", encoding="utf-8") as f:
                    self.app.setStyleSheet(f.read())
            else:
                style_css_path = os.path.join(BASE_DIR, "styles", "style.css")
                with open(style_css_path, "r", encoding="utf-8") as f:
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

        # Основной layout
        main_layout = QHBoxLayout(self.centralwidget)
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)

        self.right_layout = self.chart_container

    # --- Остальной код без изменений ---

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
            return  # Уже выполняется
        self.progressBar.setVisible(True)
        self.label.setText("Завантаження курсу...")
        cur = self.listWidget.currentItem().text()
        if cur in self.rate_cache:
            self.label.setText(f"{cur} = {self.rate_cache[cur]} UAH")
            self.progressBar.setVisible(False)
            return
        self.rate_worker = RateWorker(cur)
        self.rate_worker.finished.connect(self.on_rate_finished)
        self.rate_worker.error.connect(self.show_error)
        self.rate_worker.start()

    def on_rate_finished(self, rate: str) -> None:
        cur = self.listWidget.currentItem().text()
        self.rate_cache[cur] = rate
        self.label.setText(f"{cur} = {rate} UAH")
        self.progressBar.setVisible(False)

    def start_chart_worker(self) -> None:
        if self.chart_worker and self.chart_worker.isRunning():
            return  # Уже выполняется
        cur = self.listWidget.currentItem().text()
        days = self.comboBox_days.currentData()
        key = (cur, days)
        if key in self.chart_cache:
            self.draw_chart(*self.chart_cache[key], cur)
            return

        self.progressBar.setVisible(True)
        self.label.setText("Завантаження графіка...")
        self.chart_worker = ChartWorker(cur, days)
        self.chart_worker.finished.connect(lambda data: self.on_chart_finished(data, cur, days))
        self.chart_worker.error.connect(self.show_error)
        self.chart_worker.start()

    def on_chart_finished(self, data: Tuple[List[date], List[float]], cur: str, days: int) -> None:
        self.chart_cache[(cur, days)] = data
        self.draw_chart(*data, cur)
        self.progressBar.setVisible(False)
        self.label.setText("Графік побудовано")

    def draw_chart(self, dates: List[date], rates: List[float], cur: str) -> None:
        if self.canvas:
            self.right_layout.removeWidget(self.canvas)
            self.canvas.setParent(None)
            self.canvas.deleteLater()

        self.figure = Figure(figsize=(7, 4), dpi=100)
        ax = self.figure.add_subplot(111)
        ax.plot(dates, rates, marker='o', linestyle='-')
        ax.set_title(f"Курс {cur} до UAH")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Курс")
        ax.grid(True)

        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.figure.autofmt_xdate()

        self.canvas = FigureCanvas(self.figure)
        self.right_layout.addWidget(self.canvas)
        self.canvas.draw()

    def open_settings(self) -> None:
        dialog = ThemeSettingsDialog()
        dialog.set_theme(self.is_dark_theme)
        if dialog.exec():
            self.is_dark_theme = dialog.get_theme()
            self.settings.save_theme(self.is_dark_theme)
            if self.is_dark_theme:
                dark_css_path = os.path.join(BASE_DIR, "styles", "dark.css")
                with open(dark_css_path, "r", encoding="utf-8") as f:
                    self.app.setStyleSheet(f.read())
            else:
                style_css_path = os.path.join(BASE_DIR, "styles", "style.css")
                with open(style_css_path, "r", encoding="utf-8") as f:
                    self.app.setStyleSheet(f.read())

    def on_predict_button_clicked(self) -> None:
        cur = self.listWidget.currentItem().text()
        self.progressBar.setVisible(True)
        self.label.setText("Завантаження предікту...")
        self.predict_btn.setEnabled(False)

        def on_finished(predict: float) -> None:
            self.label.setText(f"Передбачення курсу {cur} на завтра: {predict:.4f} UAH")
            self.progressBar.setVisible(False)
            self.predict_btn.setEnabled(True)

        def on_error(msg: str) -> None:
            self.show_error(msg)
            self.predict_btn.setEnabled(True)

        self.predict_worker = PredictWorker(cur)
        self.predict_worker.finished.connect(on_finished)
        self.predict_worker.error.connect(on_error)
        self.predict_worker.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App(app)
    mainWin = QMainWindow()
    ex.setupUi(mainWin)
    mainWin.show()
    sys.exit(app.exec())

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QRadioButton, QPushButton, QCheckBox,
    QComboBox, QLabel, QColorDialog
)
from core.сonfig import load_config, save_config


class SettingsService:
    def __init__(self):
        self.config = load_config()

        self.is_dark_theme = self.config.get("is_dark_theme", False)
        self.chart_settings = self.config.get(
            "chart_settings",
            {
                "chart_type": "Лінійний",
                "show_grid": True,
                "show_sma": False,
                "line_color": "#2d78d8"  # Цвет по умолчанию
            }
        )

    def load_theme(self) -> bool:
        return self.is_dark_theme

    def save_theme(self, is_dark: bool) -> None:
        self.is_dark_theme = is_dark
        self.config["is_dark_theme"] = is_dark
        save_config(self.config)

    def load_chart_settings(self) -> dict:
        return self.chart_settings

    def save_chart_settings(self, chart_settings: dict) -> None:
        self.chart_settings = chart_settings
        self.config["chart_settings"] = chart_settings
        save_config(self.config)


class ThemeSettingsDialog(QDialog):
    def __init__(self, parent=None, settings_service=None):
        super().__init__(parent)

        self.setWindowTitle("Налаштування")
        self.setFixedSize(360, 400)

        self.settings_service = settings_service or SettingsService()
        self.is_dark_theme = self.settings_service.load_theme()
        self.chart_settings = self.settings_service.load_chart_settings()

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()

        # --- Тема ---
        self.radio_light = QRadioButton("Свiтла тема")
        self.radio_dark = QRadioButton("Темна тема")
        self.radio_light.setFixedHeight(30)
        self.radio_dark.setFixedHeight(30)

        if self.is_dark_theme:
            self.radio_dark.setChecked(True)
        else:
            self.radio_light.setChecked(True)

        layout.addWidget(QLabel("Тема:"))
        layout.addWidget(self.radio_light)
        layout.addWidget(self.radio_dark)
        layout.addSpacing(10)

        # --- Колір графіка ---
        layout.addWidget(QLabel("Колір графіка:"))

        current_color = self.chart_settings.get("line_color", "#2d78d8")
        self.color_label = QLabel()
        self.color_label.setFixedSize(340, 20)
        self.color_label.setStyleSheet(f"background-color: {current_color}")
        layout.addWidget(self.color_label)

        self.color_button = QPushButton("Вибрати колір")
        self.color_button.clicked.connect(self.choose_color)
        layout.addWidget(self.color_button)
        self.color_button.setFixedSize(340, 30)
        # --- Налаштування графіка ---
        layout.addSpacing(10)
        layout.addWidget(QLabel("Тип графіка:"))

        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Лінійний", "Баровий", "Точечний", "Діаграмма розбросу"])
        self.chart_type_combo.setCurrentText(self.chart_settings.get("chart_type", "Лінійний"))
        layout.addWidget(self.chart_type_combo)

        self.checkbox_grid = QCheckBox("Показати сітку")
        self.checkbox_grid.setChecked(self.chart_settings.get("show_grid", True))
        layout.addWidget(self.checkbox_grid)

        self.checkbox_sma = QCheckBox("Показати SMA")
        self.checkbox_sma.setChecked(self.chart_settings.get("show_sma", False))
        layout.addWidget(self.checkbox_sma)

        # --- Кнопки ---
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Вiдмiна")

        btn_ok.setFixedSize(90, 30)
        btn_cancel.setFixedSize(90, 30)

        btn_ok.clicked.connect(self.on_ok_clicked)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()

        layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def on_ok_clicked(self) -> None:
        self.is_dark_theme = self.radio_dark.isChecked()
        self.accept()  # Закрываем диалог с кодом Accepted

    def exec_and_save(self) -> bool:
        if self.exec() == QDialog.Accepted:
            self.settings_service.save_theme(self.selected_theme() == "dark")
            self.settings_service.save_chart_settings(self.selected_chart_settings())
            return True
        return False

    def selected_theme(self) -> str:
        return "dark" if self.radio_dark.isChecked() else "light"

    def choose_color(self) -> None:
        current_hex = self.chart_settings.get("line_color", "#2d78d8")
        current_color = QColor(current_hex)
        color = QColorDialog.getColor(current_color, self, "Виберіть колір графіка")

        if color.isValid():
            hex_color = color.name()
            self.chart_settings["line_color"] = hex_color
            self.color_label.setStyleSheet(f"background-color: {hex_color}")

    def selected_chart_settings(self) -> dict:
        return {
            "chart_type": self.chart_type_combo.currentText(),
            "show_grid": self.checkbox_grid.isChecked(),
            "show_sma": self.checkbox_sma.isChecked(),
            "line_color": self.chart_settings.get("line_color", "#2d78d8")
        }

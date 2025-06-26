from PyQt5 import QtCore
import logging
import traceback
import time
from typing import List
from datetime import date

from core.scrap import ExchangeRateAPIClient
from core.graphic import NBUExchangeRates
from core.regression import RatePredictor

def validate_rates(
    dates: List[date],
    rates: List[float],
    min_points: int = 5,
    max_consecutive_missing: int = 2,
    max_missing_ratio: float = 0.2
) -> bool:
    """
    Перевірка валідності даних (без змін).
    """
    if dates is None or rates is None:
        logging.warning("Дати або курси дорівнюють None")
        return False

    if len(dates) < min_points or len(rates) < min_points:
        logging.warning("Недостатньо точок для побудови графіка")
        return False

    missing_count = 0
    consecutive_missing = 0

    for rate in rates:
        if rate is None or rate == 0:
            missing_count += 1
            consecutive_missing += 1
            if consecutive_missing > max_consecutive_missing:
                logging.warning("Занадто багато відсутніх значень підряд")
                return False
        else:
            consecutive_missing = 0

    missing_ratio = missing_count / len(rates)
    if missing_ratio > max_missing_ratio:
        logging.warning("Занадто багато відсутніх значень у даних")
        return False

    return True

class PredictWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, currency_code: str, days: int = 30, parent=None):
        super().__init__(parent)
        self.currency_code = currency_code
        self.days = days

    def run(self):
        try:
            nbu = NBUExchangeRates(self.currency_code)
            dates, rates = nbu.get_rates(self.days)
            if not dates or not rates:
                self.error.emit("Немає даних для прогнозу.")
                return

            predictor = RatePredictor()
            predicted_rate = predictor.predict_rate(dates, rates)

            result_text = f"Прогноз курсу {self.currency_code} до UAH на наступний день: {predicted_rate:.2f}"
            self.finished.emit(result_text)

        except Exception as e:
            logging.error(f"Помилка в PredictWorker: {e}\n{traceback.format_exc()}")
            self.error.emit(f"Помилка при прогнозуванні: {e}")

class ChartWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal(object, object, float)  # дати, курси, прогноз
    error = QtCore.pyqtSignal(str)

    def __init__(self, currency_code: str, days: int = 30, timeout: int = 30) -> None:
        super().__init__()
        self.currency_code = currency_code
        self.days = days
        self.timeout = timeout
        self._start_time = None

    def run(self) -> None:
        self._start_time = time.time()
        try:
            nbu = NBUExchangeRates(currency_code=self.currency_code)
            dates, rates = nbu.get_rates(days=self.days)

            elapsed = time.time() - self._start_time
            if elapsed > self.timeout:
                self.error.emit("Перевищено час очікування відповіді сервера (графік)")
                return

            if not validate_rates(dates, rates):
                self.error.emit("Недостатньо даних для побудови графіка.")
                return

            prediction = RatePredictor.predict_rate(dates, rates)
            self.finished.emit(dates, rates, prediction)

        except Exception as e:
            logging.error(f"Помилка в ChartWorker: {e}\n{traceback.format_exc()}")
            self.error.emit(f"Помилка при побудові графіка: {e}")

class RateWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, currency_code: str, scrapper: ExchangeRateAPIClient, timeout: int = 10) -> None:
        super().__init__()
        self.currency_code = currency_code
        self.scrapper = scrapper
        self.timeout = timeout
        self._start_time = None

    def run(self) -> None:
        self._start_time = time.time()
        try:
            rate_data = self.scrapper.get_rate_to_uah(self.currency_code)

            elapsed = time.time() - self._start_time
            if elapsed > self.timeout:
                self.error.emit("Перевищено час очікування відповіді сервера (курс)")
                return

            text = f"Курс {rate_data['base']} → {rate_data['currency']}: {rate_data['rate']:.2f}"
            self.finished.emit(text)

        except Exception as e:
            logging.error(f"Помилка в RateWorker: {e}\n{traceback.format_exc()}")
            self.error.emit("Помилка при отриманні курсу.")

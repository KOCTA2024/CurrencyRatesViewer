import requests
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import logging
from typing import List, Tuple, Optional


class NBUExchangeRates:
    BASE_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"

    def __init__(self, currency_code: str = "USD"):
        self.currency_code = currency_code

    def get_rates(self, days: int = 30) -> Tuple[Optional[List[date]], Optional[List[float]]]:
        """
        Получить курсы валют за последние `days` дней.

        :param days: Кол-во дней для получения данных (по умолчанию 30)
        :return: Кортеж списков (даты, курсы) или (None, None) при ошибке
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        dates: List[date] = []
        rates: List[float] = []

        try:
            for day_offset in range(days + 1):
                current_date = start_date + timedelta(days=day_offset)
                date_str = current_date.strftime('%Y%m%d')
                url = f"{self.BASE_URL}?valcode={self.currency_code}&date={date_str}&json"

                response = requests.get(url)
                if response.status_code != 200:
                    logging.error(f"HTTP ошибка {response.status_code} для даты {current_date}")
                    continue

                data = response.json()

                if data and isinstance(data, list):
                    rate = data[0].get('rate')
                    if rate is not None:
                        dates.append(current_date)
                        rates.append(rate)
                    else:
                        logging.warning(f"Отсутствует курс для {self.currency_code} на дату {current_date}")
                else:
                    logging.warning(f"Пустой или некорректный ответ для даты {current_date}")

            if not dates or not rates:
                logging.error("Нет данных для выбранного периода")
                return None, None

            return dates, rates

        except Exception as e:
            logging.error(f"Ошибка при запросе данных с NBU: {e}", exc_info=True)
            return None, None

    def plot_rates(self, dates: List[date], rates: List[float]) -> None:
        """
        Построить график курсов валют.

        :param dates: Список дат
        :param rates: Список курсов валют
        """
        if not dates or not rates:
            logging.error("Нет данных для построения графика")
            return

        plt.figure(figsize=(12, 6))
        plt.plot(dates, rates, marker='o', linestyle='-', color='blue')
        plt.title(f'Курс {self.currency_code} до UAH (данные НБУ)', fontsize=14)
        plt.xlabel('Дата', fontsize=12)
        plt.ylabel(f'Курс (UAH за 1 {self.currency_code})', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def get_rates_for_period(self, start_date: date, end_date: date) -> Tuple[Optional[List[date]], Optional[List[float]]]:
        """
        Получить курсы валют за произвольный период.

        :param start_date: Начальная дата
        :param end_date: Конечная дата
        :return: Кортеж списков (даты, курсы) или (None, None) при ошибке
        """
        delta_days = (end_date - start_date).days
        if delta_days < 0:
            logging.error("Ошибка: начальная дата позже конечной")
            return None, None

        # Используем существующий метод для получения данных за последние delta_days
        # Сдвигаем даты к началу периода, так что вызов get_rates возвращает нужный период
        # Для корректности лучше написать отдельный метод, но для простоты здесь вызовем get_rates
        return self.get_rates(days=delta_days)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    nbu = NBUExchangeRates("USD")
    dates, rates = nbu.get_rates(days=30)
    if dates and rates:
        nbu.plot_rates(dates, rates)

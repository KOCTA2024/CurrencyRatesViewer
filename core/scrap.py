import requests
from datetime import datetime


class ExchangeRateAPIClient:
    BASE_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory"

    def __init__(self):
        pass

    def get_symbols(self) -> dict:
        """
        Получить список всех доступных валют, кроме UAH.
        :return: словарь вида {"symbols": {код: код, ...}}
        """
        url = f"{self.BASE_URL}/exchange?json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        symbols = {item['cc']: item['cc'] for item in data if item['cc'] != "UAH"}
        return {"symbols": symbols}

    def get_rate_to_uah(self, base_currency: str) -> dict:
        """
        Получить курс заданной валюты к гривне (UAH).
        :param base_currency: код валюты, например "USD"
        :return: словарь с курсом
        """
        url = f"{self.BASE_URL}/exchange?valcode={base_currency}&json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not data:
            raise ValueError(f"Курс {base_currency} не найден.")

        rate_info = data[0]
        return {
            "base": rate_info["cc"],
            "currency": "UAH",
            "rate": rate_info["rate"],
            "date": rate_info["exchangedate"]
        }

    def get_current_rates(self, symbols: list) -> dict:
        """
        Получить текущие курсы нескольких валют к гривне.
        :param symbols: список валют, например ["USD", "EUR"]
        :return: словарь вида {код: курс}
        """
        url = f"{self.BASE_URL}/exchange?json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        result = {}
        for item in data:
            code = item['cc']
            if code in symbols:
                result[code] = item['rate']

        return result


# Пример использования
if __name__ == "__main__":
    client = NBUExchangeRateAPIClient()

    symbols = client.get_symbols()
    print("Доступные валюты:", symbols)

    current = client.get_current_rates(["USD", "EUR"])
    print("Текущие курсы:", current)

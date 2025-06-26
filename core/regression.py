import numpy as np
from datetime import date
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from typing import List, Optional

class RatePredictor:
    """
    Клас для прогнозування курсу валюти на основі історичних даних
    з використанням поліноміальної регресії.
    """

    @staticmethod
    def predict_rate(dates: List[date], rates: List[float], degree: int = 2) -> Optional[float]:
        if len(dates) < 2 or len(rates) < 2:
            return None

        # Перетворюємо дати в числові дні з початку періоду
        X = np.array([(d - dates[0]).days for d in dates]).reshape(-1, 1)
        y = np.array(rates)

        # Створюємо поліноміальні ознаки
        poly = PolynomialFeatures(degree=degree)
        X_poly = poly.fit_transform(X)

        model = LinearRegression()
        model.fit(X_poly, y)

        # Прогнозуємо курс на наступний день
        next_day = np.array([[X[-1][0] + 1]])
        next_day_poly = poly.transform(next_day)
        prediction = model.predict(next_day_poly)[0]

        return round(float(prediction), 4)

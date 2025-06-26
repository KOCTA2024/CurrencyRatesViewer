import json
import os

CONFIG_PATH = "cfgs/config.json"


def load_config() -> dict:
    """
    Загружает конфигурацию из файла JSON.
    Если файл не существует, возвращает пустой словарь.
    """
    if not os.path.exists(CONFIG_PATH):
        return {}

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict) -> None:
    """
    Сохраняет конфигурацию в файл JSON с отступами для удобства чтения.
    """
    # Создаем директорию, если ее нет
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

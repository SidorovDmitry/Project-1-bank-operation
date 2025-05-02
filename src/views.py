import json
import logging
from typing import Any, Dict

from config import PATH_TO_FILE, PATH_TO_FILE_JSON
from src.utils import (get_card_with_spent, get_date_time, get_path_and_period, get_stocks, get_time_for_greeting,
                       get_top_transactions, get_usd_eur)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="../logs/views.log",
    filemode="w",
    encoding="utf-8",
)

# Создаем логеры для различных компонентов программы
views_loger = logging.getLogger("views")


def main_str(date_time: str) -> Dict[str, Any]:
    """Функция для страницы «Главная» принимает на вход строку с датой и временем в формате
    YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ"""
    try:
        # Записываем сообщение о запуске приложения
        views_loger.info("Запуск приложения")
        greeting = get_time_for_greeting()
        time_period: str = get_date_time(date_time)
        sorted_df = get_path_and_period(PATH_TO_FILE, time_period)
        cards = get_card_with_spent(sorted_df)
        top_transactions = get_top_transactions(sorted_df)
        currency_usd_euro = get_usd_eur(PATH_TO_FILE_JSON)
        stock_prices = get_stocks(PATH_TO_FILE_JSON)
        data = {
            "greeting": greeting,
            "cards": cards,
            "top_transactions": top_transactions,
            "currency_rates": currency_usd_euro,
            "stock_prices": stock_prices,
        }
        json_data = json.dumps(data, ensure_ascii=False, indent=4)
        return json_data
    except Exception as e:
        # Записываем ошибку, если произошло исключение во время выполнения программы
        views_loger.warning(f"Произошла ошибка: {e}", exc_info=True)

    finally:
        # Записываем сообщение об окончании работы приложения
        views_loger.info("Работа приложения завершена")

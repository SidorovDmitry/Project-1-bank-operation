import json
import logging
import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()
API_KEY = os.getenv("API_KEY")
ACCESS_KEY = os.getenv("API_KEY_MARKET")
url = "https://api.apilayer.com/exchangerates_data/convert"
url_stocks = f"https://api.marketstack.com/v1/eod/latest?access_key={ACCESS_KEY}"


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="../logs/utils.log",
    filemode="w",
    encoding="utf-8",
)

# Создаем логеры для различных компонентов программы
utils_loger = logging.getLogger("utils")


def get_date_time(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """Преобразует дату-время в список [начало месяца, переданная дата] в формате DD.MM.YYYY HH:MM:SS"""

    utils_loger.info("Запуск функции get_date_time")

    try:
        dt = datetime.strptime(date_time, date_format)

        # Создаем дату начала месяца с тем же временем
        start_of_month = dt.replace(day=1)

        # Форматируем обе даты
        return [start_of_month.strftime("%d.%m.%Y %H:%M:%S"), dt.strftime("%d.%m.%Y %H:%M:%S")]

    except ValueError as e:
        error_msg = "Введите дату в виде строки в формате YYYY-MM-DD HH:MM:SS"
        utils_loger.error(f"{error_msg}. Ошибка: {str(e)}")
        raise ValueError(error_msg) from e

    finally:
        utils_loger.info("Завершение функции get_date_time")


def get_path_and_period(path_to_file: str, period_date: list) -> DataFrame:
    """Функция принимает путь к Excel-файлу, список дат и возвращает таблицу с датами в принимаемом периоде"""

    try:
        utils_loger.info("Запускаем работу функции get_path_and_period")
        df = pd.read_excel(path_to_file, sheet_name="Отчет по операциям")
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
        start_date = datetime.strptime(period_date[0], "%d.%m.%Y %H:%M:%S")
        end_date = datetime.strptime(period_date[1], "%d.%m.%Y %H:%M:%S")
        filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]
        sorted_df = filtered_df.sort_values(by="Дата операции")
        return sorted_df
    except FileNotFoundError:
        # Записываем ошибку, если произошло исключение во время выполнения программы
        utils_loger.warning("Произошла ошибка: FileNotFoundError", exc_info=True)
    finally:
        utils_loger.info("Работа функции get_path_and_period завершена")


def get_time_for_greeting() -> str:
    """Функция принимает в формате YYYY-MM-DD HH:MM:SS и возвращает приветствие, например, 'Добрый день,

    в зависимости от времени суток"""
    utils_loger.info("Запускаем работу функции get_time_for_greeting")
    try:
        user_datetime = datetime.now()
        hour_user = user_datetime.hour
        if 5 <= hour_user < 12:
            greeting_morning = "Доброе утро"
            return greeting_morning
        elif 12 <= hour_user < 18:
            greeting_day = "Добрый день"
            return greeting_day
        elif 18 <= hour_user < 22:
            greeting_evening = "Добрый вечер"
            return greeting_evening
        else:
            greeting_night = "Доброй ночи"
            return greeting_night
    except Exception as e:
        utils_loger.warning(f"Произошла ошибка: {e}", exc_info=True)
    finally:
        utils_loger.info("Работа функции get_time_for_greeting завершена")


def get_usd_eur(path_to_json: str) -> list[dict]:
    """Функция прнимает на вход path_to_json и возвращает курс валют"""

    utils_loger.info("Запускаем работу функции get_usd_eur")
    try:
        with open(path_to_json, "r", encoding="utf-8") as file:
            currency_rates: list[dict] = []
            data = json.load(file)
            currency_list = data["user_currencies"]
            amount = 1
            for currency in currency_list:
                try:
                    payload = {"amount": f"{amount}", "from": f"{currency}", "to": "RUB"}
                    headers = {"apikey": f"{API_KEY}"}
                    response = requests.get(url, headers=headers, params=payload)
                    status_code = response.status_code
                    if status_code == 200:
                        result = response.json()
                        currency_code_response = result["query"]["from"]
                        currency_amount = round(result["result"], 2)

                        currency_rates.append(
                            {"currency": f"{currency_code_response}", "rate": f"{round(currency_amount, 2)}"}
                        )
                    else:
                        print(status_code)
                except requests.exceptions.RequestException:
                    utils_loger.error("Ошибка конвертации валюты")
            return currency_rates
    except Exception as e:
        utils_loger.warning(f"Произошла ошибка: {e}", exc_info=True)
    finally:
        utils_loger.info("Работа функции get__usd_eur завершена")


def get_stocks(path_to_json: str) -> list[dict[str, str]]:
    """Функция принимает на вход путь к json файлу и возвращает цены на акции"""

    utils_loger.info("Запускаем работу функции get_stocks")
    try:
        with open(path_to_json, "r", encoding="utf-8") as file:
            utils_loger.info("Открываем файл с данными для запроса")
            stocks_prices = []
            data = json.load(file)
            stocks_list = data["user_stocks"]
            for stock in stocks_list:
                querystring = {"symbols": f"{stock}"}
                response = requests.get(url_stocks, params=querystring)
                status_code = response.status_code
                if status_code == 200:
                    data = response.json()
                    stocks_price = data["data"][0]["high"]
                    stocks_prices.append({"stock": f"{stock}", "price": f"{stocks_price}"})
                    utils_loger.info("Запрос успешен")
                else:
                    utils_loger.error(f"Запрос не успешен, статус-код: {status_code}")
                    print(status_code)
            return stocks_prices
    except Exception as e:
        # Записываем ошибку, если произошло исключение во время выполнения программы
        utils_loger.warning(f"Произошла ошибка: {e}", exc_info=True)
    finally:
        utils_loger.info("Работа функции get_stocks завершена")


def get_top_transactions(sorted_df: DataFrame) -> list[dict]:
    """Функция принимает датафрейм и возвращает 5 топ-транзакций по сумме платежа"""

    utils_loger.info("Запускаем работу функции get_top_transactions")
    try:
        top_pay_transactions = []
        sorted_pay_df = sorted_df.sort_values(by="Сумма платежа", ascending=False)
        top_transactions = sorted_pay_df.head(5)
        top_transactions_sorted = top_transactions[
            ["Дата платежа", "Сумма платежа", "Категория", "Описание"]
        ]  # .to_dict(orient='records')
        # formatted_json = json.dumps(result, ensure_ascii=False, indent=2)
        for index, row in top_transactions_sorted.iterrows():
            row = {
                "date": f"{row['Дата платежа']}",
                "amount": row["Сумма платежа"],
                "category": f"{row['Категория']}",
                "description": f"{row['Описание']}",
            }
            top_pay_transactions.append(row)
        return top_pay_transactions
    except Exception as e:
        # Записываем ошибку, если произошло исключение во время выполнения программы
        utils_loger.warning(f"Произошла ошибка: {e}", exc_info=True)
    finally:
        utils_loger.info("Работа функции get_top_transactions завершена")


def get_card_with_spent(sorted_df: DataFrame) -> list[dict]:
    """Функция принимает DataFrame и возвращает список карт с расходами"""

    utils_loger.info("Запускаем работу функции get_card_with_spent")
    try:
        card_spent_transactions = []
        card_sorted = sorted_df[["Номер карты", "Сумма платежа", "Кэшбэк", "Сумма операции с округлением"]]
        for index, row in card_sorted.iterrows():
            if row["Сумма платежа"] < 0:
                last_digits = str(row["Номер карты"]).replace("*", "")
                total_spent = row["Сумма операции с округлением"]
                cashback = total_spent // 100
                row = {"last_digits": last_digits, "total_spent": total_spent, "cashback": cashback}
                card_spent_transactions.append(row)
            else:
                utils_loger.info("В расчет принимаем только расходы")
        df = pd.DataFrame(card_spent_transactions)
        df = df[df["last_digits"] != "nan"]

        # Группируем по 'last_digits' и суммируем 'total_spent' и 'cashback'
        result = df.groupby("last_digits", as_index=False).agg({"total_spent": "sum", "cashback": "sum"})
        result_list = result.to_dict(orient="records")
        return result_list
    except Exception as e:
        # Записываем ошибку, если произошло исключение во время выполнения программы
        utils_loger.warning(f"Произошла ошибка: {e}", exc_info=True)
    finally:
        utils_loger.info("Работа функции get_card_with_spent завершена")

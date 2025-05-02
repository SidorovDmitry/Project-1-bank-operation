import json
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

from src.utils import (get_card_with_spent, get_date_time, get_path_and_period, get_stocks, get_time_for_greeting,
                       get_top_transactions, get_usd_eur)


@pytest.mark.parametrize(
    "input_date, expected_output",
    [
        ("2023-10-15 14:30:00", ["01.10.2023 14:30:00", "15.10.2023 14:30:00"]),
        ("2023-02-28 23:59:59", ["01.02.2023 23:59:59", "28.02.2023 23:59:59"]),
    ],
)
def test_get_date_time(input_date, expected_output):
    assert get_date_time(input_date) == expected_output


def test_get_date_time_invalid_date():
    with pytest.raises(ValueError) as exc_info:
        get_date_time("2023-13-01 00:00:00")  # Некорректный месяц
    assert "Введите дату в виде строки в формате YYYY-MM-DD HH:MM:SS" in str(exc_info.value)


def test_get_path_and_period_correct_data(monkeypatch, test_dataframe):
    # Мокируем pd.read_excel, чтобы возвращать test_dataframe
    monkeypatch.setattr(pd, "read_excel", lambda *args, **kwargs: test_dataframe)

    # Входные данные
    path_to_file = "../data/operations.xlsx"
    period_date = ["01.05.2018 15:30:00", "20.05.2018 15:30:00"]

    # Ожидаемый результат
    expected_data = {
        "Дата операции": "2018-05-01 16:49:16",
        "Дата платежа": "03.05.2018",
        "Номер карты": "*7197",
        "Статус": "OK",
        "Сумма операции": -296.8,
        "Валюта операции": "RUB",
        "Сумма платежа": -296.8,
        "Валюта платежа": "RUB",
        "Кэшбэк": 5,
        "Категория": "Фастфуд",
        "MCC": 5814.0,
        "Описание": "Бургер Кинг",
        "Бонусы (включая кэшбэк)": 5,
        "Округление на инвесткопилку": 0,
        "Сумма операции с округлением": 296.8,
    }
    expected_df = pd.DataFrame(expected_data, index=[0])
    expected_df["Дата операции"] = pd.to_datetime(expected_df["Дата операции"], format="%Y-%m-%d %H:%M:%S")

    # Вызов функции
    result = get_path_and_period(path_to_file, period_date)

    # Проверка результата
    assert result is not None, "Функция вернула None"
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_df.reset_index(drop=True))


def test_get_path_and_period_invalid_data(monkeypatch):
    # Мокируем pd.read_excel, чтобы вызвать исключение
    monkeypatch.setattr(
        pd,
        "read_excel",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError("Произошла ошибка: FileNotFoundError")),
    )

    # Входные данные
    path_to_file = "invalid_file.xlsx"
    period_date = ["01.10.2023 00:00:00", "20.10.2023 23:59:59"]

    # Вызов функции
    result = get_path_and_period(path_to_file, period_date)

    # Проверка, что функция вернула None
    assert result is None, "Функция не вернула None при ошибке."


def test_get_time_for_greeting_morning():
    # Фиксируем время (08:30 утра)
    fake_now = datetime(2023, 10, 15, 8, 30, 0)  # Утро (5:00 - 11:59)

    # Заменяем datetime.now() на наше фиктивное время
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = fake_now
        result = get_time_for_greeting()  # Вызываем без аргументов
        assert result == "Доброе утро"


def test_get_time_for_greeting_afternoon():
    # Фиксируем время (14:00 дня)
    fake_now = datetime(2023, 10, 15, 14, 0, 0)  # День (12:00 - 17:59)

    # Заменяем datetime.now() на наше фиктивное время
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = fake_now
        assert get_time_for_greeting() == "Добрый день"


def test_get_time_for_greeting_evening():
    # Фиксируем время (19:00 вечера)
    fake_now = datetime(2023, 10, 15, 19, 0, 0)

    # Заменяем datetime.now() на наше фиктивное время
    with patch("src.utils.datetime") as mock_datatime:
        mock_datatime.now.return_value = fake_now
        assert get_time_for_greeting() == "Добрый вечер"


def test_get_time_for_greeting_night():
    # Фиксируем время (1:00 ночи)
    fake_now = datetime(2023, 10, 15, 1, 0, 0)

    # Заменяем datetime.now() на наше фиктивное время
    with patch("src.utils.datetime") as mock_datatime:
        mock_datatime.now.return_value = fake_now
        assert get_time_for_greeting() == "Доброй ночи"


def test_get_time_for_greeting_logging(mocker):
    # Мокируем логгер и datetime
    mock_logger = mocker.patch("src.utils.utils_loger")
    mock_datetime = mocker.patch("src.utils.datetime")

    # Настраиваем mock для datetime.now()
    fake_time = datetime(2023, 10, 15, 8, 30, 0)
    mock_datetime.now.return_value = fake_time

    # Вызываем функцию (без аргументов)
    result = get_time_for_greeting()

    # Проверяем логирование
    mock_logger.info.assert_any_call("Запускаем работу функции get_time_for_greeting")
    mock_logger.info.assert_any_call("Работа функции get_time_for_greeting завершена")

    # Проверяем обработку ошибки (имитируем исключение)
    mock_datetime.now.side_effect = Exception("Test error")
    get_time_for_greeting()
    mock_logger.warning.assert_called_with("Произошла ошибка: Test error", exc_info=True)


def test_get_usd_eur_success(mocker):
    # Мокируем открытие файла и чтение JSON
    mock_json_data = {"user_currencies": ["USD"]}
    mock_file = mocker.mock_open(read_data=json.dumps(mock_json_data))
    mocker.patch("builtins.open", mock_file)

    # Мокируем requests.get
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": {"from": "USD"}, "result": 75.50}
    mocker.patch("requests.get", return_value=mock_response)

    # Вызов функции
    result = get_usd_eur("../data/user_settings.json")

    # Ожидаемый результат
    expected_result = [
        {"currency": "USD", "rate": "75.5"},
    ]

    # Проверка результата
    assert result == expected_result


def test_get_usd_eur_invalid_json(mocker):
    # Мокируем открытие файла с некорректным JSON
    mock_file = mocker.mock_open(read_data="invalid_json")
    mocker.patch("builtins.open", mock_file)

    # Вызов функции
    result = get_usd_eur("invalid_path.json")

    # Проверка, что функция вернула None
    assert result is None


def test_get_usd_eur_bad_status_code(mocker):
    # Мокируем открытие файла и чтение JSON
    mock_json_data = {"user_currencies": ["USD"]}
    mock_file = mocker.mock_open(read_data=json.dumps(mock_json_data))
    mocker.patch("builtins.open", mock_file)

    # Мокируем requests.get с некорректным статусом
    mock_response = Mock()
    mock_response.status_code = 404
    mocker.patch("requests.get", return_value=mock_response)

    # Вызов функции
    result = get_usd_eur("../data/user_settings.json")

    # Проверка, что функция вернула []
    assert result == []


def test_get_top_transactions_correct_data(df_data):

    result = get_top_transactions(df_data)

    # Ожидаемый результат
    expected_result = [
        {"date": "04.05.2018", "amount": -58.0, "category": "Фастфуд", "description": "McDonald's"},
        {"date": "03.05.2018", "amount": -69.9, "category": "Фастфуд", "description": "Бургер Кинг"},
        {"date": "02.05.2018", "amount": -208.0, "category": "Ж/д билеты", "description": "Московский метрополитен"},
        {"date": "04.05.2018", "amount": -221.27, "category": "Супермаркеты", "description": "Пятёрочка"},
        {"date": "05.05.2018", "amount": -250.0, "category": "Связь", "description": "МТС"},
    ]

    # Проверка результата
    assert result == expected_result


def test_get_card_with_spent_correct_data(df_data):
    # Вызов функции
    result = get_card_with_spent(df_data)

    # Ожидаемый результат
    expected_result = [
        {"last_digits": "4556", "total_spent": 250.0, "cashback": 2.0},
        {"last_digits": "7197", "total_spent": 31869.55, "cashback": 312.0},
    ]

    # Проверка результата
    assert result == expected_result


def test_get_stocks_correct_data(mocker):
    # Мокируем открытие файла и чтение JSON
    mock_json_data = {"user_stocks": ["AAPL"]}
    mock_file = mocker.mock_open(read_data=json.dumps(mock_json_data))
    mocker.patch("builtins.open", mock_file)

    # Мокируем requests.get
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "pagination": {"limit": 100, "offset": 0, "count": 100, "total": 9944},
        "data": [
            {
                "open": 129.8,
                "high": 133.04,
                "low": 129.47,
                "close": 132.995,
                "volume": 106686703.0,
                "adj_high": 133.04,
                "adj_low": 129.47,
                "adj_close": 132.995,
                "adj_open": 129.8,
                "adj_volume": 106686703.0,
                "split_factor": 1.0,
                "dividend": 0.0,
                "symbol": "AAPL",
                "exchange": "XNAS",
                "date": "2021-04-09T00:00:00+0000",
            },
        ],
    }
    mocker.patch("requests.get", return_value=mock_response)

    # Вызов функции
    result = get_stocks("fake_path.json")

    # Ожидаемый результат
    expected_result = [
        {"stock": "AAPL", "price": "133.04"},
    ]

    # Проверка результата
    assert result == expected_result


def test_get_stocks_http_error(mocker):
    # Мокируем открытие файла и чтение JSON
    mock_json_data = {"user_stocks": ["AAPL", "GOOGL"]}
    mock_file = mocker.mock_open(read_data=json.dumps(mock_json_data))
    mocker.patch("builtins.open", mock_file)

    # Мокируем requests.get, чтобы вызвать исключение
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Ошибка сети"))

    # Вызов функции
    result = get_stocks("fake_path.json")

    # Проверка, что функция вернула None
    assert result is None

import json
import logging
import os
from datetime import datetime
from io import StringIO

from src.reports import report_decorator, spending_by_category


# Настройка логирования для тестов
def setup_logging():
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    # Настраиваем логгер reports_loger
    reports_loger = logging.getLogger("reports")
    reports_loger.setLevel(logging.DEBUG)
    reports_loger.addHandler(handler)

    return log_stream


# Тесты
def test_file_creation_with_name():
    log_stream = setup_logging()
    test_filename = "test_name_report.json"

    @report_decorator(test_filename)
    def test_function():
        return {"key": "value"}

    test_function()
    assert os.path.exists(test_filename)

    with open(test_filename, "r", encoding="utf-8") as file:
        content = json.load(file)
        assert content == {"key": "value"}

    os.remove(test_filename)
    logs = log_stream.getvalue()
    assert f"Отчет сохранен в {test_filename}" in logs


# Тест на функцию spending_by_category
def test_spending_by_category(test_dataframe):
    log_stream = setup_logging()

    category = "Фастфуд"
    date = "03.05.2018"

    # Преобразуем дату в нужный формат
    date = datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")

    # Вызываем функцию
    result = spending_by_category(test_dataframe, category, date)

    # Проверяем результат
    assert result == {"Фастфуд": 296.8}

    # Проверяем логи
    logs = log_stream.getvalue()
    assert "Запуск функции spending_by_category" in logs
    assert "Работа приложения завершена" in logs

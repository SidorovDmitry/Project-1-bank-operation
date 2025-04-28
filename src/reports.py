import functools
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="../logs/reports.log",
    filemode="w",
    encoding="utf-8",
)

reports_loger = logging.getLogger("reports")


def report_decorator(filename=None):
    """Декоратор для функций-отчетов, который записывает результат в файл.
    Если имя файла не передано, используется имя по умолчанию."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Формируем имя файла
            if filename is None:
                report_filename = f"report_{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            else:
                report_filename = filename

            # Записываем результат в файл
            with open(report_filename, "w", encoding="utf-8") as file:
                if isinstance(result, pd.DataFrame):
                    result.to_json(file, orient="records", lines=True, force_ascii=False)
                else:
                    json.dump(result, file, indent=4, ensure_ascii=False)

            reports_loger.info(f"Отчет сохранен в {report_filename}")
            return result

        return wrapper

    return decorator


@report_decorator("report_spending_by_category.json")
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str]) -> dict | None:
    """Функция возвращает траты по заданной категории за последние три месяца."""

    try:
        reports_loger.info(f"Запуск функции spending_by_category с категорией: {category} и датой: {date}")
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            reports_loger.info(f"Дата не передана, используется текущая дата: {date}")

        # Преобразуем дату в формат datetime
        end_date = datetime.strptime(date, "%Y-%m-%d")
        reports_loger.info("Преобразуем дату в формат datetime")
        start_date = end_date - timedelta(days=90)
        if not pd.api.types.is_datetime64_any_dtype(transactions["Дата платежа"]):
            transactions["Дата платежа"] = pd.to_datetime(transactions["Дата платежа"], dayfirst=True)
            reports_loger.info("Столбец 'Дата платежа' преобразован в формат datetime")
        # Фильтруем транзакции по категории и дате
        filtered_transactions = transactions[
            (transactions["Категория"] == category)
            & (transactions["Дата платежа"] >= start_date.strftime("%Y-%m-%d"))
            & (transactions["Дата платежа"] <= end_date.strftime("%Y-%m-%d"))
        ]
        expenses_by_category = filtered_transactions.groupby("Категория")["Сумма операции с округлением"].sum()
        reports_loger.info("Группируем данные по категории и сумме платежа")
        result = expenses_by_category.to_dict()
        return result
    except Exception as e:
        # Записываем ошибку, если произошло исключение во время выполнения программы
        reports_loger.warning(f"Произошла ошибка: {e}", exc_info=True)

    finally:
        # Записываем сообщение об окончании работы приложения
        reports_loger.info("Работа приложения завершена")

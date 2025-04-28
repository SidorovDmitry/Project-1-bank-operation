import pandas as pd
from pandas import DataFrame

from config import PATH_TO_FILE
from src.reports import spending_by_category
from src.services import analyze_cashback
from src.views import main_str

if __name__ == "__main__":
    # Вызов функции main_str из модуля views
    date_request = "2018-05-20 15:30:00"
    result_views = main_str(date_request)
    print(result_views)

    # Вызов функции spending_by_category с декоратором report_decorator из модуля reports
    df: DataFrame = pd.read_excel(PATH_TO_FILE, sheet_name="Отчет по операциям")
    result_reports = spending_by_category(df, "Фастфуд", "2018-04-15")
    print(result_reports)

    # Вызов функции analyze_cashback из модуля services
    result_services = analyze_cashback(PATH_TO_FILE, 2018, 5)
    print(result_services)

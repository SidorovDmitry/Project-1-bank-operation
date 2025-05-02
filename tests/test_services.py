import json

from src.services import analyze_cashback


def test_analyze_cashback_correct_data(mocker, test_dataframe):
    # Мокируем открытие файла и чтение данных
    mocker.patch("pandas.read_excel", return_value=test_dataframe)

    # Вызов функции
    result = analyze_cashback("../data/operations.xlsx", 2018, 5)

    # Ожидаемый результат
    expected_result = {
        "Фастфуд": 2,
    }

    # Проверка результата
    assert json.loads(result) == expected_result


def test_analyze_cashback_file_read_error(mocker):
    # Мокируем ошибку при чтении файла
    mocker.patch("pandas.read_excel", side_effect=Exception("Ошибка чтения файла"))

    # Вызов функции
    result = analyze_cashback("fake_path.xlsx", 2018, 5)

    # Проверка, что функция вернула пустой словарь
    assert result == {}

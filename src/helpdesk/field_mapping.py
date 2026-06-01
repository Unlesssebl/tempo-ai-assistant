"""
Маппинг полей IntraService для сервиса 106 и типа 1020.
"""

# Соответствие системных имен полей их ID в IntraService (для типа 1020)
INTRASERVICE_FIELDS = {
    "room": "Field1143",  # Номер кабинета
    "phone": "Field1144",  # Телефонный номер для связи
    "pc_name": "Field1145",  # Номер компьютера
    "department": "Field1195",  # Подразделение
    "position": "Field1196",  # Должность
    "last_name": "Field1388",  # Фамилия
    "first_name": "Field1389",  # Имя
    "middle_name": "Field1390",  # Отчество
    "email": "Field1490",  # Электронная почта
    "organization": "CategoryIds",  # Организация (через категории)
}

# Значения по умолчанию для обязательных полей, если они не найдены
DEFAULT_VALUES = {
    "organization": "57",  # АО "НТЗ "ТЭМ-ПО"
}

import logging
import os
import socket
from typing import Any, Dict

logger = logging.getLogger(__name__)


class UserProfileProvider:
    """Предоставляет данные профиля пользователя из AD и системы."""

    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Получает данные из ОС (имя ПК, логин)."""
        return {
            "pc_name": socket.gethostname(),
            "login": os.getlogin() or os.environ.get("USERNAME", "unknown"),
        }

    @staticmethod
    def get_ad_info() -> Dict[str, Any]:
        """
        Пытается получить данные из AD текущего пользователя.
        В реальной среде здесь будет вызов ldap3 или поиск по AD.
        Сейчас возвращаем базовые данные на основе системных переменных.
        """
        # В Windows многие данные AD доступны через переменные окружения или системные вызовы
        # Для полноценной реализации требуется ldap3, но пока соберем что можем.
        os.environ.get("USERDNSDOMAIN", "")

        # Заглушка: в реальной интеграции здесь будет поиск по LDAP
        # Если интеграция с AD еще не настроена, возвращаем пустые значения для ручного ввода
        return {
            "last_name": "",
            "first_name": "",
            "middle_name": "",
            "department": os.environ.get("USERDOMAIN", ""),
            "position": "",
            "email": "",
        }

    @classmethod
    def get_combined_profile(cls) -> Dict[str, Any]:
        """Объединяет системные данные и данные AD."""
        profile = cls.get_system_info()
        profile.update(cls.get_ad_info())
        return profile

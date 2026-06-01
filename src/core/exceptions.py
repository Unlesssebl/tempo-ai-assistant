"""
Кастомные исключения для ассистента
"""


class AssistantError(Exception):
    """Базовое исключение для ассистента"""

    pass


class SearchError(AssistantError):
    """Ошибка поиска в RAG"""

    pass


class LLMError(AssistantError):
    """Ошибка обращения к LLM"""

    pass


class AudioError(AssistantError):
    """Ошибка обработки голоса"""

    pass


class ConfigError(AssistantError):
    """Ошибка конфигурации"""

    pass

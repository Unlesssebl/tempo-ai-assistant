"""
Утилиты для морфологического анализа и лемматизации русского языка.
"""

import logging
from typing import List

try:
    import pymorphy3
except ImportError:
    pymorphy3 = None

logger = logging.getLogger(__name__)


class RussianMorphology:
    """
    Класс-синглтон для лемматизации русского текста с использованием pymorphy3.
    """

    _instance = None
    _morph = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RussianMorphology, cls).__new__(cls)
            if pymorphy3:
                try:
                    cls._morph = pymorphy3.MorphAnalyzer()
                except Exception as e:
                    logger.error(f"Failed to initialize Pymorphy3 MorphAnalyzer: {e}")
                    cls._morph = None
            else:
                logger.warning("Pymorphy3 is not installed. Lemmatization will be disabled.")
        return cls._instance

    def lemmatize_word(self, word: str) -> str:
        """Приводит слово к нормальной форме (лексеме)."""
        if not self._morph:
            return word.lower()

        # Получаем разбор слова и берем первый вариант (самый вероятный)
        parsed = self._morph.parse(word.lower())
        if not parsed:
            return word.lower()

        return parsed[0].normal_form

    def lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """Лемматизирует список токенов."""
        return [self.lemmatize_word(t) for t in tokens]

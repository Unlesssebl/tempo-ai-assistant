"""
LLM-based reranker (cross-encoder style).
"""

from typing import Dict, List

from src.core.config import Config
from src.llm.text import TextLLMService


class LLMReranker:
    """Cross-encoder reranking через LLM."""

    BATCH_RERANK_PROMPT = """Твоя задача — отобрать наиболее релевантные документы для ответа на запрос пользователя.
Верни номера документов в порядке убывания их полезности, разделенные запятой.

ПРАВИЛА ОЦЕНКИ:
1. ВЫСОКАЯ релевантность: Документ прямо отвечает на вопрос или содержит точные данные (ФИО, телефон, адрес, пункт приказа).
2. СРЕДНЯЯ релевантность: Документ описывает общую тему запроса, но не содержит прямого ответа.
3. НИЗКАЯ релевантность (ШУМ): Документ содержит те же слова, но относится к другой теме (например, вопрос про автобус, а документ про базу отдыха, где просто упоминается парковка автобуса).

ПРИМЕРЫ:
Запрос: "Как вызвать айтишника?"
Документы: [1] Как создать заявку в HelpDesk [2] Биография директора Айти ТЭМПО [3] Ремонт компьютеров.
Результат: 1, 3, 2

Запрос: {query}

ДОКУМЕНТЫ ДЛЯ АНАЛИЗА:
{documents}

ПОРЯДОК (только номера через запятую, например 3, 1, 5):"""

    def __init__(self, config: Config):
        self.config = config
        self.llm = TextLLMService(config)

    async def rerank_batch(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """Batch reranking через один LLM вызов."""
        if len(documents) <= top_k:
            return documents

        docs_text = "\n\n".join(
            [
                f"[{i + 1}] {doc.get('text', '')[: self.config.rerank_doc_chars]}"
                for i, doc in enumerate(documents[: self.config.rerank_max_docs])
            ]
        )

        response = await self.llm.generate(
            self.BATCH_RERANK_PROMPT.format(query=query, documents=docs_text),
            temperature=0.1,
        )

        order = self._parse_order(response, len(documents))
        if not order:
            return documents[:top_k]

        reranked = [documents[i] for i in order if 0 <= i < len(documents)]
        return reranked[:top_k]

    @staticmethod
    def _parse_order(response: str, max_docs: int) -> List[int]:
        parts = [p.strip() for p in response.replace("\n", "").split(",")]
        order: List[int] = []
        for p in parts:
            if p.isdigit():
                idx = int(p) - 1
                if 0 <= idx < max_docs and idx not in order:
                    order.append(idx)
        return order

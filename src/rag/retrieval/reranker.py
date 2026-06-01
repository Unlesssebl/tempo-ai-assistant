"""
LLM-based reranker (cross-encoder style).
"""

import logging
from typing import Dict, List, Literal, Tuple
from pydantic import BaseModel, Field

from src.core.config import Config
from src.llm.text import TextLLMService

logger = logging.getLogger(__name__)


class RerankerOutput(BaseModel):
    """Схема ответа реранкера."""
    order: List[int] = Field(
        description="Индексы наиболее релевантных документов в порядке убывания их полезности."
    )
    status: Literal["CORRECT", "INCORRECT"] = Field(
        description="'CORRECT' если в документах есть ответ или полезная информация, иначе 'INCORRECT'."
    )


class LLMReranker:
    """Cross-encoder reranking через LLM."""

    BATCH_RERANK_PROMPT = """Твоя задача — отобрать наиболее релевантные документы для ответа на запрос пользователя.
Определи порядок релевантных документов и статус наличия ответа.

ПРАВИЛА ОЦЕНКИ:
1. ВЫСОКАЯ релевантность: Документ прямо отвечает на вопрос или содержит точные данные (ФИО, телефон, адрес, пункт приказа).
2. СРЕДНЯЯ релевантность: Документ описывает общую тему запроса, но не содержит прямого ответа.
3. НИЗКАЯ релевантность (ШУМ): Документ содержит те же слова, но относится к другой теме (например, вопрос про автобус, а документ про базу отдыха, где просто упоминается парковка автобуса).
4. ОБЯЗАТЕЛЬНО учитывай системные подсказки в скобках. Документы с пометкой о точном совпадении имеют наивысший приоритет.

ПРИМЕР:
Запрос: "Как вызвать айтишника?"
Документы: [0] Как создать заявку в HelpDesk [1] Биография директора Айти ТЭМПО [2] Ремонт компьютеров.
Результат JSON:
{{
  "order": [0, 2, 1],
  "status": "CORRECT"
}}

Запрос: {query}

ДОКУМЕНТЫ ДЛЯ АНАЛИЗА:
{documents}
"""

    def __init__(self, config: Config):
        self.config = config
        self.llm = TextLLMService(config)

    async def rerank_batch(self, query: str, documents: List[Dict], top_k: int) -> Tuple[List[Dict], str]:
        """Batch reranking через один LLM вызов."""
        if not documents:
            return [], "incorrect"

        docs_list = []
        for i, doc in enumerate(documents[: self.config.rerank_max_docs]):
            metadata = doc.get("metadata") or {}
            system_hints = metadata.get("system_hints", [])
            hints_str = ""
            if system_hints and isinstance(system_hints, list):
                hints_str = f"(Подсказка системы: {', '.join(system_hints)}) "
            
            doc_text = doc.get('text', '')[: self.config.rerank_doc_chars]
            docs_list.append(f"[{i}] {hints_str}{doc_text}")

        docs_text = "\n\n".join(docs_list)

        try:
            response = await self.llm.generate_structured(
                prompt=self.BATCH_RERANK_PROMPT.format(query=query, documents=docs_text),
                response_schema=RerankerOutput,
                temperature=0.1,
            )
            order = response.order
            status = response.status.strip().lower()
        except Exception as e:
            logger.warning(f"Reranking failed, using original order: {e}")
            order = list(range(len(documents)))
            status = "correct"

        # Восстанавливаем порядок
        reranked: List[Dict] = []
        seen = set()
        for idx in order:
            if 0 <= idx < len(documents) and idx not in seen:
                reranked.append(documents[idx])
                seen.add(idx)

        # Добавляем упущенные документы
        for i, doc in enumerate(documents):
            if i not in seen:
                reranked.append(doc)

        return reranked[:top_k], status


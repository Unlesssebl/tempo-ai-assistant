"""
CRAG: Corrective Retrieval-Augmented Generation.
"""

from typing import Dict, List, Tuple

from src.core.config import Config
from src.llm.text import TextLLMService
from src.rag.retrieval.hybrid_search import HybridSearchService


class CRAGEvaluator:
    """Оценка качества retrieval и корректировка запроса."""

    EVAL_PROMPT = (
        "Оцени, содержат ли найденные документы информацию для ответа на вопрос.\n\n"
        "Вопрос: {query}\n\n"
        "Найденные документы:\n{documents}\n\n"
        "Оценка:\n"
        "- CORRECT: документы содержат релевантную информацию\n"
        "- INCORRECT: документы не релевантны вопросу\n"
        "- AMBIGUOUS: частично релевантны, нужна дополнительная информация\n\n"
        "Ответь ОДНИМ словом (CORRECT/INCORRECT/AMBIGUOUS):"
    )

    REFINE_PROMPT = (
        "Вопрос пользователя: {query}\n\n"
        "Найденные документы оказались нерелевантны. "
        "Предложи уточненную формулировку запроса для повторного поиска.\n\n"
        "Уточненный запрос:"
    )

    def __init__(self, config: Config):
        self.config = config
        self.llm = TextLLMService(config)

    async def evaluate_and_correct(
        self, query: str, documents: List[Dict], search_service: HybridSearchService
    ) -> Tuple[List[Dict], str]:
        """Оценивает retrieval и корректирует запрос при необходимости."""
        if not documents:
            return documents, "empty"

        docs_text = "\n---\n".join([d.get("text", "")[: self.config.rag.crag_doc_chars] for d in documents[: self.config.crag_max_docs]])
        evaluation = await self.llm.generate(self.EVAL_PROMPT.format(query=query, documents=docs_text), temperature=0.1)
        evaluation = evaluation.strip().upper()

        if evaluation == "CORRECT":
            return documents, "correct"

        if evaluation == "INCORRECT":
            refined_query = await self.llm.generate(self.REFINE_PROMPT.format(query=query), temperature=0.2)
            refined_query = refined_query.strip()
            if refined_query:
                new_docs = await search_service.search(refined_query, limit=self.config.rerank_max_docs)
                return new_docs, "refined"
            return documents, "incorrect"

        return documents, "ambiguous"

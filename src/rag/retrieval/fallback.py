"""
AdaptiveFallback Retriever: combines CRAG and HyDE principles into a single LLM call.
"""

from typing import Dict, List, Optional

from src.core.config import Config
from src.llm.text import TextLLMService
from src.rag.retrieval.hybrid_search import HybridSearchService


class FallbackRetriever:
    """Fallback retriever generating an optimized search query combining query rewriting and hypothetical context."""

    FALLBACK_PROMPT = (
        "Пользователь сделал запрос к базе знаний, но поиск не дал качественных результатов.\n"
        "Сформулируй ОДНУ оптимальную строку для векторного поиска.\n"
        "Эта строка должна объединять в себе:\n"
        "1. Переформулированную суть исходного запроса (уточнение терминов, устранение шума).\n"
        "2. Гипотетический фактологический контекст (как мог бы выглядеть фрагмент документа, содержащего ответ).\n\n"
        "Исходный запрос: {query}\n\n"
        "Сгенерируй только строку для поиска, без лишних слов, кавычек или пояснений.\n"
        "Строка для векторного поиска:"
    )

    def __init__(self, config: Config, search_service: HybridSearchService):
        self.config = config
        self.search_service = search_service
        self.llm = TextLLMService(config)

    async def execute_fallback(self, query: str, limit: int = 10, company_id: Optional[str] = None) -> List[Dict]:
        """
        Executes 1 LLM call to generate the fallback query string,
        then performs exactly 1 hybrid search vector call.
        """
        fallback_query = await self.llm.generate(
            self.FALLBACK_PROMPT.format(query=query),
            temperature=0.3
        )
        fallback_query = fallback_query.strip().strip('"\'')
        if not fallback_query:
            fallback_query = query
        return await self.search_service.search(fallback_query, limit=limit, company_id=company_id)

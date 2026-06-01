"""
HyDE: Hypothetical Document Embeddings.
"""

from typing import Dict, List

from src.core.config import Config
from src.llm.text import TextLLMService
from src.rag.retrieval.hybrid_search import HybridSearchService


class HyDERetriever:
    """HyDE retrieval: генерирует гипотетический документ и ищет по нему."""

    HYDE_PROMPT = (
        "Напиши короткий информативный текст, который мог бы содержать ответ на вопрос. "
        "Пиши как будто это фрагмент корпоративного документа.\n\n"
        "Вопрос: {query}\n\n"
        "Гипотетический документ:"
    )

    def __init__(self, config: Config, search: HybridSearchService):
        self.config = config
        self.search = search
        self.llm = TextLLMService(config)

    async def search_with_hyde(self, query: str, limit: int = 10, company_id: str = None) -> List[Dict]:
        hypothetical = await self.llm.generate(self.HYDE_PROMPT.format(query=query), temperature=0.3)
        return await self.search.search(hypothetical, limit=limit, company_id=company_id)

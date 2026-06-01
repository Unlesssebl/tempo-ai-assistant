"""
Извлечение документов из Qdrant по ссылке на источник.
"""

import asyncio
from typing import List

from qdrant_client.http.models import FieldCondition, Filter, MatchText

from src.core.clients import ClientManager
from src.core.config import Config


class SmartLinksRetriever:
    """Слой I/O: Отвечает за извлечение чанков по source (файл/папка)."""

    def __init__(self, config: Config):
        self.config = config
        self.client_manager = ClientManager.get_instance(config)

    async def fetch_by_source(self, target: str, is_folder: bool = False) -> List[str]:
        """Загрузка чанков по source (файл/папка)"""
        print(f"  -> Извлечение контекста: {'Папка' if is_folder else 'Файл'} '{target}'")

        client = self.client_manager.get_qdrant_client()

        filter_obj = Filter(must=[FieldCondition(key="source", match=MatchText(text=target))])

        loop = asyncio.get_running_loop()
        points, _ = await loop.run_in_executor(
            None,
            lambda: client.scroll(
                collection_name=self.config.collection_name,
                scroll_filter=filter_obj,
                limit=10,
                with_payload=True,
                with_vectors=False,
            ),
        )

        results = []
        for p in points:
            payload = p.payload or {}
            # Приоритет parent_text для parent-child схемы
            text = payload.get("parent_text") if self.config.use_parent_child_chunks else None
            if not text:
                text = payload.get("text", "")
            if text:
                results.append(text)
        return results

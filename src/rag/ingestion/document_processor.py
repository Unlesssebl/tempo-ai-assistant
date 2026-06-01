"""
Оркестрация обработки документов.
"""

from pathlib import Path
from typing import Dict, List, Optional

from src.core.clients import ClientManager
from src.core.config import Config
from src.rag.ingestion.document_loader import DocumentLoader
from src.rag.ingestion.semantic_chunker import SemanticChunker
from src.rag.ingestion.text_chunker import TextChunker


class DocumentProcessor:
    """Оркестратор: Координация загрузки и нарезки документов."""

    def __init__(self, config: Config):
        self.config = config
        self.loader = DocumentLoader(config)

        # Инициализация семантического чанкера отключена принудительно для стабильности Parent-Child
        semantic_chunker = None
        # if self.config.use_semantic_chunking:
        #     embedder = ClientManager.get_instance(self.config).get_embedder()
        #     semantic_chunker = SemanticChunker(embedder=embedder, threshold=self.config.semantic_similarity_threshold)

        self.chunker = TextChunker(config, semantic_chunker)

    def prepare_chunks(self, files: Optional[List[Path]] = None) -> List[Dict[str, str]]:
        """
        Основной метод: загрузка документов → chunking.
        """
        documents = self.loader.load_documents(files=files)
        chunks = self.chunker.chunk_documents(documents)

        print(f"Загружено {len(documents)} документов")
        print(f"Создано {len(chunks)} чанков")

        return chunks

    def list_document_files(self) -> List[Path]:
        """Прокси к лоадеру."""
        return self.loader.list_files()

    def load_documents(self, files: Optional[List[Path]] = None) -> List[Dict]:
        """Прокси к лоадеру."""
        return self.loader.load_documents(files=files)

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Прокси к чанкеру."""
        return self.chunker.chunk_documents(documents)

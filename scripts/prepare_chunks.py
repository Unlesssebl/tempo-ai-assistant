"""
Скрипт для предварительной подготовки чанков без векторизации.

Создаёт JSON-кэш чанков для ускорения последующей векторизации.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio  # noqa: E402

from src.core.config import Config  # noqa: E402
from src.rag.ingestion.chunks_cache import ChunksCache  # noqa: E402
from src.rag.ingestion.contextual_retrieval import ContextualChunker  # noqa: E402
from src.rag.ingestion.document_processor import DocumentProcessor  # noqa: E402


async def main():
    try:
        config = Config.from_env()
    except Exception as e:
        print(f"ОШИБКА: {e}")
        print("Скопируйте env.example в .env и заполните токены.")
        raise SystemExit(1) from e

    print("--- Подготовка чанков ---")

    # Инициализация
    processor = DocumentProcessor(config)
    cache_dir = Path(config.data_path) / ".chunks_cache"
    chunks_cache = ChunksCache(cache_dir)

    files = processor.list_document_files()
    if not files:
        print("ВНИМАНИЕ: Не найдено документов для обработки!")
        return

    print(f"Найдено документов: {len(files)}")

    def make_chunker(proc: DocumentProcessor):
        """Создаёт функцию chunking без проблем с замыканием."""

        def chunker_fn(path: Path):
            doc = proc.load_documents(files=[path])
            return proc.chunk_documents(doc) if doc else []

        return chunker_fn

    chunker_fn = make_chunker(processor)

    # Подготовка чанков с кэшированием
    all_chunks = []
    for idx, file_path in enumerate(files, 1):
        print(f"\n[{idx}/{len(files)}] {file_path.name}")
        file_chunks = chunks_cache.get_or_create(file_path, chunker_fn)
        all_chunks.extend(file_chunks)

    # Контекстуализация (опционально)
    if config.use_contextual_retrieval:
        print("\n--- Контекстуализация чанков ---")
        contextualizer = ContextualChunker(config)
        all_chunks = await contextualizer.contextualize_chunks(all_chunks)

    # Статистика
    stats = chunks_cache.get_stats()
    print("\n--- Статистика ---")
    print(f"Документов в кэше: {stats['cached_documents']}")
    print(f"Всего чанков: {stats['total_chunks']}")
    print(f"Примерно токенов: {stats['total_tokens']}")
    print(f"\nКэш сохранён в: {cache_dir}")

    # Закрытие клиентов
    from src.core.clients import ClientManager

    ClientManager.get_instance().close_all()

    print("\n--- Подготовка завершена ---")


if __name__ == "__main__":
    asyncio.run(main())

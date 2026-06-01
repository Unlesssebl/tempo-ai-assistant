import asyncio
import os
import sys

# Добавляем корень проекта в путь
sys.path.append(os.getcwd())

from src.rag.retrieval.search import SearchService
from src.core.config import Config
from src.core.clients import ClientManager

async def debug_rag_search():
    cfg = Config.from_env()
    cm = ClientManager.get_instance(cfg)
    
    # Инициализируем сервис поиска
    search_service = SearchService(cfg)
    
    query = "график обеда бухгалтерии технотрон"
    print(f"\n--- DEBUG SEARCH: '{query}' ---")
    
    # Выполняем поиск
    # Имитируем FilteredRAGTool.search
    results = await search_service.search(query, limit=10)
    
    print(f"Found {len(results.chunks)} chunks.")
    
    # Очищаем скоры как в FilteredRAGTool
    clean_chunks = SearchService.clean_scores(results.chunks)
    
    context_block = "\n\n===\n\n".join(clean_chunks)
    
    print("\n--- RAW CONTEXT BLOCK SENT TO LLM ---")
    if not context_block.strip():
        print("EMPTY CONTEXT!")
    else:
        print(context_block)
    print("\n--- END OF CONTEXT ---")

if __name__ == "__main__":
    asyncio.run(debug_rag_search())

import asyncio
import sys
from src.core.config import Config
from src.rag.retrieval.search import HybridSearchService

async def test_search():
    config = Config.from_env()
    searcher = HybridSearchService(config=config)
    await searcher.initialize()
    results = await searcher.search("Где находится бухгалтерия технотрона?", top_k=5)
    
    sys.stdout.reconfigure(encoding='utf-8')
    print("--- РЕЗУЛЬТАТЫ ПОИСКА ---")
    for r in results:
        print(f"File: {r['metadata']['source']} | Score: {r['score']}")
        
if __name__ == "__main__":
    asyncio.run(test_search())

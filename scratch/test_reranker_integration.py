import asyncio
import sys
import logging
from src.core.config import Config
from src.rag.retrieval.search import SearchService

logging.basicConfig(level=logging.INFO)

async def test_search():
    config = Config.from_env()
    # Force use of reranker for testing
    config.use_llm_rerank = True
    config.use_crag = False # we commented it out anyway
    
    searcher = SearchService(config=config)
    await searcher.initialize()
    
    query = "Как вызвать айтишника?"
    print(f"Running search for query: '{query}'")
    result = await searcher.search(query, limit=5)
    
    print("\n--- РЕЗУЛЬТАТЫ ПОИСКА ---")
    print(f"Retrieval status: {result.retrieval_status}")
    print(f"Number of chunks: {len(result.chunks)}")
    print(f"Number of documents: {len(result.documents)}")
    for i, doc in enumerate(result.documents):
        print(f"[{i}] Title: {doc.get('title', 'N/A')} | Source: {doc.get('source', 'N/A')}")
        print(f"    Text: {doc.get('text', '')[:100]}...")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(test_search())

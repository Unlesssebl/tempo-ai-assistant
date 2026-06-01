
import asyncio
import logging
import sys
from src.core.config import Config
from src.rag.retrieval.hybrid_search import HybridSearchService

# Форсируем UTF-8 для вывода в Windows
sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)

async def debug_hybrid():
    config = Config.from_env()
    hybrid = HybridSearchService(config)
    await hybrid.initialize()
    
    query = "график обеда бухгалтерии технотрон"
    print(f"\n--- HYBRID SEARCH FOR: '{query}' ---")
    
    results = await hybrid.search(query, limit=10, company_id="ПТФК Технотрон")
    
    if not results:
        print("NO RESULTS FOUND")
        return
        
    for i, res in enumerate(results):
        print(f"[{i+1}] Score: {res['score']:.4f} | Source: {res['source']}")
        text_snippet = res['text'].replace('\n', ' ')[:150]
        print(f"    Text: {text_snippet}...")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(debug_hybrid())


import asyncio
import logging
from src.core.config import Config
from src.rag.retrieval.hybrid_search import HybridSearchService

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
        print(f"[{i+1}] Score: {res['score']:.4f}")
        print(f"    Source: {res['source']}")
        print(f"    Text: {res['text'][:150]}...")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(debug_hybrid())

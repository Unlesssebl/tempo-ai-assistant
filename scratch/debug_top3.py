
import asyncio
import sys
from src.core.config import Config
from src.rag.retrieval.hybrid_search import HybridSearchService

sys.stdout.reconfigure(encoding='utf-8')

async def debug_top3():
    config = Config.from_env()
    hybrid = HybridSearchService(config)
    await hybrid.initialize()
    
    query = "график обеда бухгалтерии технотрон"
    results = await hybrid.search(query, limit=3, company_id="ПТФК Технотрон")
    
    for i, res in enumerate(results):
        print(f"RANK {i+1} | SCORE {res['score']:.4f} | SOURCE {res['source']}")
        print(f"TEXT: {res['text'][:200]}...")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(debug_top3())

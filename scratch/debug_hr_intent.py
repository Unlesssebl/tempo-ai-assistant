
import asyncio
import sys
import logging
from src.core.config import Config
from src.rag.retrieval.hybrid_search import HybridSearchService
from qdrant_client import models

sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

async def debug_hr_intent():
    config = Config.from_env()
    hybrid = HybridSearchService(config)
    await hybrid.initialize()
    
    query = "график обеда бухгалтерии технотрон"
    
    # Имитируем фильтр FilteredRAGTool для hr_policy
    should_conditions = [
        models.FieldCondition(key="company", match=models.MatchText(text="ПТФК Технотрон")),
        models.FieldCondition(key="department", match=models.MatchValue(value="HR"))
    ]
    qdrant_filter = models.Filter(should=should_conditions)
    
    results = await hybrid.search(query, limit=10, company_id="ПТФК Технотрон", qdrant_filter=qdrant_filter)
    
    for i, res in enumerate(results):
        print(f"RANK {i+1} | SCORE {res['score']:.4f} | DEPT {res['metadata'].get('department')} | SOURCE {res['source']}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(debug_hr_intent())

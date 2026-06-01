
import asyncio
import logging
from src.core.config import Config
from src.tools.rag_search import FilteredRAGTool
from src.models.state import QueryIntent

logging.basicConfig(level=logging.INFO)

async def check_rag():
    tool = FilteredRAGTool()
    await tool.initialize()
    
    query = "график обеда бухгалтерии технотрон"
    intent = QueryIntent(
        intent="hr_policy",
        target_company="ПТФК Технотрон",
        is_topic_shift=False
    )
    
    print("\n" + "="*50)
    print(f"SEARCHING FOR: {query}")
    print(f"WITH INTENT: company='{intent.target_company}', intent='{intent.intent}'")
    print("="*50)
    
    results = await tool.search(query, intent)
    print("\nRESULTS WITH FILTERS:")
    print(results)
    
    print("\n" + "="*50)
    print("SEARCHING WITHOUT FILTERS (EMPTY INTENT)")
    print("="*50)
    empty_intent = QueryIntent(intent="general_info")
    results_no_filter = await tool.search(query, empty_intent)
    print("\nRESULTS WITHOUT FILTERS:")
    print(results_no_filter)

if __name__ == "__main__":
    asyncio.run(check_rag())
